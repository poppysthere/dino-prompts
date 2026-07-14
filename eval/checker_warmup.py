#!/usr/bin/env python3
"""Mechanical rule checker for Warm Up (state machine) transcripts.

Encodes the hard rules of the L2 warm-up template (originals/warmup_l2_lesson0_original.md):
path dispatch on isFirstMeet, path-B forbidden phrases, one question per beat,
silence escalation, no invisible-action requests, tag discipline, TTS safety.

Transcript JSON:
  {
    "family": "warmup",
    "is_first_meet": true|false,
    "student_name": "heidi",          # the profile/default name
    "spoken_name": "Lily",            # optional: name the child states during the case
    "max_beats": 7,                   # optional: override the per-path beat budget (L1 warm-up is longer)
    "forbid_phrases": ["\\bape\\b"],  # optional: regexes that must not appear in any teacher reply
    "require_phrases": ["huide|heidi"] # optional: regexes that must appear in at least one teacher reply
    "case": "...",
    "messages": [ {"role": "assistant"|"user", "text": "..."}, ... ]
  }

Usage: python3 checker_warmup.py transcript.json   (exit 0 = pass)
"""
import json
import re
import sys
import unicodedata

ALLOWED_CONTROL = ["[STUDENT_TALK]", "[TEMPLATE_FINISH]"]
FORBIDDEN_TAGS = ["[NEXT_STEP]", "[WORD_EVALUATION]", "[TEACHER_TALK]"]

# Path B (returning student) — first-meeting phrases are forbidden the whole warm-up.
PATH_B_FORBIDDEN = [
    r"what\s+is\s+your\s+name", r"what'?s\s+your\s+name", r"tell\s+me\s+your\s+name",
    r"may\s+i\s+know\s+your\s+name",
    r"\bi'?m\s+teacher\b", r"\bmy\s+name\s+is\b", r"let\s+me\s+introduce",
    r"nice\s+to\s+meet\s+you",
]

# Registered avatar animations (notes/teacher_actions.md) — anything else is
# an invented tag the client cannot render (run 6: model produced [TEACHER_SALUTE]).
KNOWN_ACTIONS = {
    "[TEACHER_WAVE]", "[TEACHER_THUMBS_UP]", "[TEACHER_APPLAUD]", "[TEACHER_HIGH_FIVE]",
    "[TEACHER_POINT_TO_SCREEN]", "[TEACHER_SHOW_MUSCLE]", "[TEACHER_LISTEN]", "[TEACHER_JUMP]",
    "[TEACHER_COW_HORNS]", "[TEACHER_CAT_PAWS]", "[TEACHER_RIDE_HORSE]",
    "[TEACHER_DRINK_JUICE]", "[TEACHER_BREAK_BREAD]", "[TEACHER_BITE_APPLE]",
}

# The teacher cannot see the child — no requests for visible actions.
INVISIBLE_ACTIONS = [
    r"\bwave\b", r"thumbs\s+up", r"big\s+smile", r"touch\s+your",
    r"show\s+me\s+your", r"clap\s+your\s+hands.*\?",
]


def has_cjk(text: str) -> bool:
    return any("CJK" in unicodedata.name(ch, "") for ch in text)


def strip_tags(text: str) -> str:
    return re.sub(r"\[[A-Z_]+\]", "", text)


