#!/usr/bin/env python3
"""Mechanical rule checker for word-teaching (talk-first) transcripts.

Checks the structural hard rules of the talk-first word-teaching templates.
Every rule here maps to a real bug found in testing (July 2026).

Input: a JSON transcript file (or stdin), format:
  {
    "word": "bread",
    "opener": "And now. BREAD![TEACHER_BREAK_BREAD] Wow! Yummy bread! Do you like bread?[STUDENT_TALK]",
    "finish_line": "Bread starts with the letter B. What sound does letter B make? Let's play a game to find out!",
    "messages": [ {"role": "assistant"|"user", "text": "..."}, ... ]
  }

Usage: python3 checker.py transcript.json  (or: ... | python3 checker.py)
Exit code 0 = all checks pass, 1 = violations found (printed to stdout).
"""
import json
import re
import sys
import unicodedata


# Action-tag library (notes/teacher_actions.md): tags NOT in this set play no animation
# on the avatar (the "motionless teacher" bug) and are violations.
ACTION_TAGS = {
    "TEACHER_LISTEN", "TEACHER_WAVE", "TEACHER_APPLAUD", "TEACHER_THUMBS_UP",
    "TEACHER_HIGH_FIVE", "TEACHER_POINT_TO_SCREEN", "TEACHER_SHOW_MUSCLE",
    "TEACHER_COW_HORNS", "TEACHER_CAT_PAWS", "TEACHER_RIDE_HORSE",
    "TEACHER_BITE_APPLE", "TEACHER_BREAK_BREAD", "TEACHER_DRINK_JUICE",
}

CONTROL_TAGS = ["[STUDENT_TALK]", "[TEMPLATE_FINISH]", "[WORD_EVALUATION]", "[NEXT_STEP]"]
ALLOWED_CONTROL = ["[STUDENT_TALK]", "[TEMPLATE_FINISH]"]


def has_cjk(text: str) -> bool:
    return any("CJK" in unicodedata.name(ch, "") for ch in text)


def strip_tags(text: str) -> str:
    return re.sub(r"\[[A-Z_]+\]", "", text)


def sentences(text: str):
    parts = re.split(r"[.!?]+", strip_tags(text))
    return [p.strip().lower() for p in parts if len(p.strip()) > 12]


