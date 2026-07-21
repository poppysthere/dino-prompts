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

# --- Trial: 新手引导体验课 demo lesson (Fox's birthday party; ages 4-6, pre-A1) ---
# pre-video REPLACES the warm-up (hi + one tiny question + launch, 2 replies);
# post-video is a 3-reply shadow-guessing chat. The visitor (hedgehog) is a
# SECRET the teacher must never say — the lesson reveals it later.
LAUNCH_TRIAL_PRE = "look! a party! cake and balloons! let's watch! come on!"
# B1 ends with a fed menu: a pre-A1 child cannot answer a bare "who?" —
# "A cat? A dog?" hands them words to echo (device bug #367710: "什么？"
# got the whole line repeated verbatim instead of help). Tail check plus
# every load-bearing sentence present ("Someone is at the door!" gets
# dropped by models, so it is checked separately).
ASK1_TRIAL = "a shadow! who is it? a cat? a dog? guess!"
ASK1_TRIAL_PARTS = ("ding dong", "someone is at the door", "a shadow")
ASK2_TRIAL = "hmm! is it big, or small?"
CLOSE_TRIAL = "let's find out! come on!"
# The secret visitor: the teacher may say it ONLY as a recast of the child's
# own guess (刺猬！ -> "A hedgehog? Ooh! Maybe!" — kid-centered recast doctrine),
# never first, and never confirmed/denied.
SPOILER_TRIAL = "hedgehog"
SPOILER_TRIAL_L1 = "刺猬"

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
    t = t.replace("\u2019", "'").replace("\u2018", "'")  # curly apostrophes break script matching
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
        # "Ta-da!" is in the common layer's own toolbox; hyphenated
        # interjections are single TTS-safe words, not pause-breaking dashes.
        dashable = re.sub(r"\b(ta-da|ding-dong|high-five)\b", "x", strip_tags(r), flags=re.I)
        if "..." in r or "…" in r or re.search(r"\w\s*[-–—]\s*\w", dashable):
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

    if family == "leadin_trial" and step == "pre_video":
        return check_pre_trial(tr, replies, users, v, out)

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
    if family == "leadin_trial":
        return check_post_trial(tr, replies, users, v, out)

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


