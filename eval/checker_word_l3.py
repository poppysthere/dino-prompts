#!/usr/bin/env python3
"""Mechanical checker for L3 word-teaching pages (ASK -> one retry -> close).

L3 word pages are shorter than L2 ones: no animal-sound beat, no wonder question.
Config-driven per word family so later words (jump, run...) plug in here.

Usage: python3 checker_word_l3.py transcript.json [...]
Transcript JSON: {"family":"word_l3_climb","student_name":"...", "case":"...",
                  "forbid_phrases":[...], "require_phrases":[...],
                  "messages":[{role,text}...]}
Exit 0 = clean, 1 = violations found.
"""
import json
import re
import sys
import unicodedata

WORDS = {
    "word_l3_climb": {
        "word": "climb",
        # generous ASR whitelist: right after a say-it call these ARE the word
        "try_re": r"\b(climb\w*|clime|crime|claim)\b",
        "ask_core": ("look! dino and mia see a tall wall. they go up, up, up! "
                     "this is climb. say it with me. climb!"),
        # guided retry (user decision 2026-07-15): the retry must TEACH — tiny
        # real contexts, never a bare "one more time" repeat (prod #357245).
        # punctuation-tolerant: "wall." vs "wall!" is fine
        "retry_re": r"climb a tree\W+climb a wall",
        "bare_retry_re": r"one more time",
        "close_core": "let's climb with dino and mia! climb, climb, climb! up we go!",
        "action": "[TEACHER_CLIMB]",
    },
}

KNOWN_ACTIONS = {
    "[TEACHER_WAVE]", "[TEACHER_THUMBS_UP]", "[TEACHER_APPLAUD]", "[TEACHER_HIGH_FIVE]",
    "[TEACHER_POINT_TO_SCREEN]", "[TEACHER_SHOW_MUSCLE]", "[TEACHER_LISTEN]", "[TEACHER_JUMP]",
    "[TEACHER_COW_HORNS]", "[TEACHER_CAT_PAWS]", "[TEACHER_RIDE_HORSE]",
    "[TEACHER_DRINK_JUICE]", "[TEACHER_BREAK_BREAD]", "[TEACHER_BITE_APPLE]",
    "[TEACHER_CLIMB]",
}
AGREEMENT_RE = r"^\s*(好|好的|ok|okay|yes|嗯|恩)\s*[。.!！]?\s*$"


def has_cjk(t):
    return any(unicodedata.category(c) == "Lo" and "CJK" in unicodedata.name(c, "") for c in t)


def strip_tags(t):
    return re.sub(r"\[[A-Z_]+\]", "", t)


def norm(t):
    t = re.sub(r"\s+", " ", strip_tags(t)).strip().lower()
    # contraction-equivalence: the model occasionally writes "let us" for "let's"
    # (seen 1/20 runs); same meaning, not worth prompt bloat to pin
    return t.replace("let us ", "let's ")


def control_tags(t):
    return re.findall(r"\[(?:STUDENT_TALK|TEMPLATE_FINISH|NEXT_STEP|WORD_EVALUATION|TEACHER_TALK)\]", t)


