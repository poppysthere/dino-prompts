#!/usr/bin/env python3
"""Structural checker for the 足球课 wrap-up (ages 4-6, pre-A1).

One-way close, one reply per step: pre-video (praise + 1-2 learned words +
watch line -> [NEXT_STEP]) and post-video (proud close + goodbye ->
[TEMPLATE_FINISH]). No questions, no waits, kid words, TTS safety.

Transcript JSON:
  {"family":"wrapup_soccer","step":"pre_video"|"post_video","student_name":"tom",
   "case":"...","forbid_phrases":[...],"require_phrases":[...],
   "messages":[{"role":"assistant"|"user","text":"..."}...]}

Usage: python3 checker_wrapup_soccer.py transcript.json [...]   (exit 0 = pass)
"""
import json
import re
import sys
import unicodedata

KNOWN_ACTIONS = {"[TEACHER_APPLAUD]", "[TEACHER_THUMBS_UP]", "[TEACHER_HIGH_FIVE]",
                 "[TEACHER_WAVE]"}
FORBIDDEN_TAGS = ["[STUDENT_TALK]", "[WORD_EVALUATION]", "[TEACHER_TALK]"]
LESSON_WORDS = [r"\bgoal\b", r"\bteam\b", r"come\s+on", r"\bsoccer\b", r"\bball\b"]
ANNOUNCER_TALK = [r"team\s+up", r"match\s+is\s+on", r"goal\s+or\s+no\s+goal",
                  r"\bmatch\b", r"\bversus\b", r"\bchampion", r"\bscore\b"]


def has_cjk(t):
    return any(unicodedata.category(c) == "Lo" and "CJK" in unicodedata.name(c, "") for c in t)


def strip_tags(t):
    return re.sub(r"\[[A-Z_]+\]", "", t)


def check(tr):
    step = tr["step"]
    name = tr.get("student_name", "")
    replies = [m["text"].strip() for m in tr["messages"] if m["role"] == "assistant"]
    out = []
    v = lambda rule, msg: out.append(f"[{rule}] {msg}")

    if len(replies) != 1:
        v("one-reply", f"{step} must be exactly 1 reply, got {len(replies)}")
    if not replies:
        return out
    r = replies[0]
    body = strip_tags(r)

    want = "[NEXT_STEP]" if step == "pre_video" else "[TEMPLATE_FINISH]"
    if want not in r:
        v("tag", f"reply does not end the step with {want}")
    elif not r.rstrip().endswith(want):
        v("tag-last", "text after the control tag")
    for t in FORBIDDEN_TAGS + (["[TEMPLATE_FINISH]"] if step == "pre_video" else ["[NEXT_STEP]"]):
        if t in r:
            v("forbidden-tag", f"uses {t}")
    for t in re.findall(r"\[TEACHER_[A-Z_]+\]", r):
        if t not in KNOWN_ACTIONS:
            v("unknown-action", f"{t} is not allowed on the wrap-up")

    if "?" in body:
        v("no-question", f"the wrap-up asks a question nobody waits for: {body.strip()!r}")
    if has_cjk(r):
        v("english-only", "contains non-English characters")
    if "..." in r or "…" in r or re.search(r"\w\s*[-–—]\s*\w", body):
        v("tts-safety", "ellipsis or dash (voice engine breaks)")
    for m in re.finditer(r"[A-Za-z]*([A-Za-z])\1{2,}[A-Za-z]*", body):
        v("tts-stretched", f"stretched spelling {m.group(0)!r}")
    for m in re.finditer(r"\b(hee[\s-]?hee|tee[\s-]?hee|hehe)\b", body, re.I):
        v("tts-giggle", f"giggle spelling {m.group(0)!r}")

    for pat in ANNOUNCER_TALK:
        if re.search(pat, body, re.I):
            v("kid-words", f"announcer talk ({pat!r}): {body.strip()!r}")
    for pat in [r"show\s+me", r"let\s+me\s+see", r"tap\s+the\s+screen", r"\bmeans\b"]:
        if re.search(pat, body, re.I):
            v("invisible-or-teach", f"forbidden move ({pat!r})")

    # 3-4 tiny parts, but "You said Goal! You said team!" splits into bursts and
    # a child-catch ("More play! Yay!") may open the reply — 8 is the ceiling.
    sents = [s for s in re.split(r"(?<=[.!])\s+", body.strip()) if s.strip()]
    if len(sents) > 8:
        v("size", f"{len(sents)} bursts (the wrap-up beat is 3-4 tiny parts + catch)")
    long = [s for s in sents if len(s.split()) > 9]
    if long:
        v("size", f"sentence over the tiny-kid budget: {long[0]!r}")

    if name and name.lower() not in body.lower():
        v("name", f"never says the child's name {name!r}")

    if step == "pre_video":
        if not any(re.search(p, body, re.I) for p in LESSON_WORDS):
            v("recap", f"pre-video recaps none of the lesson words: {body.strip()!r}")
        if not re.search(r"\bwatch\b|\bwrap\b|one\s+last\s+look", body, re.I):
            v("watch-line", "pre-video never leads into the summary video")
        wordish = sum(1 for p in [r"\bgoal\b", r"\bteam\b", r"come\s+on"]
                      if re.search(p, body, re.I))
        if wordish > 2:
            v("recap-budget", "pre-video lists all the words (1-2 is the budget)")
    else:
        if not re.search(r"see\s+you|bye", body, re.I):
            v("goodbye", f"post-video has no goodbye: {body.strip()!r}")

    for pat in tr.get("forbid_phrases", []):
        if re.search(pat, body, re.I):
            v("forbid-phrase", f"contains forbidden phrase {pat!r}")
    for pat in tr.get("require_phrases", []):
        if not re.search(pat, body, re.I):
            v("require-phrase", f"missing required phrase {pat!r}")

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
