#!/usr/bin/env python3
"""Mechanical checker for the L2 sentence-teaching trail (Mouse's three bags).

Steps: intro (1 fixed line, NEXT_STEP) -> sentence_0 cow -> sentence_1 cat
       -> sentence_2 horse + mystery question -> reveal (1 fixed line, TEMPLATE_FINISH).
Transcript JSON: {"family":"sent_cow"|..., "case":..., "student_name":...,
                  "messages":[{role,text}...], "max_replies":N,
                  "forbid_phrases":[...], "require_phrases":[...], "reply_forbid":{"2":[...]}}
Exit 0 = clean, 1 = violations found.
"""
import json
import re
import sys
import unicodedata

STEPS = {
    "sent_intro": {
        "fixed": "Look! Mouse found something! Bags! One two three bags! WOW! What is inside? Let's find out!",
        "final_tag": "[NEXT_STEP]",
        "max": 1,
    },
    "sent_cow": {
        "ask": "Mouse found a bell! A bell! And look. It's a cow! Say it with me. It's a cow!",
        "retry": "Let's say it together. It's a cow!",
        "final_tag": "[NEXT_STEP]",
        "max": 3,
        "spoiler": r"\bhorse\b",
    },
    "sent_cat": {
        "ask": "WOW! Mouse found a fish! A fish! And look. It's a cat! Say it with me. It's a cat!",
        "retry": "Let's say it together. It's a cat!",
        "final_tag": "[NEXT_STEP]",
        "max": 3,
        "spoiler": r"\bhorse\b",
    },
    "sent_horse": {
        "ask": "Wait wait wait! Mouse found something! And look. It's a horse! Say it with me. It's a horse!",
        "retry": "Let's say it together. It's a horse!",
        "question": "who ate the cake",
        "close": "Let's watch the video and find out!",
        "final_tag": "[NEXT_STEP]",
        "max": 4,
        "spoiler": r"(?:\byes\b|\byou got it\b|\bright\b|\bcorrect\b)[^.!?]*\bhorse\b|\bthe horse ate\b",
    },
    "sent_reveal": {
        "must_contain": "The horse ate the cake!",
        "final_tag": "[TEMPLATE_FINISH]",
        "max": 1,
    },
}


def has_cjk(t):
    return any(unicodedata.category(c) == "Lo" and "CJK" in unicodedata.name(c, "") for c in t)


def strip_tags(t):
    return re.sub(r"\[[A-Z_]+\]", "", t)


def norm(t):
    return re.sub(r"\s+", " ", strip_tags(t)).strip().lower()


def control_tags(t):
    return re.findall(r"\[(?:STUDENT_TALK|TEMPLATE_FINISH|NEXT_STEP|WORD_EVALUATION)\]", t)


