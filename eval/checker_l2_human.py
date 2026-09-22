#!/usr/bin/env python3
"""Shared child-first checks for interactive L2 transcripts."""

import re


QUESTION = re.compile(
    r"\?|\b(?:what(?:'s| is)|who|where|why|how(?:'s| is)|do you|can you|are you)\b",
    re.I,
)
ROBOTIC_FIRST = re.compile(
    r"^(?:moo moo|meow meow|neigh neigh|listen\b|look\b|that's okay\b|"
    r"okay\b|a (?:cow|cat|horse) says\b|who has\b|does the\b|let's\b)",
    re.I,
)


def strip_tags(text):
    return re.sub(r"\[[A-Z_]+\]", "", text).strip()


def first_sentence(text):
    body = strip_tags(text)
    parts = re.split(r"[.!?]+", body, maxsplit=1)
    return parts[0].strip() if parts else ""


def check_child_first(messages, teacher_name="", family=""):
    """Return violations when a real child question gets lesson boilerplate first."""
    issues = []
    teacher = (teacher_name or "").strip()
    for index, message in enumerate(messages[:-1]):
        if message.get("role") != "user":
            continue
        child = message.get("text", "").strip()
        if child.lower().startswith("the student has been silent"):
            continue
        # On this page, a lone "How?" is a known ASR form of cow, not a question.
        if family == "word_cow" and re.fullmatch(r"how\s*\?", child, re.I):
            continue
        if not QUESTION.search(child):
            continue
        following = messages[index + 1]
        if following.get("role") != "assistant":
            issues.append("[child-first] question has no following teacher reply")
            continue
        opening = first_sentence(following.get("text", ""))
        if not opening:
            issues.append("[child-first] question received an empty teacher reply")
            continue
        if ROBOTIC_FIRST.search(opening):
            issues.append(
                f"[child-first] question {child!r} received lesson boilerplate first: {opening!r}"
            )
        if re.search(r"what(?:'s| is) your name", child, re.I):
            expected = f"I'm {teacher}" if teacher else "I'm your teacher"
            if not opening.lower().startswith(expected.lower()):
                issues.append(
                    f"[answer-name] expected first sentence to start {expected!r}, got {opening!r}"
                )
        if re.search(r"do you like (?:my )?dog", child, re.I) and "dog" not in opening.lower():
            issues.append(f"[answer-dog] first sentence does not answer the dog question: {opening!r}")
        if re.search(r"how(?:'s| is) the weather", child, re.I):
            if not re.search(r"sky|outside|weather|not sure|don't know|can't see", opening, re.I):
                issues.append(
                    f"[answer-weather] first sentence does not answer the weather question: {opening!r}"
                )
    return issues
