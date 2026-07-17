#!/usr/bin/env python3
"""Mechanical checker for Lead-in transcripts (pre-video / post-video steps).

Usage: python3 checker_leadin.py transcript.json [...]
Transcript JSON: {"family":"leadin","step":"pre_video"|"post_video",
                  "student_name":"...", "case":"...", "messages":[{role,text}...]}
Exit 0 = clean, 1 = violations found.
"""
import json
import re
import sys
import unicodedata

ASK_LINE = "Oh no! The cake! Where is the cake?"
POS_LINE = ("Yes! The cake is GONE! Look! This is Mouse! Mouse wants to help us! "
            "Let's go find that cake")
NEG_LINE = ("The cake is gone! Oh no! Look! This is Mouse! "
            "Mouse wants to help us! Let's go find that cake")
SOFT_CATCH_MAX = 6  # words allowed before the NEG line for an upset child
PRE_LINE = ("look! This is Farmer Bob! Today is Farmer Bob's birthday! "
            "A big big party! On the farm! Let's go! Come on!")
POSITIVE_SIGNALS = ["gone", "missing", "lost", "not here", "no cake", "can't see",
                    "cant see", "disappear", "不见", "没有了", "没了"]
CULPRIT = "horse"

# --- L3/L4 demo lesson (Dino & Mia meet unicorns) ---
# pre-video HAS teaser questions by design (answered by the video, never waited on).
PRE_LINE_L3 = ("look! dino and mia are ready for an adventure! where will they go? "
               "what will happen to them? let's watch and find out!")
ASK_L3 = ("look! unicorns! dino and mia meet some unicorns! "
          "what fun will they have together?")
LAUNCH_L3 = "let's watch and find out!"
IDK_SIGNALS = ["don't know", "dont know", "不知道", "no sé", "no se"]

# --- L5 lesson (Mike arrives in Tomorrow Town, meets Zoe; ages 11-12, A2+) ---
# Same 2-reply shape as L3; the catch budget is wider (preteens give real
# predictions worth echoing) and "Good guess!" joins "Good idea!" as fake
# praise after silence/IDK (the original script said it to EVERY answer).
PRE_LINE_L5 = ("look! mike is in tomorrow town. he has just arrived. what will he see? "
               "what will happen next? let's watch and find out!")
ASK_L5 = ("look! mike meets zoe in tomorrow town. tomorrow town has many robots. "
          "zoe wants to show mike around. what robots do you think mike will see?")
LAUNCH_L5 = "let's see what zoe shows mike first!"

# --- Festival: 足球课 World Cup special (ages 4-6, pre-A1) ---
# pre-video is a fixed no-question hype line; post-video is ONE reply
# (feel + hook + go), never waits, never asks.
PRE_LINE_SOCCER = ("look! soccer time! it's the world cup! "
                   "a big big soccer party! let's watch! come on!")
# Device bug #360001: "Tiny bugs team up! The big match is on! Goal or no goal!"
# — sports-announcer talk a pre-A1 child cannot picture. Words must be tiny
# and the launch must put the CHILD in the game.
ANNOUNCER_TALK = [r"team\s+up", r"match\s+is\s+on", r"goal\s+or\s+no\s+goal",
                  r"we\s+will\s+see", r"\bmatch\b", r"\bversus\b", r"\bcompete\b",
                  r"kick[\s-]?off\b", r"\bchampionship\b"]


def has_cjk(t):
    return any(unicodedata.category(c) == "Lo" and "CJK" in unicodedata.name(c, "") for c in t)


def strip_tags(t):
    return re.sub(r"\[[A-Z_]+\]", "", t)


def norm(t):
    return re.sub(r"\s+", " ", strip_tags(t)).strip().lower()


def control_tags(t):
    return re.findall(r"\[(?:STUDENT_TALK|TEMPLATE_FINISH|NEXT_STEP|WORD_EVALUATION|TEACHER_TALK)\]", t)


