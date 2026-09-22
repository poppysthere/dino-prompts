#!/usr/bin/env python3
"""Mechanical checker for the L2 cow, cat, and horse word pages."""

import json
import re
import sys
import unicodedata


WORDS = {
    "word_cow": {
        "meet": "Look! Mouse sees a cow. Cow. Listen first. Cow. Now you try. Cow.",
        "retry": "Let's try again. Cow. Now you try. Cow.",
        "question": "Does the cow have the cake? Say yes or no.",
        "close": "Let's keep looking, Mouse!",
    },
    "word_cat": {
        "meet": "Look! Mouse sees a cat. Cat. Listen first. Cat. Now you try. Cat.",
        "retry": "Let's try again. Cat. Now you try. Cat.",
        "question": "Does the cat have the cake? Say yes or no.",
        "close": "Let's keep looking, Mouse!",
        "close_tag": "[TEACHER_SHOW_MUSCLE]",
    },
    "word_horse": {
        "meet": "Look! Mouse sees a horse. Horse. Listen first. Horse. Now you try. Horse.",
        "retry": "Let's try again. Horse. Now you try. Horse.",
        "question": "Does the horse have the cake? Say yes or no.",
        "close": "Let's watch and find out!",
        "close_tag": "[TEACHER_RIDE_HORSE]",
        "spoiler": r"\bthe horse ate\b|\bhorse (?:did|took) it\b|\byes[^.!?]*horse[^.!?]*(?:cake|ate|took)\b",
    },
}


def has_cjk(text):
    return any(unicodedata.category(c) == "Lo" and "CJK" in unicodedata.name(c, "")
               for c in text)


def strip_tags(text):
    return re.sub(r"\[[A-Z_]+\]", "", text)


def norm(text):
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", strip_tags(text)).strip().lower()


def script_norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[.!?,]", " ", norm(text))).strip()


def control_tags(text):
    return re.findall(r"\[(?:STUDENT_TALK|TEMPLATE_FINISH|NEXT_STEP|WORD_EVALUATION)\]", text)


def spoken_sentences(text):
    return [s.strip() for s in re.split(r"[.!?]+", strip_tags(text)) if s.strip()]


def word_count(text):
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text))


def check(transcript):
    config = WORDS[transcript["family"]]
    replies = [m["text"] for m in transcript["messages"] if m["role"] == "assistant"]
    issues = []
    v = lambda rule, detail: issues.append(f"[{rule}] {detail}")

    for n, reply in enumerate(replies, 1):
        body = strip_tags(reply)
        tags = control_tags(reply)
        if "[WORD_EVALUATION]" in reply:
            v("no-word-eval", f"reply {n}: retired [WORD_EVALUATION] tag")
        if len(tags) != 1:
            v("one-tag", f"reply {n}: {len(tags)} control tags")
        if tags and not reply.rstrip().endswith(tags[-1]):
            v("tag-last", f"reply {n}: text after control tag")
        if reply.rstrip().endswith("[STUDENT_TALK]") and not reply.rstrip().endswith(
                "[TEACHER_LISTEN][STUDENT_TALK]"):
            v("listen-pose", f"reply {n}: wait without listening pose")
        if has_cjk(reply):
            v("english-only", f"reply {n}: non-English teacher output")
        if "..." in reply or "…" in reply or re.search(r"\w\s*[-–—]\s*\w", body):
            v("tts-safety", f"reply {n}: dash or ellipsis")
        if re.search(r"\b(?:say it with me|repeat after me|can you say)\b", body, re.I):
            v("clear-instruction", f"reply {n}: unclear or rising imitation prompt")
        if re.search(r"\b(?:investigation|detective|culprit|belongs|adventure)\b", body, re.I):
            v("a1-wording", f"reply {n}: avoidable non-A1 word")
        if body.count("?") > 1:
            v("one-question", f"reply {n}: more than one question")
        for sentence in spoken_sentences(body):
            if word_count(sentence) > 10:
                v("a1-length", f"reply {n}: sentence over 10 words: {sentence!r}")
        for match in re.finditer(r"[A-Za-z]*([A-Za-z])\1{2,}[A-Za-z]*", body):
            v("tts-stretched", f"reply {n}: stretched spelling {match.group(0)!r}")
        if config.get("spoiler") and re.search(config["spoiler"], body, re.I):
            v("spoiler", f"reply {n}: revealed the cake answer")
        for pattern in transcript.get("forbid_phrases", []):
            if re.search(pattern, body, re.I):
                v("forbid-phrase", f"reply {n}: contains {pattern!r}")

    for index, patterns in (transcript.get("reply_forbid") or {}).items():
        i = int(index)
        if i <= len(replies):
            for pattern in patterns:
                if re.search(pattern, strip_tags(replies[i - 1]), re.I):
                    v("reply-forbid", f"reply {i}: contains {pattern!r}")

    for index, patterns in (transcript.get("reply_require") or {}).items():
        i = int(index)
        if i > len(replies):
            v("reply-require", f"reply {i}: missing")
            continue
        for pattern in patterns:
            if not re.search(pattern, strip_tags(replies[i - 1]), re.I):
                v("reply-require", f"reply {i}: missing {pattern!r}")

    all_teacher = " ".join(strip_tags(r) for r in replies)
    for pattern in transcript.get("require_phrases", []):
        if not re.search(pattern, all_teacher, re.I):
            v("require-phrase", f"missing {pattern!r}")

    if not replies:
        v("empty", "no teacher replies")
        return issues

    if script_norm(config["meet"]) not in script_norm(replies[0]):
        v("script-meet", f"reply 1 does not match MEET: {strip_tags(replies[0])!r}")

    max_replies = transcript.get("max_replies") or 5
    if len(replies) > max_replies:
        v("too-long", f"{len(replies)} replies, max {max_replies}")

    retries = sum(script_norm(config["retry"]) in script_norm(r) for r in replies)
    if retries > 1:
        v("retry-once", f"retry appears {retries} times")

    questions = sum(script_norm(config["question"]) in script_norm(r) for r in replies)
    if questions != 1:
        v("cake-question", f"cake question appears {questions} times, expected 1")

    last = replies[-1]
    if "[TEMPLATE_FINISH]" not in last:
        v("must-finish", "last reply lacks [TEMPLATE_FINISH]")
    if config.get("close_tag") and config["close_tag"] not in last:
        v("close-action", f"last reply lacks {config['close_tag']}")
    if script_norm(config["close"]) not in script_norm(last):
        v("close-line", f"last reply lacks {config['close']!r}")
    for reply in replies[:-1]:
        if "[TEMPLATE_FINISH]" in reply:
            v("early-finish", "page finished before last reply")

    return issues


def main():
    bad = 0
    for path in sys.argv[1:]:
        issues = check(json.loads(open(path, encoding="utf-8").read()))
        if issues:
            bad += 1
            print(f"FAIL {path}")
            for issue in issues:
                print("  " + issue)
        else:
            print(f"PASS {path}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
