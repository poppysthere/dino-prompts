#!/usr/bin/env python3
"""Mechanical checker for the L2 no-warm-up lead-in."""

import json
import re
import sys
import unicodedata

from checker_l2_human import check_child_first


START = ("Today, let's meet Farmer Bob. It is his birthday. First, watch the video. "
         "Look, here he is. Let's watch.")
RESCUE = "Listen first. Hi. Now you try. Hi."
POST_ASK = "Oh no. The cake is gone. Where is it?"
POST_POS = "Yes, it is gone. Look, this is Mouse. Mouse can help us. Let's find the cake."
POST_OTHER = "The cake is gone. Look, this is Mouse. Mouse can help us. Let's find the cake."
GREETING = re.compile(r"\b(?:hi|hello|hey)\b|你好|哈喽", re.I)


def strip_tags(text):
    return re.sub(r"\[[A-Z_]+\]", "", text)


def action_with_later_speech(text):
    for match in re.finditer(r"\[TEACHER_[A-Z_]+\]", text):
        if strip_tags(text[match.end():]).strip():
            return match.group()
    return None


def norm(text):
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", strip_tags(text)).strip().lower()


def script_norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[.!?,]", " ", norm(text))).strip()


def has_cjk(text):
    return any(unicodedata.category(c) == "Lo" and "CJK" in unicodedata.name(c, "")
               for c in text)


def control_tags(text):
    return re.findall(r"\[(?:STUDENT_TALK|TEMPLATE_FINISH|NEXT_STEP|WORD_EVALUATION)\]", text)


def spoken_sentences(text):
    return [s.strip() for s in re.split(r"[.!?]+", strip_tags(text)) if s.strip()]


def word_count(text):
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text))


def usable(value):
    value = (value or "").strip()
    return bool(value and not re.fullmatch(r"\d+", value)
                and value.lower() not in {"test_user", "null", "none"}
                and "{{" not in value)


def check(transcript):
    family = transcript["family"]
    replies = [m["text"] for m in transcript["messages"] if m["role"] == "assistant"]
    users = [m["text"] for m in transcript["messages"] if m["role"] == "user"]
    issues = []
    v = lambda rule, detail: issues.append(f"[{rule}] {detail}")

    for n, reply in enumerate(replies, 1):
        body = strip_tags(reply)
        tags = control_tags(reply)
        if len(tags) != 1:
            v("one-tag", f"reply {n}: {len(tags)} control tags")
        if tags and not reply.rstrip().endswith(tags[-1]):
            v("tag-last", f"reply {n}: text after control tag")
        if reply.rstrip().endswith("[STUDENT_TALK]") and not reply.rstrip().endswith(
                "[TEACHER_LISTEN][STUDENT_TALK]"):
            v("listen-pose", f"reply {n}: wait without listening pose")
        if transcript.get("action_timing"):
            early_action = action_with_later_speech(reply)
            if early_action:
                v("action-timing", f"reply {n}: spoken text follows {early_action}")
        if has_cjk(reply):
            v("english-only", f"reply {n}: non-English teacher output")
        if "..." in reply or "…" in reply or re.search(r"\w\s*[-–—]\s*\w", body):
            v("tts-safety", f"reply {n}: dash or ellipsis")
        if re.search(r"\b(?:say it with me|repeat after me|are you ready)\b", body, re.I):
            v("forbidden-prompt", f"reply {n}: unclear or unnecessary child prompt")
        if body.count("?") > 1:
            v("one-question", f"reply {n}: more than one question")
        if body.count("!") > 1:
            v("too-excited", f"reply {n}: more than one exclamation mark")
        for sentence in spoken_sentences(body):
            if word_count(sentence) > 10:
                v("a1-length", f"reply {n}: sentence over 10 words: {sentence!r}")
        for pattern in transcript.get("forbid_phrases", []):
            if re.search(pattern, body, re.I):
                v("forbid-phrase", f"reply {n}: contains {pattern!r}")

    for index, patterns in (transcript.get("reply_require") or {}).items():
        i = int(index)
        if i > len(replies):
            v("reply-require", f"reply {i}: missing")
            continue
        for pattern in patterns:
            if not re.search(pattern, strip_tags(replies[i - 1]), re.I):
                v("reply-require", f"reply {i}: missing {pattern!r}")

    for index, patterns in (transcript.get("reply_forbid") or {}).items():
        i = int(index)
        if i <= len(replies):
            for pattern in patterns:
                if re.search(pattern, strip_tags(replies[i - 1]), re.I):
                    v("reply-forbid", f"reply {i}: contains {pattern!r}")

    if not replies:
        v("empty", "no teacher replies")
        return issues

    if len(replies) > (transcript.get("max_replies") or 3):
        v("too-long", f"{len(replies)} replies")

    if family == "leadin_pre":
        student = transcript.get("student_name", "")
        teacher = transcript.get("teacher_name", "")
        hello = "Hi"
        if usable(student):
            hello += f", {student}"
        hello += "!"
        if usable(teacher):
            hello += f" I'm {teacher}."
        hello += " Nice to meet you. Say hi to me!"
        if script_norm(hello) != script_norm(replies[0]):
            v("hello-script", f"reply 1 is not the expected hello: {strip_tags(replies[0])!r}")
        if script_norm(START) not in script_norm(replies[-1]):
            v("start-script", "last reply lacks the fixed lesson launch")
        if "[NEXT_STEP]" not in replies[-1]:
            v("must-launch", "last reply lacks [NEXT_STEP]")
        first = users[0] if users else ""
        greeted = bool(GREETING.search(first))
        rescues = sum(script_norm(RESCUE) in script_norm(r) for r in replies)
        if greeted and rescues:
            v("unneeded-rescue", "child greeted but teacher used the hi rescue")
        if not greeted and rescues != 1:
            v("rescue-count", f"non-greeting path used {rescues} rescues, expected 1")
        if greeted and len(replies) != 2:
            v("greeting-length", f"greeting path has {len(replies)} replies, expected 2")
        if not greeted and len(replies) != 3:
            v("rescue-length", f"rescue path has {len(replies)} replies, expected 3")
    elif family == "leadin_post":
        if len(replies) != 2:
            v("post-length", f"post-video has {len(replies)} replies, expected 2")
        if script_norm(POST_ASK) != script_norm(replies[0]):
            v("post-ask", "reply 1 differs from fixed ask")
        if not any(script_norm(line) in script_norm(replies[-1]) for line in (POST_POS, POST_OTHER)):
            v("post-close", "reply 2 lacks a valid fixed continuation")
        if "[TEMPLATE_FINISH]" not in replies[-1]:
            v("must-finish", "reply 2 lacks [TEMPLATE_FINISH]")
        if re.search(r"\bhorse\b", strip_tags(replies[-1]), re.I):
            v("spoiler", "post-video reply named the horse")
    else:
        v("family", f"unknown family {family!r}")

    issues.extend(check_child_first(
        transcript["messages"], transcript.get("teacher_name", ""), family
    ))

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
