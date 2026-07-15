#!/usr/bin/env python3
"""Structural checker for the 足球课 generic word-teaching page (ages 4-6, pre-A1).

Unlike the L2/L3 word pages, the lines are GENERATED from renderContent
(word + imageDesc), so this checker validates shape and language, not scripts:
beat budget, tag discipline, say-it calls, kid-words, fake praise, TTS safety.

Transcript JSON:
  {"family":"word_soccer","word":"goal","case":"...","student_name":"tom",
   "forbid_phrases":[...],"require_phrases":[...],
   "messages":[{"role":"assistant"|"user","text":"..."}...]}

Usage: python3 checker_word_soccer.py transcript.json [...]   (exit 0 = pass)
"""
import json
import re
import sys
import unicodedata

KNOWN_ACTIONS = {
    "[TEACHER_POINT_TO_SCREEN]", "[TEACHER_APPLAUD]", "[TEACHER_THUMBS_UP]",
    "[TEACHER_HIGH_FIVE]", "[TEACHER_JUMP]", "[TEACHER_LISTEN]", "[TEACHER_WAVE]",
}
FORBIDDEN_TAGS = ["[WORD_EVALUATION]", "[NEXT_STEP]", "[TEACHER_TALK]"]
# Device bug #360001: sports-announcer talk a pre-A1 child cannot picture.
ANNOUNCER_TALK = [r"team\s+up", r"match\s+is\s+on", r"goal\s+or\s+no\s+goal",
                  r"we\s+will\s+see", r"\bmatch\b", r"\bversus\b", r"\bcompete\b",
                  r"\bchampionship\b", r"\bscore\b"]
AGREEMENT_ONLY = re.compile(r"^(好|好的|ok|okay|yes|嗯|恩)[。.!！]?$", re.I)
PRAISE = re.compile(r"great job|you got it|well done|you know it", re.I)


def has_cjk(t):
    return any(unicodedata.category(c) == "Lo" and "CJK" in unicodedata.name(c, "") for c in t)


def strip_tags(t):
    return re.sub(r"\[[A-Z_]+\]", "", t)


def check(tr):
    word = tr["word"].lower()
    msgs = tr["messages"]
    replies = [m["text"].strip() for m in msgs if m["role"] == "assistant"]
    out = []
    v = lambda rule, msg: out.append(f"[{rule}] {msg}")

    if len(replies) > 5:
        v("beat-budget", f"{len(replies)} teacher replies (max 5: meet, retry, play, wonder, close)")
    if replies and "[TEMPLATE_FINISH]" not in replies[-1]:
        v("must-finish", "last reply does not end the page with [TEMPLATE_FINISH]")

    retry_like = 0
    last_user = None
    for i, m in enumerate(msgs):
        if m["role"] == "user":
            last_user = m["text"]
            continue
        r = m["text"].strip()
        n = sum(1 for x in msgs[: i + 1] if x["role"] == "assistant")
        body = strip_tags(r)

        found = [t for t in ("[STUDENT_TALK]", "[TEMPLATE_FINISH]") if t in r]
        if len(found) != 1:
            v("one-tag", f"reply {n}: control tags found: {found or 'none'}")
        elif not r.endswith(found[0]):
            v("tag-last", f"reply {n}: text after the control tag")
        for t in FORBIDDEN_TAGS:
            if t in r:
                v("forbidden-tag", f"reply {n}: uses {t}")
        if "[STUDENT_TALK]" in r and "[TEACHER_LISTEN]" not in r:
            v("listen", f"reply {n}: waits without [TEACHER_LISTEN]")
        for t in re.findall(r"\[TEACHER_[A-Z_]+\]", r):
            if t not in KNOWN_ACTIONS:
                v("unknown-action", f"reply {n}: {t} is not a registered avatar action")

        if has_cjk(r):
            v("english-only", f"reply {n}: contains non-English characters")
        if "..." in r or "…" in r or re.search(r"\w\s*[-–—]\s*\w", body):
            v("tts-safety", f"reply {n}: ellipsis or dash")
        for s in re.finditer(r"[A-Za-z]*([A-Za-z])\1{2,}[A-Za-z]*", body):
            v("tts-stretched", f"reply {n}: stretched spelling {s.group(0)!r}")
        for s in re.finditer(r"\b(hee[\s-]?hee|tee[\s-]?hee|hehe)\b", body, re.I):
            v("tts-giggle", f"reply {n}: giggle spelling {s.group(0)!r}")

        for pat in ANNOUNCER_TALK:
            if re.search(pat, body, re.I):
                v("kid-words", f"reply {n}: announcer talk ({pat!r}): {body.strip()!r}")
        for pat in [r"\bmeans\b", r"\bspell", r"\bletter\b", r"repeat\s+after\s+me"]:
            if re.search(pat, body, re.I):
                v("no-teaching", f"reply {n}: talks ABOUT the word ({pat!r})")
        # request-shaped only: describing the PICTURE ("Friends wave.") is fine
        for pat in [r"show\s+me", r"let\s+me\s+see", r"(can|do|will)\s+you\s+(wave|smile|clap)"]:
            if re.search(pat, body, re.I):
                v("invisible-action", f"reply {n}: asks for something the teacher cannot see ({pat!r})")

        # say-it call shape: "Say it with me. X?" teaches a rising copy
        if re.search(rf"say\s+it\s+with\s+me[.,!\s]+{re.escape(word)}\s*\?", body, re.I):
            v("rising-call", f"reply {n}: say-it call ends on a question mark")

        if n == 1 and word.rstrip("!") not in body.lower():
            v("meet-word", f"reply 1 never says the target word {word!r}")

        # at most ONE real question per reply ("Yes or no?" choice tails are free)
        segs = re.split(r"(?<=[.!?])\s+", body.strip())
        nq = sum(1 for s in segs if s.endswith("?")
                 and len(s.rstrip("?").split()) >= 3
                 and not re.fullmatch(r"yes\s+or\s+no\s*\?", s.strip(), re.I))
        if nq > 1:
            v("one-question", f"reply {n}: {nq} real questions in one reply")
        # the close asks nothing — except the template's tiny opening echo
        # ("No? Ha ha, okay!"), max 2 words, as the very first segment
        if "[TEMPLATE_FINISH]" in r and "?" in body:
            q_idxs = [j for j, s in enumerate(segs) if s.endswith("?")]
            echo_ok = q_idxs == [0] and len(segs[0].rstrip("?").split()) <= 2
            if not echo_ok:
                v("no-question-finish", f"reply {n}: the close still asks: {body.strip()!r}")

        # fake praise: agreement-only child answer must not be celebrated
        if last_user is not None and AGREEMENT_ONLY.match(last_user.strip()) and PRAISE.search(body):
            v("fake-praise", f"reply {n}: praises a child who only agreed: {body.strip()!r}")

        if re.search(r"one\s+more\s+time|let'?s\s+go\s+together|try\s+again", body, re.I):
            retry_like += 1

        for pat in tr.get("forbid_phrases", []):
            if re.search(pat, body, re.I):
                v("forbid-phrase", f"reply {n}: contains forbidden phrase {pat!r}")

    if retry_like > 1:
        v("one-retry", f"{retry_like} retry-shaped replies (the retry happens once, ever)")

    all_teacher = " ".join(strip_tags(r) for r in replies)
    if word.rstrip("!") not in all_teacher.lower():
        v("word-taught", f"the target word {word!r} never appears")
    for pat in tr.get("require_phrases", []):
        if not re.search(pat, all_teacher, re.I):
            v("require-phrase", f"no reply contains required phrase {pat!r}")

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
