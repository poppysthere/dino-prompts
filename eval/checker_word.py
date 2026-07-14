#!/usr/bin/env python3
"""Mechanical checker for L2 word pages (Mouse's cake mystery).

Shape: MEET -> try (max 1 retry) -> animal-sound invite -> sound react + wonder -> close.
One checker for every word page; per-word lines live in WORDS below.
Transcript JSON: {"family":"word_cow"|"word_cat","case":"...","student_name":"...",
                  "messages":[{role,text}...], "max_replies":N,
                  "forbid_phrases":[...], "require_phrases":[...], "reply_forbid":{"2":[...]}}
Exit 0 = clean, 1 = violations found.
"""
import json
import re
import sys
import unicodedata

WORDS = {
    "word_cow": {
        "meet": "Mouse sees a cow! A COW! Cow! Say it with me. Cow!",
        "retry": "Let's go together. Cow. Cow. One more time. Cow!",
        "close": "Let's keep looking. Come on, Mouse!",
        "spoiler": r"\bhorse\b",  # culprit word banned on non-horse pages
    },
    "word_cat": {
        "meet": "Mouse sees a cat! A CAT! Cat! Say it with me. Cat!",
        "retry": "Let's go together. Cat. Cat. One more time. Cat!",
        "close": "Let's keep looking. Come on, Mouse!",
        "close_tag": "[TEACHER_SHOW_MUSCLE]",
        "spoiler": r"\bhorse\b",
    },
    "word_horse": {
        "meet": "Mouse sees a horse! A HORSE! Horse! Say it with me. Horse!",
        "retry": "Let's go together. Horse. Horse. One more time. Horse!",
        "close": "Let's go find out!",
        "close_tag": "[TEACHER_RIDE_HORSE]",
        # teacher says "horse" all page, but must never CONFIRM the culprit
        "spoiler": r"(?:\byes\b|\byou got it\b|\bright\b|\bcorrect\b)[^.!?]*\bhorse\b[^.!?]*\b(?:ate|did)\b|\bthe horse ate\b",
    },
}
WONDER = "who ate the cake"


def has_cjk(t):
    return any(unicodedata.category(c) == "Lo" and "CJK" in unicodedata.name(c, "") for c in t)


def strip_tags(t):
    return re.sub(r"\[[A-Z_]+\]", "", t)


def norm(t):
    return re.sub(r"\s+", " ", strip_tags(t)).strip().lower()


def control_tags(t):
    return re.findall(r"\[(?:STUDENT_TALK|TEMPLATE_FINISH|NEXT_STEP|WORD_EVALUATION)\]", t)


def check(tr):
    word = WORDS[tr["family"]]
    replies = [m["text"] for m in tr["messages"] if m["role"] == "assistant"]
    out = []
    v = lambda rule, msg: out.append(f"[{rule}] {msg}")

    for n, r in enumerate(replies, 1):
        body = strip_tags(r)
        if "[WORD_EVALUATION]" in r:
            v("no-word-eval", f"reply {n}: [WORD_EVALUATION] is banned on this page")
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
            v("rising-invite", f"reply {n}: 'can you say' — say-it invites must not be questions")
        if word.get("spoiler") and re.search(word["spoiler"], body, re.I):
            v("spoiler", f"reply {n}: culprit leak (matched {word['spoiler']!r})")
        if r.rstrip().endswith("[STUDENT_TALK]") and not r.rstrip().endswith("[TEACHER_LISTEN][STUDENT_TALK]"):
            v("listen-pose", f"reply {n}: wait without the listening pose (must end [TEACHER_LISTEN][STUDENT_TALK])")
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

    if norm(word["meet"]) not in norm(replies[0]):
        v("script-meet", f"reply 1 deviates from the MEET line: {strip_tags(replies[0]).strip()!r}")

    n_max = tr.get("max_replies") or 5
    if len(replies) > n_max:
        v("too-long", f"{len(replies)} replies (max {n_max} for this case)")

    retries = sum(1 for r in replies if norm(word["retry"]) in norm(r))
    if retries > 1:
        v("retry-once", f"the retry call appears {retries} times (max 1, ever)")

    wonders = sum(1 for r in replies if WONDER in norm(r))
    if wonders == 0:
        v("wonder-missing", "the cake wonder question never happens")
    elif wonders > 1:
        v("wonder-loop", f"the wonder question asked {wonders} times")

    last = replies[-1]
    if "[TEMPLATE_FINISH]" not in last:
        v("must-finish", "last reply does not end the page with [TEMPLATE_FINISH]")
    if word.get("close_tag") and word["close_tag"] not in last:
        v("close-action", f"last reply missing the close action tag {word['close_tag']}")
    if norm(word["close"]) not in norm(last):
        v("close-line", f"last reply missing the fixed close: {strip_tags(last).strip()!r}")
    else:
        catch = norm(last).split(norm(word["close"]))[0].strip()
        if len(catch.split()) > 8:
            v("catch-budget", f"close catch over budget ({len(catch.split())} words): {catch!r}")
    for r in replies[:-1]:
        if "[TEMPLATE_FINISH]" in r:
            v("early-finish", "a reply before the last one ends the page")

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