def check(tr):
    step = STEPS[tr["family"]]
    replies = [m["text"] for m in tr["messages"] if m["role"] == "assistant"]
    out = []
    v = lambda rule, msg: out.append(f"[{rule}] {msg}")

    for n, r in enumerate(replies, 1):
        body = strip_tags(r)
        if "[WORD_EVALUATION]" in r:
            v("no-word-eval", f"reply {n}: [WORD_EVALUATION] is banned")
        tags = control_tags(r)
        if len(tags) != 1:
            v("one-tag", f"reply {n}: {len(tags)} control tags (need exactly 1)")
        if tags and not r.rstrip().endswith(tags[-1]):
            v("tag-last", f"reply {n}: text after the control tag")
        if has_cjk(r):
            v("english-only", f"reply {n}: contains non-English characters")
        if "..." in r or "…" in r or re.search(r"\w\s*[-–—]\s*\w", body):
            v("tts-safety", f"reply {n}: ellipsis or dash (voice engine breaks)")
        for m in re.finditer(r"[A-Za-z]*([A-Za-z])\1{2,}[A-Za-z]*", body):
            v("tts-stretched", f"reply {n}: stretched spelling {m.group(0)!r}")
        for m in re.finditer(r"\b(hee[\s-]?hee|tee[\s-]?hee|hehe)\b", body, re.I):
            v("tts-giggle", f"reply {n}: giggle spelling {m.group(0)!r} (use 'Ha ha!')")
        if re.search(r"can\s+you\s+say", body, re.I):
            v("rising-invite", f"reply {n}: 'can you say' — invites must not be questions")
        if step.get("spoiler") and re.search(step["spoiler"], body, re.I):
            v("spoiler", f"reply {n}: culprit leak (matched {step['spoiler']!r})")
        if r.rstrip().endswith("[STUDENT_TALK]") and not r.rstrip().endswith("[TEACHER_LISTEN][STUDENT_TALK]"):
            v("listen-pose", f"reply {n}: wait without [TEACHER_LISTEN][STUDENT_TALK]")
        for pat in tr.get("forbid_phrases", []):
            if re.search(pat, body, re.I):
                v("forbid-phrase", f"reply {n}: contains forbidden phrase {pat!r}")

    for idx, pats in (tr.get("reply_forbid") or {}).items():
        i = int(idx)
        if i <= len(replies):
            for pat in pats:
                if re.search(pat, strip_tags(replies[i - 1]), re.I):
                    v("reply-forbid", f"reply {i}: contains forbidden phrase {pat!r}")

    all_teacher = " ".join(strip_tags(r) for r in replies)
    for pat in tr.get("require_phrases", []):
        if not re.search(pat, all_teacher, re.I):
            v("require-phrase", f"no teacher reply contains required phrase {pat!r}")

    if not replies:
        v("empty", "no teacher replies at all")
        return out

    n_max = tr.get("max_replies") or step["max"]
    if len(replies) > n_max:
        v("too-long", f"{len(replies)} replies (max {n_max})")

    if step.get("fixed") and norm(step["fixed"]) not in norm(replies[0]):
        v("script-fixed", f"reply 1 deviates from the fixed line: {strip_tags(replies[0]).strip()!r}")
    if step.get("ask") and norm(step["ask"]) not in norm(replies[0]):
        v("script-ask", f"reply 1 deviates from the ASK line: {strip_tags(replies[0]).strip()!r}")
    if step.get("must_contain") and norm(step["must_contain"]) not in norm(replies[0]):
        v("script-reveal", f"reply 1 missing {step['must_contain']!r}: {strip_tags(replies[0]).strip()!r}")

    if step.get("retry"):
        retries = sum(1 for r in replies if norm(step["retry"]) in norm(r))
        if retries > 1:
            v("retry-once", f"the retry call appears {retries} times (max 1, ever)")

    if step.get("question"):
        qs = sum(1 for r in replies if step["question"] in norm(r))
        if qs == 0:
            v("question-missing", "the mystery question never happens")
        elif qs > 1:
            v("question-loop", f"the mystery question asked {qs} times")

    last = replies[-1]
    if step["final_tag"] not in last:
        v("must-advance", f"last reply does not end with {step['final_tag']}")
    if step.get("close"):
        if norm(step["close"]) not in norm(last):
            v("close-line", f"last reply missing the fixed close: {strip_tags(last).strip()!r}")
        else:
            catch = norm(last).split(norm(step["close"]))[0].strip()
            if len(catch.split()) > 8:
                v("catch-budget", f"close catch over budget ({len(catch.split())} words): {catch!r}")
    for r in replies[:-1]:
        if step["final_tag"] in r:
            v("early-advance", f"a reply before the last one contains {step['final_tag']}")
        if "[TEMPLATE_FINISH]" in r:
            v("early-finish", "a reply before the last one ends the template")

    return out


def main():
    bad = 0
    for path in sys.argv[1:]:
        issues = check(json.loads(open(path, encoding="utf-8").read()))
        if issues:
            bad += 1
            print(f"FAIL {path}")
            for i in issues:
                print(f"  {i}")
        else:
            print(f"PASS {path}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
