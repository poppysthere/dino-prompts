#!/usr/bin/env python3
"""Mechanical checks for the experimental cat language-rescue page."""
import json
import re
import sys


CONTROL = re.compile(r"\[(?:STUDENT_TALK|TEMPLATE_FINISH|NEXT_STEP|WORD_EVALUATION)\]")
CJK = re.compile(r"[\u3400-\u9fff]")
ARABIC = re.compile(r"[\u0600-\u06ff]")
BANNED_TEACHING = re.compile(r"\b(?:say it with me|repeat after me|one more time)\b", re.I)
ROBOTIC_CHINESE = re.compile(r"(?:^|[。！？])\s*(?:猫|听|说|看|看图片|先听|跟着老师|你不用说|我们先继续)\s*[。！？]")
UNNATURAL_CAT = re.compile(r"good look|we go to cat|cat\s*就是小猫|^\s*什么意思[？?]", re.I)


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
    """The first-turn orientation is not a rescue bridge."""
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
        if UNNATURAL_CAT.search(reply):
            issues.append(f"reply {i}: unnatural or context-insensitive cat language")
        spoken_lower = re.sub(r"\[[A-Z_]+\]", "", reply).lower()
        if re.search(r"\b(?:move on|continue|next)\b", spoken_lower) and "[TEMPLATE_FINISH]" not in reply:
            issues.append(f"reply {i}: announced a transition without finishing the page")
        spoken = re.sub(r"\[[A-Z_]+\]", "", reply)
        for sentence in re.split(r"[.!?]+", spoken):
            words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", sentence)
            if len(words) > 6:
                issues.append(f"reply {i}: English sentence too long ({len(words)} words)")
        if i > 1 and "Mouse sees a cat" in reply:
            issues.append(f"reply {i}: restarted the page")

    configured = proactive_script(tr)
    if configured is not None and replies:
        if not configured.search(replies[0]):
            issues.append("first reply missed the configured-language orientation")
        elif str(tr.get("support_language", "")).strip().lower() == "chinese" and not re.search(r"看.*听.*轮到你", replies[0]):
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
        elif "cat" not in replies[bridge_replies[0] - 1].lower():
            issues.append("bridge did not return immediately to English target 'cat'")
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
                if "猫" not in bridge:
                    issues.append("Chinese meaning bridge did not give the target meaning")
            if job == "meow_meaning" and tr.get("bridge_script") == "cjk":
                if not re.search(r"猫.*(?:叫声|声音)", bridge):
                    issues.append("Chinese meow bridge did not explain that meow is a cat sound")
                if "先听我说吧" not in bridge or "meow meow" not in bridge.lower():
                    issues.append("meow bridge did not give a natural instruction and English model")
                if re.search(r"(?:you say|say)[, ]+meow meow", bridge, re.I):
                    issues.append("meow help response immediately demanded performance")
                if re.search(r"say[, ]+cat", bridge, re.I):
                    issues.append("meow question incorrectly returned to teaching cat")
            if job == "contextual_rescue" and tr.get("bridge_script") == "cjk":
                first = replies[bridge_replies[0] - 1]
                second = replies[bridge_replies[1] - 1]
                last = replies[bridge_replies[-1] - 1]
                if "Cat 就是猫" not in first:
                    issues.append("first meaning bridge is not natural Chinese")
                if re.search(r"say[, ]+cat", second, re.I):
                    issues.append("continued drilling cat after meaning rescue failed")
                if "蛋糕" not in last or "猫的叫声" in last:
                    issues.append("final confusion did not explain the current cake question")
            if job == "rescue_exit" and tr.get("bridge_script") == "cjk":
                first = replies[bridge_replies[0] - 1]
                last = replies[bridge_replies[-1] - 1]
                if "猫" not in first:
                    issues.append("first help response did not explain cat")
                if not re.search(r"先听我说吧|看这里", first):
                    issues.append("first help response gave no clear local instruction")
                if re.search(r"(?:say|you say)[, ]+cat", first, re.I):
                    issues.append("first help response immediately demanded cat")
                if not re.search(r"没关系[^。！？]*先听我说吧", last):
                    issues.append("rescue exit did not use natural reassurance plus instruction")
                if re.search(r"你不用说|不需要说|可以不说", last):
                    issues.append("rescue exit dismissed the child from speaking")
                if not re.search(r"先听我说吧|看这里", last):
                    issues.append("rescue exit gave no clear local instruction")
                if not re.search(r"that's a cat", last, re.I):
                    issues.append("rescue exit did not return gently to English")
                if re.search(r"(?:say|you say)[, ]+cat", last, re.I):
                    issues.append("rescue exit repeated the cat demand")
                if "[TEMPLATE_FINISH]" not in last:
                    issues.append("rescue exit did not gently finish the activity")
            if job == "contextual_help_flow" and tr.get("bridge_script") == "cjk":
                silence_nudge = replies[1]
                first_help = replies[2]
                direction_help = replies[3]
                meow_help = replies[5]
                slow_help = replies[6]
                if "Good look" in silence_nudge or "Look here" not in silence_nudge:
                    issues.append("first silence did not get a natural cat nudge")
                if "先听我说吧" not in first_help or "That's a cat" not in first_help:
                    issues.append("first confusion did not get natural instruction plus English model")
                if "还在学 cat" not in direction_help or "We go to cat" in direction_help:
                    issues.append("where-next question was not answered naturally")
                if "猫的叫声" not in meow_help or "Cat 就是" in meow_help:
                    issues.append("meaning question after meow explained the wrong item")
                if "我慢一点" not in slow_help or not re.search(r"Meow\.\s*Meow\.", slow_help, re.I):
                    issues.append("slow-down request did not slow the current meow target")
                if "[TEMPLATE_FINISH]" in slow_help:
                    issues.append("slow-down request incorrectly ended the activity")
            if job == "instruction" and tr.get("bridge_script") == "arabic":
                if not re.search(r"(?:قل|اسمع|استمع|استماع|انظر|اختر)", bridge):
                    issues.append("Arabic bridge did not give a concrete instruction")

    if len(replies) > tr["max_replies"]:
        issues.append(f"too many replies: {len(replies)} > {tr['max_replies']}")
    if tr.get("case") == "previous-cow-is-not-cat" and len(replies) > 1:
        if "Cow says moo" not in replies[1] or re.search(r"YES! Cat|You got it", replies[1], re.I):
            issues.append("previous word cow was falsely accepted as cat")
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