def check_pre_trial(tr, replies, users, v, out):
    """Trial demo pre-video: B1 hello only (small win) -> B2 celebrate + one tiny
    question, or the fed line for a lost/silent child -> B3 catch + fixed launch."""
    if len(replies) != 3:
        v("three-replies", f"trial pre-video must be exactly 3 replies, got {len(replies)}")
    if replies:
        r1, b1 = replies[0], strip_tags(replies[0])
        if "[STUDENT_TALK]" not in r1:
            v("tag-b1", "reply 1 must wait with [STUDENT_TALK]")
        if "?" in b1:
            v("hello-only", f"reply 1 is the hello ONLY — the small win — no question yet: {b1.strip()!r}")
        if re.search(r"your\s+name|你叫什么", b1, re.I):
            v("no-name-ask", "the demo never asks the child's name")
    # The greeting/self-intro lives in reply 1 ONLY (device bug #368067-75:
    # "Hi hi Tommy! I'm Max!" re-said verbatim after the child said hi).
    for n, r in enumerate(replies[1:], 2):
        if re.search(r"\bI'?m\s+[A-Z][a-z]+\b|\bhi\s+hi\b|\bhello\s+hello\b", strip_tags(r)):
            v("dead-greeting", f"reply {n}: re-greets or re-introduces — the greeting exists once, in reply 1 only: {strip_tags(r).strip()!r}")
    if len(replies) >= 2:
        r2, b2 = replies[1], strip_tags(replies[1])
        if "[STUDENT_TALK]" not in r2:
            v("tag-b2", "reply 2 must wait with [STUDENT_TALK]")
        if b2.count("?") > 1:
            v("one-question", f"reply 2 asks more than one question: {b2.strip()!r}")
        second = users[1].lower() if len(users) > 1 else ""
        if second.startswith("the student has been silent") and "you can say" not in b2.lower():
            v("feed-on-silence", f"a silent child gets the fed line ('You can say, hi ...'), got: {b2.strip()!r}")
    if len(replies) >= 3:
        r3, n3 = replies[2], norm(replies[2])
        if "[NEXT_STEP]" not in r3:
            v("next-step", "reply 3 does not start the video with [NEXT_STEP] (class stuck)")
        if "[STUDENT_TALK]" in r3:
            v("no-wait", "reply 3 must launch, never wait again")
        at = n3.find(LAUNCH_TRIAL_PRE)
        if at < 0:
            v("script-launch", f"reply 3 is missing the fixed launch: {strip_tags(r3).strip()!r}")
        else:
            catch = n3[:at].strip()
            if len(catch.split()) > 8:
                v("catch-budget", f"reply 3 catch over budget ({len(catch.split())} words): {catch!r}")
            if n3[at + len(LAUNCH_TRIAL_PRE):].strip():
                v("script-launch", "reply 3 has text after the launch line")
            qs = [s for s in re.split(r"(?<=[?])\s+", catch) if s.endswith("?")]
            if len(qs) > 1 or any(len(q.rstrip("?").split()) > 3 for q in qs):
                v("no-question-launch", f"reply 3 catch asks a real question: {catch!r}")
            last = users[2].lower() if len(users) > 2 else ""
            if last.startswith("the student has been silent") and catch:
                v("catch-on-silence", f"reply 3 puts a catch before the launch on a silent child: {catch!r}")
    # Nothing said twice (same law as the post-video page).
    seen_sents = {}
    for n, r in enumerate(replies, 1):
        for s in re.split(r"(?<=[.!?])\s+", strip_tags(r).strip()):
            ns = re.sub(r"[^a-z' ]", "", s.lower()).strip()
            if len(ns.split()) < 3:
                continue
            if ns in seen_sents and seen_sents[ns] != n:
                v("sentence-repeat", f"reply {n}: repeats {s.strip()!r} (first said in reply {seen_sents[ns]})")
            seen_sents.setdefault(ns, n)
    return out