def check(path):
    tr = json.loads(open(path, encoding="utf-8").read())
    cfg = WORDS[tr["family"]]
    msgs = tr["messages"]
    replies = [m["text"] for m in msgs if m["role"] == "assistant"]
    out = []
    v = lambda rule, msg: out.append(f"[{rule}] {msg}")

    # child msg heard just before each reply (None for reply 1: UI-ready)
    heard = []
    last_user = None
    for m in msgs:
        if m["role"] == "user":
            last_user = m["text"]
        else:
            heard.append(last_user)

    for n, r in enumerate(replies, 1):
        tags = control_tags(r)
        if len(tags) != 1:
            v("one-tag", f"reply {n}: {len(tags)} control tags (need exactly 1)")
        if "[WORD_EVALUATION]" in r:
            v("word-eval", f"reply {n}: legacy [WORD_EVALUATION] used")
        if tags and not r.rstrip().endswith(tags[-1]):
            v("tag-last", f"reply {n}: text after the control tag")
        if "[STUDENT_TALK]" in r and "[TEACHER_LISTEN][STUDENT_TALK]" not in r.replace(" ", ""):
            v("listen-pose", f"reply {n}: wait without [TEACHER_LISTEN] glued to [STUDENT_TALK]")
        if has_cjk(r):
            v("english-only", f"reply {n}: contains non-English characters")
        if "..." in r or "…" in r or re.search(r"\w\s*[-–—]\s*\w", strip_tags(r)):
            v("tts-safety", f"reply {n}: ellipsis or dash (voice engine breaks)")
        for m in re.finditer(r"[A-Za-z]*([A-Za-z])\1{2,}[A-Za-z]*", strip_tags(r)):
            v("tts-stretched", f"reply {n}: stretched spelling {m.group(0)!r}")
        for m in re.finditer(r"\b(hee[\s-]?hee|tee[\s-]?hee|hehe)\b", strip_tags(r), re.I):
            v("tts-giggle", f"reply {n}: giggle spelling {m.group(0)!r} (use 'Ha ha!')")
        if re.search(r"\bmeans\b", strip_tags(r), re.I):
            v("word-teach-leak", f"reply {n}: explains the word ('means') instead of showing it")
        if re.search(rf"can you say\b", strip_tags(r), re.I):
            v("rising-invite", f"reply {n}: say-it invite phrased as a question")
        for t in re.findall(r"\[TEACHER_[A-Z_]+\]", r):
            if t not in KNOWN_ACTIONS:
                v("unknown-action", f"reply {n}: {t} is not a registered avatar action")
        for pat in tr.get("forbid_phrases", []):
            if re.search(pat, strip_tags(r), re.I):
                v("forbid-phrase", f"reply {n}: contains forbidden phrase {pat!r}")
        # praise guard: "great job" only right after a real English try
        if re.search(r"great job", r, re.I):
            h = heard[n - 1] or ""
            if h.startswith("The student has been silent") or not re.search(cfg["try_re"], h, re.I):
                v("fake-praise", f"reply {n}: praises a try the child never made (heard: {h!r})")

    for pat in tr.get("require_phrases", []):
        if not any(re.search(pat, strip_tags(r), re.I) for r in replies):
            v("require-phrase", f"no reply contains required phrase {pat!r}")

    if not 2 <= len(replies) <= 3:
        v("reply-count", f"page must be 2-3 replies, got {len(replies)}")
    if replies:
        if cfg["ask_core"] not in norm(replies[0]):
            v("script-ask", f"reply 1 is not the ASK line: {strip_tags(replies[0]).strip()!r}")
        last = replies[-1]
        if "[TEMPLATE_FINISH]" not in last:
            v("must-finish", "last reply does not end the page with [TEMPLATE_FINISH]")
        if cfg["close_core"] not in norm(last):
            v("script-close", f"last reply is missing the close line: {strip_tags(last).strip()!r}")
    retry_re = re.compile(cfg["retry_re"], re.I)
    n_retry = sum(1 for r in replies if retry_re.search(norm(r)))
    if n_retry > 1:
        v("retry-once", f"the retry call was spoken {n_retry} times (max 1, ever)")
    # a 3-reply page means the retry fired: it must be the GUIDED retry
    if len(replies) == 3 and not retry_re.search(norm(replies[1])):
        v("guided-retry", f"reply 2 retries without the teaching contexts: {strip_tags(replies[1]).strip()!r}")
    for n, r in enumerate(replies, 1):
        if re.search(cfg["bare_retry_re"], strip_tags(r), re.I):
            v("bare-retry", f"reply {n}: bare 'one more time' repeat (the retry must teach, prod #357245)")
    return out


def main():
    bad = 0
    for path in sys.argv[1:]:
        issues = check(path)
        if issues:
            bad += 1
            print(f"FAIL {path}")
            for i in issues:
                print(f"  {i}")
        else:
            print(f"PASS {path}")
    sys.exit(1 if bad else 0)


main()
