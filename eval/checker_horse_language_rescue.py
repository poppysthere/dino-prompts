#!/usr/bin/env python3
"""Mechanical checks for the experimental horse language-rescue page."""
import copy
import json
import re
import sys

import checker_cat_language_rescue as shared


def cat_equivalent(tr):
    """Reuse the mature rescue checker after mapping horse concepts to cat concepts."""
    mapped = copy.deepcopy(tr)
    mapped["skip_personality_check"] = True
    replacements = (
        ("[TEACHER_RIDE_HORSE]", "[TEACHER_CAT_PAWS]"),
        ("HORSES", "CATS"),
        ("Horses", "Cats"),
        ("horses", "cats"),
        ("HORSE", "CAT"),
        ("Horse", "Cat"),
        ("horse", "cat"),
        ("NEIGH", "MEOW"),
        ("Neigh", "Meow"),
        ("neigh", "meow"),
        ("马的叫声", "猫的叫声"),
        ("马的声音", "猫的声音"),
        ("马", "猫"),
    )
    for message in mapped["messages"]:
        text = message["text"]
        for before, after in replacements:
            text = text.replace(before, after)
        message["text"] = text
    return mapped


def teacher_replies(tr):
    return [m["text"] for m in tr["messages"] if m["role"] == "assistant"]


def check(tr):
    issues = shared.check(cat_equivalent(tr))
    replies = teacher_replies(tr)
    spoken = [re.sub(r"\[[A-Z_]+\]", "", reply) for reply in replies]

    spoiler = re.compile(
        r"\bthe horse ate\b|\b(?:yes|right|correct|you got it)\b[^.!?]*\bhorse\b[^.!?]*\b(?:ate|did)\b",
        re.I,
    )
    for i, line in enumerate(spoken, 1):
        if spoiler.search(line):
            issues.append(f"reply {i}: confirmed the horse as the cake culprit")

    if replies and "[TEMPLATE_FINISH]" in replies[-1] and not tr.get("rescue_exit"):
        if "Let's go find out." not in replies[-1]:
            issues.append("normal horse close did not say Let's go find out")
        if "[TEACHER_RIDE_HORSE]" not in replies[-1]:
            issues.append("horse close missed [TEACHER_RIDE_HORSE]")

    case = tr.get("case")
    if case in {"house-asr-is-horse", "of-course-asr-is-horse"} and len(spoken) > 1:
        if not re.search(r"\b(?:Yes, horse|You got it)\b", spoken[1], re.I):
            issues.append(f"{case}: ASR horse try was not accepted")
        if re.search(r"say[, ]+horse", spoken[1], re.I):
            issues.append(f"{case}: ASR horse try incorrectly triggered a retry")

    if case == "previous-cat-is-not-horse" and len(spoken) > 1:
        if "Cat says meow" not in spoken[1] or "horse" not in spoken[1].lower():
            issues.append("previous cat word was not handled warmly and redirected to horse")
        if re.search(r"Yes, horse|You got it", spoken[1], re.I):
            issues.append("previous cat word was falsely accepted as horse")

    if case == "nainai-asr-is-neigh" and len(spoken) > 2:
        if "Funny sound" in spoken[2] or "I want to ride one" not in spoken[2]:
            issues.append("奶奶 ASR was not accepted as a real neigh")

    if case == "correct-culprit-is-not-confirmed" and replies:
        if spoiler.search(spoken[-1]):
            issues.append("correct horse guess was not kept as a mystery")

    if not tr.get("rescue_exit"):
        if any("Who ate the cake" in line for line in replies):
            issues.append("horse page fell back to the repetitive cake question")
        if not any("I want to ride one" in line for line in replies):
            issues.append("horse page missed Max's natural riding wish")

    if tr.get("bridge_job") == "current_personal_direction" and tr.get("bridge_script") == "cjk":
        bridge_replies = [i for i, line in enumerate(replies, 1) if re.search(r"[\u3400-\u9fff]", line) and i != 1]
        if bridge_replies:
            direction = replies[bridge_replies[0] - 1]
            if not re.search(r"想不想骑", direction) or not re.search(r"yes.*no", direction, re.I):
                issues.append("late what-to-do question did not explain the current horse riding task")
            if re.search(r"我们来学\s*horse|现在你说\s*horse|听，?\s*horse", direction, re.I):
                issues.append("late what-to-do question regressed to the mastered horse drill")

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
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