def check(path):
    tr = json.loads(open(path, encoding="utf-8").read())
    msgs = tr["messages"]
    step = tr.get("step", "post_video")
    replies = [m["text"] for m in msgs if m["role"] == "assistant"]
    users = [m["text"] for m in msgs if m["role"] == "user"]
    out = []
    v = lambda rule, msg: out.append(f"[{rule}] {msg}")

    for n, r in enumerate(replies, 1):
        tags = control_tags(r)
        if len(tags) != 1:
            v("one-tag", f"reply {n}: {len(tags)} control tags (need exactly 1)")
        if tags and not r.rstrip().endswith(tags[-1]):
            v("tag-last", f"reply {n}: text after the control tag")
        if has_cjk(r):
            v("english-only", f"reply {n}: contains non-English characters")
        if "..." in r or "…" in r or re.search(r"\w\s*[-–—]\s*\w", strip_tags(r)):
            v("tts-safety", f"reply {n}: ellipsis or dash (voice engine breaks)")
        for m in re.finditer(r"[A-Za-z]*([A-Za-z])\1{2,}[A-Za-z]*", strip_tags(r)):
            v("tts-stretched", f"reply {n}: stretched spelling {m.group(0)!r} (voice engine cannot say it)")
        for m in re.finditer(r"\b(hee[\s-]?hee|tee[\s-]?hee|hehe)\b", strip_tags(r), re.I):
            v("tts-giggle", f"reply {n}: giggle spelling {m.group(0)!r} (voice engine breaks; use 'Ha ha!')")
        for pat in tr.get("forbid_phrases", []):
            if re.search(pat, strip_tags(r), re.I):
                v("forbid-phrase", f"reply {n}: contains forbidden phrase {pat!r}")

    for pat in tr.get("require_phrases", []):
        if not any(re.search(pat, strip_tags(r), re.I) for r in replies):
            v("require-phrase", f"no reply contains required phrase {pat!r}")

    family = tr.get("family", "leadin_l2")

    if step == "pre_video":
        if len(replies) != 1:
            v("one-turn", f"pre-video must be exactly 1 reply, got {len(replies)}")
        if replies:
            r = replies[0]
            if "[NEXT_STEP]" not in r:
                v("next-step", "pre-video reply does not end with [NEXT_STEP] (video never starts)")
            if "[STUDENT_TALK]" in r:
                v("no-wait", "pre-video must never wait for the child")
            if family == "leadin_l3":
                if PRE_LINE_L3 not in norm(r):
                    v("script", f"pre-video reply deviates from the fixed script: {strip_tags(r).strip()!r}")
            elif family == "leadin_l5":
                if PRE_LINE_L5 not in norm(r):
                    v("script", f"pre-video reply deviates from the fixed script: {strip_tags(r).strip()!r}")
            elif family == "leadin_l1_soccer":
                if PRE_LINE_SOCCER not in norm(r):
                    v("script", f"pre-video reply deviates from the fixed script: {strip_tags(r).strip()!r}")
                if "?" in strip_tags(r):
                    v("no-question", "pre-video must not ask anything")
            else:
                if PRE_LINE.lower() not in norm(r):
                    v("script", f"pre-video reply deviates from the fixed script: {strip_tags(r).strip()!r}")
                if "?" in strip_tags(r):
                    v("no-question", "pre-video must not ask anything")
        return out

    if family == "leadin_l3":
        return check_post_l3(tr, replies, users, v, out)
    if family == "leadin_l5":
        return check_post_l3(tr, replies, users, v, out,
                             ask=ASK_L5, launch=LAUNCH_L5,
                             praise=r"good\s+(idea|guess)", catch_max=SOFT_CATCH_MAX + 4)
    if family == "leadin_l1_soccer":
        return check_post_soccer(tr, replies, users, v, out)

    # post_video: exactly 2 replies (ASK -> confirm+launch), no ready-wait
    if len(replies) != 2:
        v("two-replies", f"post-video must be exactly 2 replies, got {len(replies)}")

    if replies:
        if norm(replies[0]) != ASK_LINE.lower():
            v("script-ask", f"reply 1 is not the ASK line: {strip_tags(replies[0]).strip()!r}")
        if "[STUDENT_TALK]" not in replies[0]:
            v("tag-ask", "reply 1 must wait with [STUDENT_TALK]")

    if len(replies) >= 2:
        r2, n2 = replies[1], norm(replies[1])
        is_pos = n2.startswith(norm(POS_LINE))
        neg_at = n2.find(norm(NEG_LINE))
        is_neg = neg_at >= 0
        if not (is_pos or is_neg):
            v("script-row2", f"reply 2 matches neither POS nor NEG script line: {strip_tags(r2).strip()!r}")
        if is_neg and neg_at > 0:
            catch = n2[:neg_at].strip()
            if len(catch.split()) > SOFT_CATCH_MAX:
                v("catch-budget", f"reply 2 soft catch over budget ({len(catch.split())} words): {catch!r}")
        if "[TEMPLATE_FINISH]" not in r2:
            v("must-finish", "reply 2 does not end the step with [TEMPLATE_FINISH]")
        if "?" in strip_tags(r2):
            v("no-question-finish", "reply 2 asks a question ('are you ready?' wait was cut); it must launch and end")
        # classification: POS row only if the child's first answer carried a positive signal
        first = users[1].lower() if len(users) > 1 else ""  # users[0] is the UI-ready message
        if not first.startswith("the student has been silent"):
            hit = any(s in first for s in POSITIVE_SIGNALS)
            if is_pos and not hit:
                v("row2-classify", f"reply 2 took POS row but child answer had no 'gone' signal: {first!r}")
        elif is_pos:
            v("row2-classify", "reply 2 took POS row on silence")

    # spoiler guard: the culprit's name must never be spoken by the teacher
    for n, r in enumerate(replies, 1):
        if re.search(rf"\b{CULPRIT}\b", r, re.I):
            v("spoiler", f"reply {n}: teacher says the culprit ({CULPRIT!r})")

    return out


