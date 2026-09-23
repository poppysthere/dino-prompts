#!/usr/bin/env python3
"""Mechanical and child-first checks for the L1 pre-A1 lesson."""

import json
import re
import sys
import unicodedata


CONFIG = {
    "leadin_pre": {
        "first": (
            r"^Hi(?:, [A-Za-z][A-Za-z .'-]*| there)\. I'm .+\. "
            r"Welcome to class\. Say hi to me\."
        ),
        "finish": "[NEXT_STEP]",
    },
    "leadin_post": {
        "first": r"^Chef Boo has food\. Now let's learn three words\.",
        "finish": "[TEMPLATE_FINISH]",
    },
    "word_apple": {
        "first": r"^Look\. Boo has an apple\. Listen first\. Apple\. Now you try\. Apple\.",
        "finish": "[TEMPLATE_FINISH]",
    },
    "word_bread": {
        "first": r"^Look\. Boo has bread\. Listen first\. Bread\. Now you try\. Bread\.",
        "finish": "[TEMPLATE_FINISH]",
    },
    "word_juice": {
        "first": r"^Look\. Boo has juice\. Listen first\. Juice\. Now you try\. Juice\.",
        "finish": "[TEMPLATE_FINISH]",
    },
    "sentence_intro": {
        "first": r"^Apple\. Juice\. Bread\. Boo has food\. Let's watch Boo eat\.",
        "finish": "[NEXT_STEP]",
    },
    "sentence_like_bread": {
        "first": r"^Look\. Boo eats the bread\. Munch munch\. Listen first\. I like bread\.",
        "finish": "[NEXT_STEP]",
    },
    "sentence_dont_apples": {
        "first": r"^Oh, Boo says yuck\. Listen first\. I don't like apples\.",
        "finish": "[TEMPLATE_FINISH]",
    },
    "wrapup": {
        "first": r"^Look at Boo's food\. Apple, juice, and bread\. Was class fun\?",
        "finish": "[NEXT_STEP]",
    },
}

CONTROL = re.compile(r"\[(?:STUDENT_TALK|TEMPLATE_FINISH|NEXT_STEP|WORD_EVALUATION)\]")
QUESTION = re.compile(
    r"\?|\b(?:what(?:'s| is)|who|where|why|how(?:'s| is)|do you|can you|are you)\b",
    re.I,
)
HARD_OUTPUT = [
    r"\bdo you want\b",
    r"\bwhat does\b",
    r"\bwhat sound\b",
    r"\bwho ate\b",
    r"\bare you ready\b",
    r"\bsay it with me\b",
    r"\brepeat after me\b",
    r"\bcan you say\b",
    r"\bwhat fun\b",
]
LESSON_FIRST = re.compile(
    r"^(?:look\b|listen\b|now\b|your turn\b|apple\b|bread\b|juice\b|"
    r"i like bread\b|i don't like apples\b|that's okay\b|okay\b|let's\b)",
    re.I,
)


def strip_tags(text):
    return re.sub(r"\[[A-Z_]+\]", "", text).strip()


def first_sentence(text):
    body = strip_tags(text)
    parts = re.split(r"[.!?]+", body, maxsplit=1)
    return parts[0].strip() if parts else ""


def spoken_sentences(text):
    return [part.strip() for part in re.split(r"[.!?]+", strip_tags(text)) if part.strip()]


def action_with_later_speech(text):
    for match in re.finditer(r"\[TEACHER_[A-Z_]+\]", text):
        if strip_tags(text[match.end():]).strip():
            return match.group()
    return None


def word_count(text):
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text))


def has_non_latin_script(text):
    for char in text:
        if char.isascii() or char.isspace():
            continue
        name = unicodedata.name(char, "")
        if any(script in name for script in ("CJK", "HIRAGANA", "KATAKANA", "HANGUL", "ARABIC", "CYRILLIC")):
            return True
    return False


def child_first_issues(messages, teacher_name):
    issues = []
    for index, message in enumerate(messages[:-1]):
        if message.get("role") != "user":
            continue
        child = message.get("text", "").strip()
        if child.lower().startswith("the student has been silent"):
            continue
        following = messages[index + 1]
        if following.get("role") != "assistant":
            continue
        opening = first_sentence(following.get("text", ""))
        low = child.lower()

        instruction_question = bool(re.search(
            r"what do i do|what should i do|what am i doing", low
        ))
        if (QUESTION.search(child) and LESSON_FIRST.search(opening)
                and not instruction_question):
            issues.append(
                f"[child-first] question {child!r} got lesson script first: {opening!r}"
            )
        if re.search(r"what(?:'s| is) your name", low):
            expected = f"I'm {teacher_name}" if teacher_name else "I'm your teacher"
            if not opening.lower().startswith(expected.lower()):
                issues.append(
                    f"[answer-name] expected {expected!r} first, got {opening!r}"
                )
        if re.search(r"do you like (?:my )?dog", low) and "dog" not in opening.lower():
            issues.append(f"[answer-dog] dog question not answered first: {opening!r}")
        if re.search(r"how(?:'s| is) the weather", low):
            if not re.search(r"sky|weather|can't see|cannot see", opening, re.I):
                issues.append(
                    f"[answer-weather] weather question not answered first: {opening!r}"
                )
        if instruction_question:
            if not re.search(r"listen|say|you can", opening, re.I):
                issues.append(
                    f"[answer-job] instruction question lacks a clear job: {opening!r}"
                )
        if re.fullmatch(r"why\s*\??", child, re.I):
            if not re.search(r"boo|taste", opening, re.I):
                issues.append(f"[answer-why] why question not answered first: {opening!r}")
    return issues