def check_post_trial(tr, replies, users, v, out):
    """Trial demo post-video: shadow chat — ASK1 who -> catch + ASK2 big/small -> catch + close."""
    if len(replies) != 3:
        v("three-replies", f"trial post-video must be exactly 3 replies, got {len(replies)}")
    child_guessed_secret = False
    for m in tr["messages"]:
        if m["role"] == "user":
            if SPOILER_TRIAL_L1 in m["text"] or re.search(rf"\b{SPOILER_TRIAL}\b", m["text"], re.I):
                child_guessed_secret = True
        elif re.search(rf"\b{SPOILER_TRIAL}\b", m["text"], re.I) and not child_guessed_secret:
            v("spoiler", f"teacher says the secret visitor FIRST (child never guessed it): {strip_tags(m['text']).strip()!r}")
    # Say-nothing-twice law (device bug #367711: the who-line repeated verbatim
    # to a confused child, then "A mystery! Ooh!" twice): no sentence of 3+
    # words appears in two different replies.
    seen_sents = {}
    for n, r in enumerate(replies, 1):
        for s in re.split(r"(?<=[.!?])\s+", strip_tags(r).strip()):
            ns = re.sub(r"[^a-z' ]", "", s.lower()).strip()
            if len(ns.split()) < 3:
                continue
            if ns in seen_sents and seen_sents[ns] != n:
                v("sentence-repeat", f"reply {n}: repeats {s.strip()!r} (first said in reply {seen_sents[ns]})")
            seen_sents.setdefault(ns, n)
    # The who-line lives in reply 1 ONLY (device bug: it was re-said word for
    # word to a confused child instead of helping). "Ding dong" / "who is it"
    # anywhere later = the robot bug, even partially.
    for n, r in enumerate(replies[1:], 2):
        if re.search(r"ding\s+dong|who is it|someone is at the door", strip_tags(r), re.I):
            v("dead-line-repeat", f"reply {n}: brings back the who-line ('Ding dong' / 'Who is it') — it exists once, in reply 1 only: {strip_tags(r).strip()!r}")
    for n, r in enumerate(replies, 1):
        if re.search(rf"(yes|yeah|right|correct)[^a-z]{{0,4}}[^.!?]*\b{SPOILER_TRIAL}\b|it('s| is) (a |the )?{SPOILER_TRIAL}", strip_tags(r), re.I):
            v("spoiler-confirm", f"reply {n}: confirms the secret visitor: {strip_tags(r).strip()!r}")
        if re.search(r"good\s+(guess|job|idea)", strip_tags(r), re.I):
            v("fake-praise", f"reply {n}: empty praise instead of playing with the child's word")
        if re.search(r"\bno[,.!]?\s+(it('s| is)?\s+)?not\b", strip_tags(r), re.I):
            v("no-deny", f"reply {n}: denies a guess (the teacher does not know who it is)")
    if replies:
        n1 = norm(replies[0])
        if not n1.endswith(ASK1_TRIAL):
            v("script-ask1", f"reply 1 does not end with the who-is-it line: {strip_tags(replies[0]).strip()!r}")
        for part in ASK1_TRIAL_PARTS:
            if part not in n1:
                v("script-ask1-drop", f"reply 1 dropped {part!r} from the B1 script (real test bug)")
        if "[STUDENT_TALK]" not in replies[0]:
            v("tag-ask1", "reply 1 must wait with [STUDENT_TALK]")
    if len(replies) >= 2:
        n2 = norm(replies[1])
        if not n2.endswith(ASK2_TRIAL):
            v("script-ask2", f"reply 2 does not end with the big-or-small line: {strip_tags(replies[1]).strip()!r}")
        else:
            catch = n2[: n2.rfind(ASK2_TRIAL)].strip()
            if len(catch.split()) > 10:
                v("catch-budget", f"reply 2 catch over budget ({len(catch.split())} words): {catch!r}")
            first = users[1].lower() if len(users) > 1 else ""
            if first.startswith("the student has been silent") and catch:
                v("catch-on-silence", f"reply 2 puts a catch before the ask on a silent child: {catch!r}")
            elif first and not first.startswith("the student has been silent") and not catch:
                v("missing-catch", "reply 2 ignores the child's answer — no catch before the ask (real test bug: 'Mommy!' got no echo)")
        if "[STUDENT_TALK]" not in replies[1]:
            v("tag-ask2", "reply 2 must wait with [STUDENT_TALK]")
    if len(replies) >= 3:
        r3, n3 = replies[2], norm(replies[2])
        if "[TEMPLATE_FINISH]" not in r3:
            v("must-finish", "reply 3 does not end the lead-in with [TEMPLATE_FINISH]")
        at = n3.find(CLOSE_TRIAL)
        if at < 0:
            v("script-close", f"reply 3 is missing the close line: {strip_tags(r3).strip()!r}")
        else:
            catch = n3[:at].strip()
            if len(catch.split()) > 10:
                v("catch-budget", f"reply 3 catch over budget ({len(catch.split())} words): {catch!r}")
            if n3[at + len(CLOSE_TRIAL):].strip():
                v("script-close", "reply 3 has text after the close line")
            # template allows a 3-word echo max at the close — a longer question
            # shape here is a re-asked dead question ("is it big, or small?")
            qs = [s for s in re.split(r"(?<=[?])\s+", catch) if s.endswith("?")]
            if len(qs) > 1 or any(len(q.rstrip("?").split()) > 3 for q in qs):
                v("no-question-finish", f"reply 3 catch asks a real question: {catch!r}")
            second = users[2].lower() if len(users) > 2 else ""
            if second.startswith("the student has been silent") and catch:
                v("catch-on-silence", f"reply 3 puts a catch before the close on a silent child: {catch!r}")
            elif second and not second.startswith("the student has been silent") and not catch:
                v("missing-catch", "reply 3 ignores the child's answer — no catch before the close")
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
