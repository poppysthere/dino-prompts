#!/usr/bin/env python3
"""Mechanical checks for the experimental cow language-rescue page."""
import json
import re
import sys


CONTROL = re.compile(r"\[(?:STUDENT_TALK|TEMPLATE_FINISH|NEXT_STEP|WORD_EVALUATION)\]")
CJK = re.compile(r"[\u3400-\u9fff]")
ARABIC = re.compile(r"[\u0600-\u06ff]")
BANNED_TEACHING = re.compile(r"\b(?:say it with me|repeat after me|one more time)\b", re.I)
ROBOTIC_CHINESE = re.compile(r"(?:^|[。！？])\s*(?:牛|听|说|看|看图片|先听|跟着老师|你不用说|我们先继续)\s*[。！？]")


def proactive_script(tr):
    language = str(tr.get("support_language", "")).strip().lower()
    if language in {"", "none", "unknown", "unsupported"}:
        return None
    if language == "chinese":
        return CJK
    if language == "arabic":
        return ARABIC
    return None


def is_proactive_scaffold(reply, reply_number, tr):
    return proactive_script(tr) is not None and reply_number == 1


def check(tr):
    replies = [m["text"] for m in tr["messages"] if m["role"] == "assistant"]
    issues = []
    bridge_replies = []
    expected = CJK if tr.get("bridge_script") == "cjk" else ARABIC

    for i, reply in enumerate(replies, 1):
        tags = CONTROL.findall(reply)
        if len(tags) != 1 or not reply.rstrip().endswith(tags[-1] if tags else "__missing__"):
            issues.append(f"reply {i}: needs exactly one final control tag")
        if "[WORD_EVALUATION]" in reply:
            issues.append(f"reply {i}: [WORD_EVALUATION] is forbidden")
        if (CJK.search(reply) or ARABIC.search(reply)) and not is_proactive_scaffold(reply, i, tr):
            bridge_replies.append(i)
        if BANNED_TEACHING.search(reply):
            issues.append(f"reply {i}: banned teaching phrase")
        if ROBOTIC_CHINESE.search(reply):
            issues.append(f"reply {i}: robotic or unnatural Chinese teacher language")
        spoken = re.sub(r"\[[A-Z_]+\]", "", reply)
        for sentence in re.split(r"[.!?]+", spoken):
            words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", sentence)
            if len(words) > 6:
                issues.append(f"reply {i}: English sentence too long ({len(words)} words)")
        if i > 1 and "Mouse sees a cow" in reply:
            issues.append(f"reply {i}: restarted the page")

    configured = proactive_script(tr)
    if configured is not None and replies:
        if not configured.search(replies[0]):
            issues.append("first reply missed the configured-language orientation")
        elif tr.get("support_language") == "Chinese" and not re.search(r"看.*听.*轮到你", replies[0]):
            issues.append("Chinese orientation was not one natural look-listen-your-turn sentence")
    elif replies:
        if CJK.search(replies[0]) or ARABIC.search(replies[0]):
            issues.append("first reply invented a local language with no configured support language")
        spoken_first = re.sub(r"\[[A-Z_]+\]", "", replies[0])
        if not all(piece in spoken_first for piece in ("Look here", "Listen first", "your turn")):
            issues.append("first reply missed the easy-English orientation")

    if tr["bridge"] == "forbidden" and bridge_replies:
        issues.append(f"unexpected support-language reply(s): {bridge_replies}")
    if tr["bridge"] == "optional" and bridge_replies:
        if not all(expected.search(replies[i - 1]) for i in bridge_replies):
            issues.append("optional bridge used the wrong writing system")
    if tr["bridge"] == "required":
        expected_replies = tr.get("bridge_replies")
        if expected_replies is not None and bridge_replies != expected_replies:
            issues.append(f"support-language replies were {bridge_replies}, expected {expected_replies}")
        elif expected_replies is None and len(bridge_replies) != 1:
            issues.append(f"expected exactly one support-language bridge, got {bridge_replies}")
        elif not bridge_replies:
            issues.append("expected support-language bridge, got none")
        elif not all(expected.search(replies[i - 1]) for i in bridge_replies):
            issues.append("bridge used the wrong writing system")
        elif "cow" not in replies[bridge_replies[0] - 1].lower():
            issues.append("bridge did not return immediately to English target 'cow'")
        else:
            bridge = replies[bridge_replies[0] - 1]
            expected_reply = tr.get("bridge_reply")
            if expected_reply and bridge_replies[0] != expected_reply:
                issues.append(
                    f"support-language bridge came on reply {bridge_replies[0]}, "
                    f"expected reply {expected_reply}"
                )
            job = tr.get("bridge_job")
            if job == "instruction" and tr.get("bridge_script") == "cjk":
                if not re.search(r"[听说看选]", bridge):
                    issues.append("Chinese bridge did not give a concrete instruction")
            if job == "meaning" and tr.get("bridge_script") == "cjk":
                if "牛" not in bridge:
                    issues.append("Chinese meaning bridge did not give the target meaning")
            if job == "moo_meaning" and tr.get("bridge_script") == "cjk":
                if not re.search(r"牛.*(?:叫声|声音)", bridge):
                    issues.append("Chinese moo bridge did not explain that moo is a cow sound")
                if not re.search(r"(?:you say|say)[, ]+moo moo", bridge, re.I):
                    issues.append("moo bridge did not return to a tiny English moo invitation")
                if re.search(r"say[, ]+cow", bridge, re.I):
                    issues.append("moo question incorrectly returned to teaching cow")
            if job == "contextual_rescue" and tr.get("bridge_script") == "cjk":
                first = replies[bridge_replies[0] - 1]
                second = replies[bridge_replies[1] - 1]
                last = replies[bridge_replies[-1] - 1]
                if "Cow 就是牛" not in first:
                    issues.append("first meaning bridge is not natural Chinese")
                if re.search(r"say[, ]+cow", second, re.I):
                    issues.append("continued drilling cow after meaning rescue failed")
                if "蛋糕" not in last or "牛的叫声" in last:
                    issues.append("final confusion did not explain the current cake question")
            if job == "rescue_exit" and tr.get("bridge_script") == "cjk":
                first = replies[bridge_replies[0] - 1]
                last = replies[bridge_replies[-1] - 1]
                if "牛" not in first:
                    issues.append("first help response did not explain cow")
                if not re.search(r"先听我说吧|看这里", first):
                    issues.append("first help response gave no clear local instruction")
                if re.search(r"(?:say|you say)[, ]+cow", first, re.I):
                    issues.append("first help response immediately demanded cow")
                if not re.search(r"没关系[^。！？]*先听我说吧", last):
                    issues.append("rescue exit did not use natural reassurance plus instruction")
                if re.search(r"你不用说|不需要说|可以不说", last):
                    issues.append("rescue exit dismissed the child from speaking")
                if not re.search(r"先听我说吧|看这里", last):
                    issues.append("rescue exit gave no clear local instruction")
                if not re.search(r"that's a cow", last, re.I):
                    issues.append("rescue exit did not return gently to English")
                if re.search(r"(?:say|you say)[, ]+cow", last, re.I):
                    issues.append("rescue exit repeated the cow demand")
                if "[TEMPLATE_FINISH]" not in last:
                    issues.append("rescue exit did not gently finish the activity")
            if job == "instruction" and tr.get("bridge_script") == "arabic":
                if not re.search(r"(?:قل|اسمع|استمع|استماع|انظر|اختر)", bridge):
                    issues.append("Arabic bridge did not give a concrete instruction")

    if len(replies) > tr["max_replies"]:
        issues.append(f"too many replies: {len(replies)} > {tr['max_replies']}")
    if not replies or "[TEMPLATE_FINISH]" not in replies[-1]:
        issues.append("page did not finish")
    if not tr.get("rescue_exit") and sum("Who ate the cake" in r for r in replies) != 1:
        issues.append("cake wonder must appear exactly once")
    return issues


def main():
    bad = 0
    for path in sys.argv[1:]:
        tr = json.loads(open(path, encoding="utf-8").read())
        issues = check(tr)
        if issues:
            bad += 1
            print(f"FAIL {path}")
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"PASS {path}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
