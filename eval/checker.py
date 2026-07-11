#!/usr/bin/env python3
"""Mechanical rule checker for word-teaching (talk-first) transcripts.

Checks the structural hard rules of the talk-first word-teaching templates.
Every rule here maps to a real bug found in testing (July 2026).

Input: a JSON transcript file (or stdin), format:
  {
    "word": "bread",
    "opener": "And now — BREAD![TEACHER_BREAK_BREAD] Wow! Yummy bread! Do you like bread?[STUDENT_TALK]",
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

        # R4: finish line placement
        if finish_line in r and "[TEMPLATE_FINISH]" not in r:
            v("finish-line-leak", f"reply {n}: finish/handover line without [TEMPLATE_FINISH]")
        if finish_line in r and strip_tags(r).strip().startswith(strip_tags(finish_line).strip()[:20]):
            v("warm-sentence-first", f"reply {n}: finish turn starts with the handover line (no warm sentence first)")

        # R5: TEMPLATE_FINISH position (only reply 3+)
        if "[TEMPLATE_FINISH]" in r and n <= 2:
            v("early-finish", f"reply {n}: [TEMPLATE_FINISH] before reply 3")
        if "[TEMPLATE_FINISH]" in r and finish_line not in r:
            v("finish-without-line", f"reply {n}: [TEMPLATE_FINISH] without the verbatim finish/handover line")

        # R6: opener rules
        if n == 1 and strip_tags(r).strip() != strip_tags(opener).strip():
            v("opener-verbatim", f"reply 1 is not the fixed opener")
        if n > 1 and strip_tags(opener).strip()[:25].lower() in strip_tags(r).lower():
            v("opener-repeat", f"reply {n}: repeats the fixed opener")

        # R7: STUDENT_TALK replies must end with the child's job (question or say-it call)
        if "[STUDENT_TALK]" in r:
            body = strip_tags(r).strip()
            last = re.split(r"(?<=[.!?])\s+", body)[-1] if body else ""
            is_question = last.endswith("?")
            is_say_call = re.search(rf"\b(say|copy|together|your turn|repeat)\b", last, re.I) or word in last.lower()
            if not (is_question or is_say_call):
                v("child-job", f"reply {n}: STUDENT_TALK turn ends on a plain statement: ...{last[-60:]!r}")

        # R8: TTS safety — no naked single letters as sentences, no ellipses (TTS reads "..." badly)
        for s in re.split(r"[.!?]+", strip_tags(r)):
            if re.fullmatch(r"\s*[A-Za-z]\s*", s or ""):
                v("tts-naked-letter", f"reply {n}: single letter as its own sentence")
        if "..." in r or "\u2026" in r:
            v("tts-ellipsis", f"reply {n}: contains '...' — the voice engine renders it badly")

    # R9: no repeated sentences across the page
    seen = {}
    for i, r in enumerate(replies):
        for s in sentences(r):
            if s in seen:
                v("no-repeat", f"reply {i+1} repeats a sentence from reply {seen[s]+1}: {s[:60]!r}")
            else:
                seen[s] = i

    # R10: last reply must finish the page
    if replies and "[TEMPLATE_FINISH]" not in replies[-1]:
        v("must-finish", "last assistant reply does not end the page with [TEMPLATE_FINISH] (transcript may be cut early — verify)")

    # R11: false celebration — "Yes!"-style cheer in a finish turn requires a word-try in any prior user msg
    user_texts = " ".join(m["text"].lower() for m in msgs if m["role"] == "user")
    said_word = word in user_texts  # generous variants need the LLM judge; exact match is the mechanical floor
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