def check(transcript: dict):
    first_meet = bool(transcript["is_first_meet"])
    name = transcript.get("student_name", "").lower()
    msgs = transcript["messages"]
    replies = [m["text"].strip() for m in msgs if m["role"] == "assistant"]
    violations = []

    def v(rule, detail):
        violations.append(f"[{rule}] {detail}")

    # Beat budget (shortened 2026-07-13, retention data: kids quit before the video):
    # path A = 3 beats, path B = 2; +1 per silence nudge;
    # +1 slack for a child-derail (their own question etc. costs one extra beat).
    nudges = sum(1 for m in msgs if m["role"] == "user" and "has been silent" in m["text"])
    max_beats = transcript.get("max_beats") or ((3 if first_meet else 2) + nudges + 1)
    if len(replies) > max_beats:
        v("beat-budget", f"{len(replies)} teacher beats (max {max_beats} for this path incl. {nudges} silence nudge(s) + 1 slack)")

    # Name handling (prod bug 2026-07-12: "Lily! Hi, rosa." — spoken name must WIN,
    # the default/profile name must disappear, never both in one reply).
    spoken = transcript.get("spoken_name", "").lower()
    if spoken and name and spoken != name:
        child_said_name = False
        beat_no = 0
        for m in msgs:
            if m["role"] == "user":
                if spoken in m["text"].lower() or transcript.get("spoken_name_l1", "") and transcript["spoken_name_l1"] in m["text"]:
                    child_said_name = True
                continue
            beat_no += 1
            low = strip_tags(m["text"]).lower()
            if spoken in low and name in low:
                v("name-mix", f"beat {beat_no}: both the spoken name '{spoken}' and the default name '{name}' in one reply")
            elif child_said_name and name in low:
                v("stale-name", f"beat {beat_no}: still says default name '{name}' after the child said their name is '{spoken}'")

    silence_streak = 0
    last_user = None
    for m in msgs:
        if m["role"] == "user":
            last_user = m["text"]
            if "has been silent" in m["text"]:
                silence_streak += 1
            else:
                silence_streak = 0
            continue

        r = m["text"].strip()
        n = sum(1 for x in msgs[: msgs.index(m) + 1] if x["role"] == "assistant")
        body = strip_tags(r)

        # tags: exactly one allowed control tag, at the very end; forbidden tags never
        found = [t for t in ALLOWED_CONTROL if t in r]
        if len(found) != 1:
            v("one-control-tag", f"beat {n}: control tags found: {found or 'none'}")
        elif not r.endswith(found[0]):
            v("tag-at-end", f"beat {n}: does not end with {found[0]}")
        for t in FORBIDDEN_TAGS:
            if t in r:
                v("forbidden-tag", f"beat {n}: uses {t} — warm up may not")
        for t in re.findall(r"\[TEACHER_[A-Z_]+\]", r):
            if t not in KNOWN_ACTIONS:
                v("unknown-action", f"beat {n}: {t} is not a registered avatar action (see notes/teacher_actions.md)")

        if has_cjk(r):
            v("english-only", f"beat {n}: contains non-English characters")

        # one question per beat; the finish beat may contain no question at all.
        # Not counted as questions: "Yes or no?" choice-prompts (the silence rule
        # prescribes them) and 1-2 word echo interjections ("Hmm?", "A cat?").
        segments = re.split(r"(?<=[.!?])\s+", body.strip())
        nq = sum(1 for s in segments
                 if s.endswith("?")
                 and len(s.rstrip("?").split()) >= 3
                 and not re.fullmatch(r"yes\s+or\s+no\s*\?", s.strip(), re.I))
        if nq > 1:
            v("one-question", f"beat {n}: {nq} questions in one beat")
        if "[TEMPLATE_FINISH]" in r and nq > 0:
            # L3 (7-9): ONE rhetorical echo is human, but only as the OPENING
            # segment ("You won? No WAY!..."). A real question buried later in
            # the close is a fake ask the teacher never waits for (run 6,
            # b3-answer-first: "...How are you today? Alright, let's go!").
            is_l3 = transcript.get("family") == "warmup_l3"
            q_idxs = [i for i, s in enumerate(segments)
                      if s.endswith("?") and len(s.rstrip("?").split()) >= 3]
            opening_echo_only = (q_idxs == [0]
                                 and len(segments[0].rstrip("?").split()) <= 8)
            if not (is_l3 and nq == 1 and opening_echo_only):
                v("no-question-on-finish", f"beat {n}: finish beat still asks a question")

        # path B forbidden phrases (the prod bug this template exists to prevent)
        if not first_meet:
            for pat in PATH_B_FORBIDDEN:
                if re.search(pat, body, re.I):
                    v("path-b-forbidden", f"beat {n}: first-meeting phrase {pat!r} with a returning student")
            if n == 1 and name and name not in body.lower():
                v("path-b-name", f"beat 1: returning student not greeted by name '{name}'")
            if n == 1 and not re.search(r"\bagain\b|\bback\b", body, re.I):
                v("path-b-again", "beat 1: no 'again/back' (seeing-you-again wording) for a returning student")
        else:
            if n == 1 and not re.search(r"\bname\b", body, re.I):
                v("path-a-ask-name", "beat 1: first meeting but the teacher never asks the name")
            if n == 1 and name and name in body.lower():
                v("path-a-name-leak", f"beat 1: says '{name}' before the child ever gave it")

        for pat in INVISIBLE_ACTIONS:
            if re.search(pat, body, re.I):
                v("invisible-action", f"beat {n}: asks for an action the teacher cannot see ({pat!r})")

        # case-specific forbidden phrases (e.g. name-mock regression: "appe" -> "Ape!")
        for pat in transcript.get("forbid_phrases", []):
            if re.search(pat, body, re.I):
                v("forbid-phrase", f"beat {n}: contains forbidden phrase {pat!r}")

        # word-teaching leak (prod #350750: 'From means start... Can you say from?'):
        # the warm-up never explains words or assigns repeat-tasks
        for pat in [r"\bmeans\b", r"can\s+you\s+say", r"repeat\s+after\s+me"]:
            if re.search(pat, body, re.I):
                v("word-teach-leak", f"beat {n}: warm-up is teaching vocabulary ({pat!r})")

        # cut beats (2026-07-13 shortening): no age question, no separate ready-wait
        if re.search(r"how\s+old\s+are\s+you", body, re.I):
            v("age-question", f"beat {n}: asks the age — cut from the warm up (kids quit when the opening drags)")
        if re.search(r"are\s+you\s+ready", body, re.I) and "[STUDENT_TALK]" in r:
            v("ready-wait", f"beat {n}: parks on a separate 'are you ready' wait — readiness belongs inside the close")

        # silence escalation (2-rung ladder): after the 2nd consecutive silence the beat MUST finish
        if last_user is not None and silence_streak >= 2 and "[TEMPLATE_FINISH]" not in r:
            v("silence-escalation", f"beat {n}: 2nd consecutive silence but warm up still not finished")

        # TTS safety (same device findings as the word pages)
        if "..." in r or "\u2026" in r:
            v("tts-ellipsis", f"beat {n}: contains '...'")
        if "\u2014" in r or "\u2013" in r or " - " in r:
            v("tts-dash", f"beat {n}: contains a dash")
        # stretched spellings ("Hiiii", "squeeeeze") — the avatar cannot pronounce non-words
        for m in re.finditer(r"[A-Za-z]*([A-Za-z])\1{2,}[A-Za-z]*", body):
            v("tts-stretched", f"beat {n}: stretched spelling {m.group(0)!r} (voice engine cannot say it)")

        # written giggles ("hee hee", "teehee", "hehe") sound broken; only "ha ha" is safe
        for m in re.finditer(r"\b(hee[\s-]?hee|tee[\s-]?hee|hehe)\b", body, re.I):
            v("tts-giggle", f"beat {n}: giggle spelling {m.group(0)!r} (voice engine breaks; use 'Ha ha!')")

        # STUDENT_TALK beats must end with the child's job (question or say-it call)
        if "[STUDENT_TALK]" in r:
            tail = " ".join(re.split(r"(?<=[.!?])\s+", body.strip())[-2:])
            if "?" not in tail and not re.search(r"\b(say|your turn)\b", tail, re.I):
                v("child-job", f"beat {n}: STUDENT_TALK beat ends on a plain statement: ...{tail[-60:]!r}")

    # question loop (prod bug 2026-07-13 #350425: "Are you happy today?" asked 3x):
    # the same normalized question sentence in 3+ beats is a broken-robot loop.
    from collections import Counter
    qnorm = []
    for r in replies:
        segs = re.split(r"(?<=[.!?])\s+", strip_tags(r).strip())
        q = next((s for s in reversed(segs) if s.strip().endswith("?")), None)
        qnorm.append(re.sub(r"[^a-z ]", "", q.lower()).strip() if q else None)
    for q, cnt in Counter(q for q in qnorm if q).items():
        if cnt >= 3:
            v("question-loop", f"the question {q!r} is asked {cnt} times in one warm-up")

    # case-specific required phrases (e.g. the child's name attempt must be echoed back)
    all_teacher = " ".join(strip_tags(r) for r in replies)
    for pat in transcript.get("require_phrases", []):
        if not re.search(pat, all_teacher, re.I):
            v("require-phrase", f"no teacher reply contains required phrase {pat!r}")

    # the warm up must actually finish
    if replies and "[TEMPLATE_FINISH]" not in replies[-1]:
        v("must-finish", "last beat does not end the warm up with [TEMPLATE_FINISH] (transcript may be cut early — verify)")

    # no two identical beats (word-for-word repeats read as a stuck teacher)
    seen = {}
    for i, r in enumerate(replies):
        key = strip_tags(r).strip().lower()
        if key in seen:
            v("no-repeat-beat", f"beat {i+1} is word-for-word identical to beat {seen[key]+1}")
        else:
            seen[key] = i

    return violations


def main():
    raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    violations = check(json.loads(raw))
    if violations:
        print(f"FAIL — {len(violations)} violation(s):")
        for vi in violations:
            print("  " + vi)
        sys.exit(1)
    print("PASS — all warm-up structural checks OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
