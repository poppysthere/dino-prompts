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
UNNATURAL_CAT = re.compile(r"good look|we go to cat|cat\s*就是小猫|^\s*什么意思[？?]|我先说[^。！？]*现在[^。！？]*你说|嗯[，,]?现在[^。！？]*Now you say", re.I)
CHINESE_LABELS = {"chinese", "中文", "简体中文", "繁體中文", "繁体中文", "zh-cn", "zh-tw"}


def is_chinese_language(value):
    return str(value or "").strip().lower() in CHINESE_LABELS


def proactive_script(tr):
    language = str(tr.get("support_language", "")).strip().lower()
    if language in {"", "none", "unknown", "unsupported"}:
        return None
    if is_chinese_language(language):
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
        if spoken.count("!") > 1:
            issues.append(f"reply {i}: too many exclamation marks ({spoken.count('!')})")
        for sentence in re.split(r"[.!?。！？]+", spoken):
            words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", sentence)
            if len(words) > 6:
                issues.append(f"reply {i}: English sentence too long ({len(words)} words)")
        if i > 1 and "Mouse sees a cat" in reply:
            issues.append(f"reply {i}: restarted the page")

    configured = proactive_script(tr)
    if configured is not None and replies:
        if not configured.search(replies[0]):
            issues.append("first reply missed the configured-language orientation")
        elif is_chinese_language(tr.get("support_language")):
            if not re.search(r"(?:快看|咦|再看看).*谁", replies[0]) or "新单词" not in replies[0]:
                issues.append("Chinese opening did not explain the new-word activity naturally")
            if not re.search(r"先听我说.*cat.*(?:轮到你|换你|试试|说说)", replies[0], re.I):
                issues.append("Chinese opening did not use a natural model-and-invitation flow")
            if re.search(r"我先说.*现在.*你说", replies[0]):
                issues.append("Chinese opening used literal robotic turn labels")
        elif str(tr.get("support_language", "")).strip().lower() == "arabic":
            if not re.search(r"كلمة جديدة.*cat.*استمع.*cat.*جرب أنت.*cat", replies[0], re.I) or re.search(r"أنا أقول|الآن دورك|\bsay\b|كالقط|يعني|معناه", replies[0], re.I):
                issues.append("Arabic opening did not use a natural child-teacher flow")
    elif replies:
        if CJK.search(replies[0]) or ARABIC.search(replies[0]):
            issues.append("first reply invented a local language with no configured support language")
        spoken_first = re.sub(r"\[[A-Z_]+\]", "", replies[0])
        if not re.search(r"\b(?:Look|look)\b", spoken_first) or not re.search(r"\b(?:Your turn|You try|Now you)\b", spoken_first, re.I):
            issues.append("first reply missed the easy-English discovery and invitation cues")

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
        elif tr.get("bridge_job") not in {"meow_meaning", "current_personal_direction"} and "cat" not in replies[bridge_replies[0] - 1].lower():
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
                if not re.search(r"学猫叫|叫一声|试试", bridge) or "meow meow" not in bridge.lower():
                    issues.append("meow bridge did not give a natural child action and English model")
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
                if not re.search(r"现在你说|先听我说吧|看这里", first):
                    issues.append("first help response gave no clear local instruction")
                if not re.search(r"没关系[^。！？]*听老师说", last):
                    issues.append("rescue exit did not use natural reassurance plus instruction")
                if re.search(r"你不用说|不需要说|可以不说", last):
                    issues.append("rescue exit dismissed the child from speaking")
                if not re.search(r"听老师说", last):
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
                if "New word" not in silence_nudge or not re.search(r"Listen.*cat.*Your turn.*cat", silence_nudge, re.I):
                    issues.append("first silence did not get a natural cat nudge")
                if "Cat 就是猫" not in first_help or not re.search(r"现在你说\s*cat", first_help, re.I):
                    issues.append("first Chinese confusion did not get meaning plus a clear child action")
                if "还在学 cat" not in direction_help or not re.search(r"你说\s*cat", direction_help, re.I) or "We go to cat" in direction_help:
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
            if job == "first_silence_clarity" and tr.get("bridge_script") == "arabic":
                if not re.search(r"نتعلم.*كلمة جديدة", bridge):
                    issues.append("Arabic first silence did not explain the learning activity")
                if not re.search(r"إذا لم تفهم.*(?:أخبرني|قل لي)", bridge):
                    issues.append("Arabic first silence did not make help-seeking safe")
                if not re.search(r"استمع.*cat.*جرب أنت.*cat", bridge, re.I) or re.search(r"أنا أقول|الآن دورك", bridge):
                    issues.append("Arabic first silence did not use a natural model-and-try invitation")
            if job == "current_personal_direction" and tr.get("bridge_script") == "cjk" and not tr.get("skip_personality_check"):
                direction = replies[bridge_replies[0] - 1]
                if not re.search(r"喜不喜欢猫", direction) or not re.search(r"yes.*no", direction, re.I):
                    issues.append("late what-to-do question did not explain the current cat preference task")
                if re.search(r"我们来学\s*cat|现在你说\s*cat|听，?\s*cat", direction, re.I):
                    issues.append("late what-to-do question regressed to the mastered cat drill")
            if job == "first_silence_clarity" and tr.get("bridge_script") == "cjk":
                silence_help = replies[bridge_replies[0] - 1]
                if not re.search(r"(?:正在|在)学新单词\s*cat", silence_help, re.I):
                    issues.append("first silence did not explain what the child is doing")
                if not re.search(r"(?:没听清|没听懂|不明白|不太明白).*告诉我|告诉我.*(?:不明白|没听懂|没听清)", silence_help):
                    issues.append("first silence did not teach safe help-seeking")
                if not re.search(r"先听我说.*cat.*(?:试试|说说).*cat", silence_help, re.I):
                    issues.append("first silence did not use a natural model-and-try invitation")
                if re.search(r"我先说.*现在.*你说", silence_help):
                    issues.append("first silence used literal robotic turn labels")
                if re.search(r"Look.*Cat.*Say\s*cat", silence_help, re.I):
                    issues.append("first silence fell back to a mechanical English command")

    if len(replies) > tr["max_replies"]:
        issues.append(f"too many replies: {len(replies)} > {tr['max_replies']}")
    if tr.get("case") == "previous-cow-is-not-cat" and len(replies) > 1:
        if "Cow says moo" not in replies[1] or re.search(r"YES! Cat|You got it", replies[1], re.I):
            issues.append("previous word cow was falsely accepted as cat")
    if tr.get("case") == "what-to-do-after-cat-and-meow" and len(replies) > 2:
        if "That was cute" not in replies[2]:
            issues.append("real meow did not receive a specific human reaction")
    if not replies or "[TEMPLATE_FINISH]" not in replies[-1]:
        issues.append("page did not finish")
    if not tr.get("rescue_exit") and not tr.get("skip_personality_check"):
        if any("Who ate the cake" in r for r in replies):
            issues.append("cat page fell back to the repetitive cake question")
        if not any("I have two cats" in r and "Do you like cats" in r for r in replies):
            issues.append("cat page missed Max's stable two-cats story")
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
