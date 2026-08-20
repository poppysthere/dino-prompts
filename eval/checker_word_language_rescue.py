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
UNNATURAL_TEACHER = re.compile(r"(?:Good look|We go to (?:cow|cat|horse) now|I (?:will not|won't) say more)", re.I)


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
        if UNNATURAL_TEACHER.search(reply):
            issues.append(f"reply {i}: unnatural teacher wording")
        spoken = re.sub(r"\[[A-Z_]+\]", "", reply)
        if spoken.count("!") > 1:
            issues.append(f"reply {i}: too many exclamation marks ({spoken.count('!')})")
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
        elif str(tr.get("support_language", "")).strip().lower() == "chinese" and not re.search(r"(?:快看|咦|再看看).*谁.*(?:试试|说说看|轮到你|现在你|来[^。！？]*(?:说|读))", replies[0]):
            issues.append("Chinese opening did not use a natural discovery-model-invitation flow")
        elif str(tr.get("support_language", "")).strip().lower() == "arabic":
            if not re.search(r"أنا أقول\s*cow.*الآن دورك.*قل\s*cow", replies[0], re.I) or re.search(r"\bsay\b", replies[0], re.I):
                issues.append("Arabic opening did not use a natural Arabic turn-taking flow")
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
        elif tr.get("bridge_job") not in {"moo_meaning", "current_personal_direction"} and "cow" not in replies[bridge_replies[0] - 1].lower():
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
                if not re.search(r"(?:现在)?你.*(?:学牛叫|叫一声|试试|说)", bridge):
                    issues.append("moo bridge did not give a clear child action after the model")
                if not re.search(r"moo moo", bridge, re.I):
                    issues.append("moo bridge did not model the current sound")
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
                if not re.search(r"现在你说|先听我说吧|看这里", first):
                    issues.append("first help response gave no clear local instruction")
                if not re.search(r"没关系[^。！？]*听老师说", last):
                    issues.append("rescue exit did not use natural reassurance plus instruction")
                if re.search(r"你不用说|不需要说|可以不说", last):
                    issues.append("rescue exit dismissed the child from speaking")
                if not re.search(r"听老师说", last):
                    issues.append("rescue exit gave no clear local instruction")
                if not re.search(r"that's a cow", last, re.I):
                    issues.append("rescue exit did not return gently to English")
                if re.search(r"(?:say|you say)[, ]+cow", last, re.I):
                    issues.append("rescue exit repeated the cow demand")
                if "[TEMPLATE_FINISH]" not in last:
                    issues.append("rescue exit did not gently finish the activity")
            if job == "exact_log_help_flow" and tr.get("bridge_script") == "cjk":
                retry = replies[1]
                help_reply = replies[2]
                final = replies[3]
                if "cow" not in retry.lower() or not re.search(r"you try|say[, ]+cow", retry, re.I):
                    issues.append("unclear first response did not get one tiny cow retry")
                if re.search(r"moo|Who ate the cake", retry, re.I):
                    issues.append("unclear first response incorrectly advanced past cow")
                if not re.search(r"我在说\s*cow|cow[^。！？]*就是牛", help_reply, re.I):
                    issues.append("what-did-you-say request was not answered in Chinese")
                if re.search(r"\bShe\b|Ha ha|No, cow|moo|Who ate the cake", help_reply, re.I):
                    issues.append("Chinese help reply echoed ASR, laughed, corrected, or advanced")
                if "你已经说出来啦" not in final or "Cow" not in final:
                    issues.append("mixed cow success and inability was not acknowledged")
                if re.search(r"I (?:will not|won't) say more|moo|Who ate the cake", final, re.I):
                    issues.append("final reply refused help or incorrectly advanced")
                if "[TEMPLATE_FINISH]" not in final:
                    issues.append("mixed success and inability did not finish gently")
            if job == "human_direction_current_item" and tr.get("bridge_script") == "cjk":
                cow_help = replies[1]
                moo_help = replies[3]
                cutoff = replies[4]
                if "Cow 就是牛" not in cow_help or not re.search(r"现在你说\s*cow", cow_help, re.I):
                    issues.append("cow meaning help was not a natural explanation plus clear action")
                if not re.search(r"Moo moo 是牛的叫声", moo_help, re.I):
                    issues.append("current moo question was not answered directly")
                if not re.search(r"(?:学牛叫|叫一声|试试)", moo_help) or not re.search(r"moo moo", moo_help, re.I):
                    issues.append("moo help lacked one clear child action and model")
                if re.search(r"Cow 就是牛|Cow\. That's a cow", moo_help, re.I):
                    issues.append("moo question regressed to the mastered cow meaning")
                if not re.search(r"慢慢说.*我在听", cutoff):
                    issues.append("cut-off speech was not met with a natural invitation to finish")
                if re.search(r"move on|继续|TEMPLATE_FINISH", cutoff, re.I):
                    issues.append("teacher redirected or closed while the child was still speaking")
            if job == "exact_task_direction_flow" and tr.get("bridge_script") == "cjk":
                task_help = replies[1]
                then_help = replies[2]
                moo_help = replies[4]
                repeated_moo_help = replies[5]
                if "我们来学 cow" not in task_help or not re.search(r"现在你说\s*cow", task_help, re.I):
                    issues.append("what-to-do question did not explain the task and child's action")
                if "没关系" in task_help or "[STUDENT_TALK]" not in task_help:
                    issues.append("neutral task question got canned reassurance or no wait")
                if not re.search(r"现在轮到你", then_help) or not re.search(r"(?:你)?说\s*cow", then_help, re.I):
                    issues.append("then-what question did not give the immediate child action")
                if re.search(r"先听|听我说", then_help):
                    issues.append("teacher told the child to listen again after they already listened")
                if not re.search(r"Moo moo 是牛的叫声", moo_help, re.I):
                    issues.append("first moo meaning request did not explain the current sound")
                if not re.search(r"学牛叫|叫一声", moo_help):
                    issues.append("first moo help did not tell the child how to participate")
                if not re.search(r"牛会这样叫", repeated_moo_help) or not re.search(r"叫一声", repeated_moo_help):
                    issues.append("repeated moo confusion did not get a clearer natural explanation and action")
                if re.search(r"Cow 就是牛|Cow\. That's a cow|move on|TEMPLATE_FINISH", moo_help + repeated_moo_help, re.I):
                    issues.append("moo help regressed to cow or closed before resolving the question")
            if job == "current_personal_direction" and tr.get("bridge_script") == "cjk":
                direction = replies[bridge_replies[0] - 1]
                if not re.search(r"喜不喜欢牛", direction) or not re.search(r"yes.*no", direction, re.I):
                    issues.append("late what-to-do question did not explain the current cow preference task")
                if re.search(r"我们来学\s*cow|现在你说\s*cow|听，?\s*cow", direction, re.I):
                    issues.append("late what-to-do question regressed to the mastered cow drill")
            if job == "first_silence_clarity" and tr.get("bridge_script") == "cjk":
                silence_help = replies[bridge_replies[0] - 1]
                if not re.search(r"在学新单词\s*cow", silence_help, re.I):
                    issues.append("first silence did not explain what the child is doing")
                if not re.search(r"没听懂.*告诉我", silence_help):
                    issues.append("first silence did not teach safe help-seeking")
                if not re.search(r"我先说.*cow.*轮到你.*(?:你)?说\s*cow", silence_help, re.I):
                    issues.append("first silence did not model child-friendly turn-taking and one action")
                if re.search(r"Look.*Cow.*Say\s*cow", silence_help, re.I):
                    issues.append("first silence fell back to a mechanical English command")
            if job == "instruction" and tr.get("bridge_script") == "arabic":
                if not re.search(r"(?:قل|اسمع|استمع|استماع|انظر|اختر)", bridge):
                    issues.append("Arabic bridge did not give a concrete instruction")
            if job == "first_silence_clarity" and tr.get("bridge_script") == "arabic":
                if not re.search(r"نتعلم.*كلمة جديدة", bridge):
                    issues.append("Arabic first silence did not explain the learning activity")
                if not re.search(r"إذا لم تفهم.*(?:أخبرني|قل لي)", bridge):
                    issues.append("Arabic first silence did not make help-seeking safe")
                if not re.search(r"أنا أقول.*cow.*دورك.*قل\s*cow", bridge, re.I):
                    issues.append("Arabic first silence did not explain turn-taking and the cow action")

    if len(replies) > tr["max_replies"]:
        issues.append(f"too many replies: {len(replies)} > {tr['max_replies']}")
    if not replies or "[TEMPLATE_FINISH]" not in replies[-1]:
        issues.append("page did not finish")
    if not tr.get("rescue_exit"):
        if any("Who ate the cake" in r for r in replies):
            issues.append("cow page fell back to the repetitive cake question")
        if not any("I like cows" in r and "Do you like cows" in r for r in replies):
            issues.append("cow page missed Max's natural preference reaction")
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