def check(transcript: dict):
    word = transcript["word"].lower()
    opener = transcript["opener"].strip()
    finish_line = transcript["finish_line"].strip()
    msgs = transcript["messages"]
    replies = [m["text"].strip() for m in msgs if m["role"] == "assistant"]
    violations = []

    def v(rule, detail):
        violations.append(f"[{rule}] {detail}")

    # R1: page length 3-4 assistant replies (+1 headroom per silence nudge the client injected)
    nudges = sum(1 for m in msgs if m["role"] == "user" and "has been silent" in m["text"])
    if not (1 <= len(replies) <= 4 + nudges):
        v("page-length", f"{len(replies)} assistant replies (expected 3-4 plus {nudges} silence nudge(s), or fewer if transcript cut early)")

    for i, r in enumerate(reply for reply in replies):
        n = i + 1
        # R2: exactly one control tag, at the very end
        found = [t for t in CONTROL_TAGS if t in r]
        allowed_found = [t for t in ALLOWED_CONTROL if t in r]
        if len(allowed_found) != 1:
            v("one-control-tag", f"reply {n}: control tags found: {found or 'none'}")
        else:
            tag = allowed_found[0]
            if not r.endswith(tag):
                v("tag-at-end", f"reply {n}: does not end with {tag}")
        if "[WORD_EVALUATION]" in r:
            v("no-word-evaluation", f"reply {n}: uses retired [WORD_EVALUATION] tag")

        # R3: English only — no CJK in teacher output
        if has_cjk(r):
            v("english-only", f"reply {n}: contains non-English characters")

        # TTS: stretched spellings are non-words the avatar cannot pronounce
        for m in re.finditer(r"[A-Za-z]*([A-Za-z])\1{2,}[A-Za-z]*", strip_tags(r)):
            v("tts-stretched", f"reply {n}: stretched spelling {m.group(0)!r} (voice engine cannot say it)")
        for m in re.finditer(r"\b(hee[\s-]?hee|tee[\s-]?hee|hehe)\b", strip_tags(r), re.I):
            v("tts-giggle", f"reply {n}: giggle spelling {m.group(0)!r} (voice engine breaks; use 'Ha ha!')")
        for m in re.finditer(r"\[(TEACHER_[A-Z_]+)\]", r):
            if m.group(1) not in ACTION_TAGS:
                v("unknown-action", f"reply {n}: {m.group(0)} is not in the action library (plays no animation)")

        # R4: finish line placement
        if finish_line in r and "[TEMPLATE_FINISH]" not in r:
            v("finish-line-leak", f"reply {n}: finish/handover line without [TEMPLATE_FINISH]")
        if finish_line in r and strip_tags(r).strip().startswith(strip_tags(finish_line).strip()[:20]):
            v("warm-sentence-first", f"reply {n}: finish turn starts with the handover line (no warm sentence first)")

        # R5: TEMPLATE_FINISH position — reply 3+, or reply 2 when the child's
        # first words already contained a word-try (instant-sayer fast path).
        if "[TEMPLATE_FINISH]" in r and n <= 2:
            accepted_early = [word] + [a.lower() for a in transcript.get("accept_variants", [])]
            first_user = next((m["text"].lower() for m in msgs if m["role"] == "user"
                               and not m["text"].startswith("The UI is ready")), "")
            if not (n == 2 and any(a in first_user for a in accepted_early)):
                v("early-finish", f"reply {n}: [TEMPLATE_FINISH] before reply 3 without an instant word-try")
        if "[TEMPLATE_FINISH]" in r and finish_line not in r:
            v("finish-without-line", f"reply {n}: [TEMPLATE_FINISH] without the verbatim finish/handover line")

        # R6: opener rules
        if n == 1 and strip_tags(r).strip() != strip_tags(opener).strip():
            v("opener-verbatim", f"reply 1 is not the fixed opener")
        if n > 1 and strip_tags(opener).strip()[:25].lower() in strip_tags(r).lower():
            v("opener-repeat", f"reply {n}: repeats the fixed opener")

        # R7b: the avatar must visibly listen — [TEACHER_LISTEN] right before [STUDENT_TALK]
        if r.endswith("[STUDENT_TALK]") and not r.endswith("[TEACHER_LISTEN][STUDENT_TALK]"):
            v("listen-pose", f"reply {n}: [STUDENT_TALK] without [TEACHER_LISTEN] right before it")

        # R7: STUDENT_TALK replies must end with the child's job (question or say-it call).
        # A short trailing tag-along after the question is fine ("Tiny bread with me? Little voice."),
        # so look at the last TWO sentences.
        if "[STUDENT_TALK]" in r:
            body = strip_tags(r).strip()
            tail = " ".join(re.split(r"(?<=[.!?])\s+", body)[-2:]) if body else ""
            is_question = "?" in tail
            is_say_call = re.search(rf"\b(say|copy|together|your turn|repeat)\b", tail, re.I) or word in tail.lower()
            if not (is_question or is_say_call):
                v("child-job", f"reply {n}: STUDENT_TALK turn ends on a plain statement: ...{tail[-60:]!r}")

        # R8: TTS safety — no naked single letters as sentences, no ellipses (TTS reads "..." badly)
        for s in re.split(r"[.!?]+", strip_tags(r)):
            if re.fullmatch(r"\s*[A-Za-z]\s*", s or ""):
                v("tts-naked-letter", f"reply {n}: single letter as its own sentence")
        if "..." in r or "\u2026" in r:
            v("tts-ellipsis", f"reply {n}: contains '...' — the voice engine renders it badly")
        if "\u2014" in r or "\u2013" in r or " - " in r:
            v("tts-dash", f"reply {n}: contains a dash — the voice engine makes no pause there; use a period")
        # Only say-it invites may not end the word with "?" (child imitates the rising intonation).
        # Real questions ("Do you like bread?") are fine.
        if re.search(rf"\b(say|copy|repeat)\b[^.!?]*\b{re.escape(word)}\s*\?", strip_tags(r), re.I):
            v("rising-word", f"reply {n}: say-it invite ends with '{word}?' — child imitates the rising intonation")

    # R9: no repeated sentences across the page.
    # Exempt tiny word-calls ("bread bread bread", "your turn") — the target word is
    # the song of the page and may repeat (template hard rule 6).
    chant_words = {word, "your", "turn"}
    seen = {}
    for i, r in enumerate(replies):
        for s in sentences(r):
            if set(s.split()) <= chant_words:
                continue
            if s in seen:
                v("no-repeat", f"reply {i+1} repeats a sentence from reply {seen[s]+1}: {s[:60]!r}")
            else:
                seen[s] = i

    # R10: last reply must finish the page
    if replies and "[TEMPLATE_FINISH]" not in replies[-1]:
        v("must-finish", "last assistant reply does not end the page with [TEMPLATE_FINISH] (transcript may be cut early — verify)")

    # R11: false celebration — "Yes!"-style cheer in a finish turn requires a word-try in any prior user msg
    user_texts = " ".join(m["text"].lower() for m in msgs if m["role"] == "user")
    accepted = [word] + [v.lower() for v in transcript.get("accept_variants", [])]
    said_word = any(v in user_texts for v in accepted)  # exact word + known messy ASR variants; other variants need the LLM judge
    for i, r in enumerate(replies):
        if "[TEMPLATE_FINISH]" in r and re.search(r"\byou said it\b|\byes!\b", r, re.I) and not said_word:
            v("false-celebration", f"reply {i+1}: celebrates 'you said it' but no user message contains '{word}' "
                                   "(mechanical floor check - verify manually, ASR variants may be legitimate)")

    return violations


def main():
    raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    transcript = json.loads(raw)
    violations = check(transcript)
    if violations:
        print(f"FAIL — {len(violations)} violation(s):")
        for vi in violations:
            print("  " + vi)
        sys.exit(1)
    print("PASS — all structural checks OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
