#!/usr/bin/env python3
"""Mechanical checks for the experimental cow language-rescue page."""
import json
import re
import sys


CONTROL = re.compile(r"\[(?:STUDENT_TALK|TEMPLATE_FINISH|NEXT_STEP|WORD_EVALUATION)\]")
CJK = re.compile(r"[\u3400-\u9fff]")
ARABIC = re.compile(r"[\u0600-\u06ff]")
BANNED_TEACHING = re.compile(r"\b(?:say it with me|repeat after me|one more time)\b", re.I)


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
        if CJK.search(reply) or ARABIC.search(reply):
            bridge_replies.append(i)
        if BANNED_TEACHING.search(reply):
            issues.append(f"reply {i}: banned teaching phrase")
        spoken = re.sub(r"\[[A-Z_]+\]", "", reply)
        for sentence in re.split(r"[.!?]+", spoken):
            words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", sentence)
            if len(words) > 6:
                issues.append(f"reply {i}: English sentence too long ({len(words)} words)")
        if i > 1 and "Mouse sees a cow" in reply:
            issues.append(f"reply {i}: restarted the page")

    if tr["bridge"] == "forbidden" and bridge_replies:
        issues.append(f"unexpected support-language reply(s): {bridge_replies}")
    if tr["bridge"] == "required":
        if len(bridge_replies) != 1:
            issues.append(f"expected exactly one support-language bridge, got {bridge_replies}")
        elif not expected.search(replies[bridge_replies[0] - 1]):
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
            if job == "instruction" and tr.get("bridge_script") == "arabic":
                if not re.search(r"(?:قل|اسمع|انظر|اختر)", bridge):
                    issues.append("Arabic bridge did not give a concrete instruction")

    if len(replies) > tr["max_replies"]:
        issues.append(f"too many replies: {len(replies)} > {tr['max_replies']}")
    if not replies or "[TEMPLATE_FINISH]" not in replies[-1]:
        issues.append("page did not finish")
    if sum("Who ate the cake" in r for r in replies) != 1:
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
