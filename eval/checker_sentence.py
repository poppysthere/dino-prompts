#!/usr/bin/env python3
"""Mechanical checker for L2 sentence-teaching steps (Mouse's bags).

Steps: intro (1 fixed reply) -> sentence_0 cow -> sentence_1 cat ->
sentence_2 horse + big question -> reveal (1 fixed reply after video).
Transcript JSON: {"family":"sent_*","case":"...","student_name":"...",
                  "messages":[{role,text}...], "max_replies":N,
                  "forbid_phrases":[...], "require_phrases":[...], "reply_forbid":{"2":[...]}}
Exit 0 = clean, 1 = violations found.
"""
import json
import re
import sys
import unicodedata

FAMILIES = {
    "sent_intro": {
        "single": True,
        "end_tag": "[NEXT_STEP]",
        "close": "One two three bags! Ooh, what's inside? Let's find out!",
    },
    "sent_cow": {
        "ask": "Mouse found a bell! A bell! And look! It's a cow! Say it with me. It's a cow!",
        "retry": "Let's say it together. It's a cow!",
        "end_tag": "[NEXT_STEP]",
    },
    "sent_cat": {
        "ask": "Mouse found a fish! A fish! And look! It's a cat! Say it with me. It's a cat!",
        "retry": "Let's say it together. It's a cat!",
        "end_tag": "[NEXT_STEP]",
    },
    "sent_horse": {
        "ask": "Mouse found something! And look! It's a horse! Say it with me. It's a horse!",
        "retry": "Let's say it together. It's a horse!",
        "end_tag": "[NEXT_STEP]",
        "close": "Let's watch the video and find out!",
        "wonder": "who ate the cake",
        "spoiler": r"\bhorse ate\b",
    },
    "sent_reveal": {
        "single": True,
        "end_tag": "[TEMPLATE_FINISH]",
        "close": "THE HORSE! The horse ate the cake!",
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
    fam = FAMILIES[tr["family"]]
    replies = [m["text"] for m in tr["messages"] if m["role"] == "assistant"]
    out = []
    v = lambda rule, msg: out.append(f"[{rule}] {msg}")

    for n, r in enumerate(replies, 1):
        body = strip_tags(r)
        if "[WORD_EVALUATION]" in r:
            v("no-word-eval", f"reply {n}: [WORD_EVALUATION] is banned on sentence pages")
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
        if fam.get("spoiler") and re.search(fam["spoiler"], body, re.I):
            v("spoiler", f"reply {n}: culprit leak (matched {fam['spoiler']!r})")
        if r.rstrip().endswith("[STUDENT_TALK]") and not r.rstrip().endswith("[TEACHER_LISTEN][STUDENT_TALK]"):
            v("listen-pose", f"reply {n}: wait without the listening pose")
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

    if fam.get("single") and len(replies) != 1:
        v("single-reply", f"this step is ONE reply, got {len(replies)}")

    if fam.get("ask") and norm(fam["ask"]) not in norm(replies[0]):
        v("script-ask", f"reply 1 deviates from the ASK line: {strip_tags(replies[0]).strip()!r}")

    n_max = tr.get("max_replies") or (1 if fam.get("single") else 4)
    if len(replies) > n_max:
        v("too-long", f"{len(replies)} replies (max {n_max} for this case)")

    if fam.get("retry"):
        retries = sum(1 for r in replies if norm(fam["retry"]) in norm(r))
        if retries > 1:
            v("retry-once", f"the retry call appears {retries} times (max 1, ever)")

    if fam.get("wonder"):
        wonders = sum(1 for r in replies if fam["wonder"] in norm(r))
        if wonders == 0:
            v("wonder-missing", "the big question never happens")
        elif wonders > 1:
            v("wonder-loop", f"the big question asked {wonders} times")

    last = replies[-1]
    if fam["end_tag"] not in last:
        v("must-end", f"last reply does not end the step with {fam['end_tag']}")
    if fam.get("close") and norm(fam["close"]) not in norm(last):
        v("close-line", f"last reply missing the fixed close: {strip_tags(last).strip()!r}")
    for r in replies[:-1]:
        if fam["end_tag"] in r or "[TEMPLATE_FINISH]" in r:
            v("early-end", "a reply before the last one ends the step")

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