def check(transcript):
    family = transcript["family"]
    config = CONFIG[family]
    messages = transcript.get("messages", [])
    replies = [m.get("text", "").strip() for m in messages if m.get("role") == "assistant"]
    issues = []

    def violation(rule, detail):
        issues.append(f"[{rule}] {detail}")

    if not replies:
        return ["[empty] no teacher replies"]

    for number, reply in enumerate(replies, 1):
        body = strip_tags(reply)
        tags = CONTROL.findall(reply)
        if len(tags) != 1:
            violation("one-tag", f"reply {number}: found {tags or 'none'}")
        elif not reply.endswith(tags[0]):
            violation("tag-last", f"reply {number}: text follows {tags[0]}")
        if "[WORD_EVALUATION]" in reply:
            violation("old-tag", f"reply {number}: uses [WORD_EVALUATION]")
        if "[STUDENT_TALK]" in reply and not reply.endswith(
                "[TEACHER_LISTEN][STUDENT_TALK]"):
            violation("listen", f"reply {number}: child wait lacks [TEACHER_LISTEN]")
        if transcript.get("prompt_version") == "v2":
            early_action = action_with_later_speech(reply)
            if early_action:
                violation(
                    "action-timing",
                    f"reply {number}: spoken text follows {early_action}",
                )
        if has_non_latin_script(reply):
            violation("english-only", f"reply {number}: non-English script")
        if "..." in reply or "…" in reply or re.search(r"\w\s*[-–—]\s*\w", body):
            violation("tts", f"reply {number}: dash or ellipsis")
        if body.count("!") > 1:
            violation("exclamation", f"reply {number}: {body.count('!')} exclamation marks")
        if body.count("?") > 1:
            violation("question", f"reply {number}: more than one question")
        for sentence in spoken_sentences(reply):
            if word_count(sentence) > 8:
                violation(
                    "pre-a1-length",
                    f"reply {number}: over 8 words: {sentence!r}",
                )
        for pattern in HARD_OUTPUT:
            if re.search(pattern, body, re.I):
                violation("hard-output", f"reply {number}: contains {pattern!r}")
        for pattern in transcript.get("forbid_phrases", []):
            if re.search(pattern, body, re.I):
                violation("forbid-phrase", f"reply {number}: contains {pattern!r}")
        if "[STUDENT_TALK]" in reply:
            tail = " ".join(spoken_sentences(reply)[-2:])
            if not re.search(
                    r"\b(?:try|your turn|say|yes or no|what's your name|are you happy|you can)\b",
                    tail, re.I):
                violation("child-job", f"reply {number}: unclear child job: {tail!r}")

    for index, patterns in (transcript.get("reply_require") or {}).items():
        reply_index = int(index)
        if reply_index > len(replies):
            violation("reply-require", f"reply {reply_index}: missing")
            continue
        body = strip_tags(replies[reply_index - 1])
        for pattern in patterns:
            if not re.search(pattern, body, re.I):
                violation(
                    "reply-require",
                    f"reply {reply_index}: missing {pattern!r}",
                )

    for index, patterns in (transcript.get("reply_forbid") or {}).items():
        reply_index = int(index)
        if reply_index > len(replies):
            continue
        body = strip_tags(replies[reply_index - 1])
        for pattern in patterns:
            if re.search(pattern, body, re.I):
                violation(
                    "reply-forbid",
                    f"reply {reply_index}: contains {pattern!r}",
                )

    first = strip_tags(replies[0])
    if not re.search(config["first"], first, re.I):
        violation("opening", f"unexpected first reply: {first!r}")

    max_replies = transcript.get("max_replies") or 4
    if len(replies) > max_replies:
        violation("reply-budget", f"{len(replies)} replies, max {max_replies}")

    if config["finish"] not in replies[-1]:
        violation("must-finish", f"last reply lacks {config['finish']}")
    for reply in replies[:-1]:
        if config["finish"] in reply:
            violation("early-finish", f"{config['finish']} appears before final reply")

    normalized = {}
    for number, reply in enumerate(replies, 1):
        key = re.sub(r"[^a-z' ]", "", strip_tags(reply).lower())
        key = re.sub(r"\s+", " ", key).strip()
        if key in normalized:
            violation(
                "repeat-reply",
                f"reply {number} repeats reply {normalized[key]}",
            )
        normalized[key] = number

    all_teacher = " ".join(strip_tags(reply) for reply in replies)
    for pattern in transcript.get("require_phrases", []):
        if not re.search(pattern, all_teacher, re.I):
            violation("require-phrase", f"missing {pattern!r}")

    issues.extend(child_first_issues(
        messages, transcript.get("teacher_name", "")
    ))
    return issues


def main():
    failures = 0
    for path in sys.argv[1:]:
        transcript = json.loads(open(path, encoding="utf-8").read())
        issues = check(transcript)
        if issues:
            failures += 1
            print(f"FAIL {path}")
            for issue in issues:
                print("  " + issue)
        else:
            print(f"PASS {path}")
    return failures > 0


if __name__ == "__main__":
    sys.exit(main())