def check_post_soccer(tr, replies, users, v, out):
    """足球课 post-video: ONE reply (feel + hook + go), no waits, no questions."""
    if len(replies) != 1:
        v("one-reply", f"post-video must be exactly 1 reply, got {len(replies)}")
    if replies:
        r = replies[0]
        body = strip_tags(r)
        if "[TEMPLATE_FINISH]" not in r:
            v("must-finish", "the reply does not end the lead-in with [TEMPLATE_FINISH]")
        if "[STUDENT_TALK]" in r or "[NEXT_STEP]" in r:
            v("no-wait", "post-video must never wait or start another video")
        if "?" in body:
            v("no-question", f"post-video asks a question nobody waits for: {body.strip()!r}")
        sents = [s for s in re.split(r"(?<=[.!])\s+", body.strip()) if s.strip()]
        if len(sents) > 8:
            v("size", f"reply has {len(sents)} bursts (max 6 tiny ones + slack)")
        long = [s for s in sents if len(s.split()) > 9]
        if long:
            v("size", f"sentence over the tiny-kid budget: {long[0]!r}")
        for pat in [r"\bmeans\b", r"say\s+it\s+with\s+me", r"can\s+you\s+say", r"repeat\s+after"]:
            if re.search(pat, body, re.I):
                v("no-teaching", f"lead-in is teaching ({pat!r})")
        for pat in ANNOUNCER_TALK:
            if re.search(pat, body, re.I):
                v("kid-words", f"announcer talk a pre-A1 child cannot picture ({pat!r}): {body.strip()!r}")
        if not re.search(r"\b(we|you|let's|let us)\b", body, re.I):
            v("personal", f"the reply never puts the child in the game (no we/you/let's): {body.strip()!r}")
    return out


def check_post_l3(tr, replies, users, v, out,
                  ask=ASK_L3, launch=LAUNCH_L3,
                  praise=r"good\s+idea", catch_max=SOFT_CATCH_MAX + 2):
    """L3/L4 and L5 post-video: reveal-ASK -> matched catch + fixed launch (2 replies)."""
    if len(replies) != 2:
        v("two-replies", f"post-video must be exactly 2 replies, got {len(replies)}")

    if replies:
        n1 = norm(replies[0])
        if not n1.endswith(ask):
            v("script-ask", f"reply 1 is not the ASK line: {strip_tags(replies[0]).strip()!r}")
        if "[STUDENT_TALK]" not in replies[0]:
            v("tag-ask", "reply 1 must wait with [STUDENT_TALK]")

    if len(replies) >= 2:
        r2, n2 = replies[1], norm(replies[1])
        if "[TEMPLATE_FINISH]" not in r2:
            v("must-finish", "reply 2 does not end the step with [TEMPLATE_FINISH]")
        launch_at = n2.find(launch)
        if launch_at < 0:
            v("script-launch", f"reply 2 is missing the launch line: {strip_tags(r2).strip()!r}")
        else:
            catch = n2[:launch_at].strip()
            if len(catch.split()) > catch_max:
                v("catch-budget", f"reply 2 catch over budget ({len(catch.split())} words): {catch!r}")
            after = n2[launch_at + len(launch):].strip()
            if after:
                v("script-launch", f"reply 2 has text after the launch line: {after!r}")
            # ONE short rhetorical echo ("Fly together? Maybe!") is human;
            # anything more is a fake ask the teacher never waits for.
            qs = [s for s in re.split(r"(?<=[?])\s+", catch) if s.endswith("?")]
            if len(qs) > 1 or any(len(q.rstrip("?").split()) > 5 for q in qs):
                v("no-question-finish", f"reply 2 catch asks a real question: {catch!r}")
        first = users[1].lower() if len(users) > 1 else ""  # users[0] is the UI-ready message
        silent = first.startswith("the student has been silent")
        idk = any(s in first for s in IDK_SIGNALS)
        if (silent or idk) and re.search(praise, n2):
            v("fake-praise", "reply 2 gives praise but the student gave no idea (silence / 'I don't know')")
        if silent and launch_at > 0:
            v("catch-on-silence", f"reply 2 puts a catch before the launch on a silent child: {n2[:launch_at].strip()!r}")

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
