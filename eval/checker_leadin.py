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
START_L3_V2 = ("today, let's learn three new words. climb. jump. fly. first, watch. "
               "then, say the words. look! dino and mia are here. let's watch!")
RESCUE_L3_V2 = "listen first. hi! now, you try."
GREETING_L3_RE = re.compile(
    r"\b(hi|hello|hey|good morning|good afternoon|good evening|nice to meet you)\b"
    r"|你好|哈喽",
    re.I,
)
ASK_L3 = ("look! unicorns! dino and mia meet some unicorns! "
          "what fun will they have together?")
ASK_L3_V2 = ("look! unicorns! dino and mia meet some unicorns. "
             "can they fly together?")
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
CLOSE_TRIAL = "let's open the door! come on!"
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


def unquirk(t):
    return t.replace("\u2019", "'").replace("\u2018", "'")  # curly apostrophes break phrase matching


def norm(t):
    return re.sub(r"\s+", " ", strip_tags(unquirk(t))).strip().lower()


def control_tags(t):
    return re.findall(r"\[(?:STUDENT_TALK|TEMPLATE_FINISH|NEXT_STEP|WORD_EVALUATION|TEACHER_TALK)\]", t)


def turn_before(msgs, n):
    """Text of the user message right before the nth (1-based) assistant reply.

    Replaces plain users[i] indexing, which silently went off-by-one whenever a
    runner kept or dropped the UI-ready line, or a case seeded user history —
    the silence/catch checks were reading the WRONG child turn (found in the
    second-round retest: an opt-out at B2 was read from the wrong slot)."""
    seen = 0
    for i, m in enumerate(msgs):
        if m["role"] == "assistant":
            seen += 1
            if seen == n:
                return msgs[i - 1]["text"] if i and msgs[i - 1]["role"] == "user" else ""
    return ""


def is_client_silence(t):
    """The client's explicit silence message — a catch here comforts nobody
    about nothing, so catches are FORBIDDEN."""
    return t.strip().lower().startswith("the student has been silent")


def is_silent(t):
    """No words a catch could answer: the client silence message OR a
    contentless turn ("...", a whimper). A catch is not REQUIRED here —
    but a tiny one on a contentless turn is fine (only is_client_silence
    forbids it)."""
    t = t.strip()
    return is_client_silence(t) or not re.search(r"[\w\u4e00-\u9fff]", t)


SILENCE_HOOK_BAD = re.compile(
    r"it'?s okay|that'?s okay|\bokay\b|good job|great|well done|me too|don'?t worry", re.I)


def silence_catch_issue(catch):
    """A client-silence turn has no words to answer, so a real CATCH is
    forbidden — but a tiny attention call (the child's name + one playful
    sound: 'Lily! Peek-a-boo!') is a pro-tutor move and welcome (user
    doctrine: grab a silent child's attention, never just roll on). Bad =
    comfort or praise aimed at nobody, or anything longer than a call."""
    if not catch:
        return None
    if SILENCE_HOOK_BAD.search(catch):
        return f"comforts or praises nobody: {catch!r}"
    if len(catch.split()) > 5:
        return f"a whole catch at a silent child: {catch!r}"
    return None


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
        dashable = re.sub(r"\b(ta-da|ding-dong|high-five|bye-bye|peek-a-boo|so-so)\b", "x", strip_tags(r), flags=re.I)
        if "..." in r or "…" in r or re.search(r"\w\s*[-–—]\s*\w", dashable):
            v("tts-safety", f"reply {n}: ellipsis or dash (voice engine breaks)")
        for m in re.finditer(r"[A-Za-z]*([A-Za-z])\1{2,}[A-Za-z]*", strip_tags(r)):
            v("tts-stretched", f"reply {n}: stretched spelling {m.group(0)!r} (voice engine cannot say it)")
        for m in re.finditer(r"\b(hee[\s-]?hee|tee[\s-]?hee|hehe)\b", strip_tags(r), re.I):
            v("tts-giggle", f"reply {n}: giggle spelling {m.group(0)!r} (voice engine breaks; use 'Ha ha!')")
        for pat in tr.get("forbid_phrases", []):
            if re.search(pat, unquirk(strip_tags(r)), re.I):
                v("forbid-phrase", f"reply {n}: contains forbidden phrase {pat!r}")

    for pat in tr.get("require_phrases", []):
        if not any(re.search(pat, unquirk(strip_tags(r)), re.I) for r in replies):
            v("require-phrase", f"no reply contains required phrase {pat!r}")

    family = tr.get("family", "leadin_l2")

    if family == "leadin_l3_v2" and step == "pre_video":
        return check_pre_l3_v2(tr, replies, users, v, out)

    if family == "leadin_trial" and step == "pre_video":
        return check_pre_trial(tr, replies, users, v, out)

    if family == "bridge_trial":
        if step == "pre_video":
            return check_pre_bridge(tr, replies, users, v, out)
        return check_post_bridge(tr, replies, users, v, out)

    if family == "wrap_trial":
        return check_pre_wrap(tr, replies, users, v, out)

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
    if family == "leadin_l3_v2":
        return check_post_l3(tr, replies, users, v, out, ask=ASK_L3_V2)
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
        first = turn_before(tr["messages"], 2).lower()
        if not is_silent(first):
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


def check_pre_l3_v2(tr, replies, users, v, out):
    """L3 V2 begins with one hello turn, one optional rescue, then the story."""
    if len(replies) not in (2, 3):
        v("reply-count", f"V2 pre-video must be hello -> [rescue ->] start, got {len(replies)} replies")

    if replies:
        r1, n1 = replies[0], norm(replies[0])
        student = tr.get("student_name", "")
        teacher = tr.get("teacher_name", "")
        if teacher:
            prefix = f"hi, {student}! " if student else "hi! "
            expected = f"{prefix}i'm {teacher}. nice to meet you! say hi to me!".lower()
            if n1 != expected:
                v("script-hello", f"reply 1 is not the tagged-name hello: {strip_tags(r1).strip()!r}")
        if teacher and not re.search(rf"\b{re.escape(teacher)}\b", strip_tags(r1), re.I):
            v("teacher-name", f"reply 1 does not use teacherName {teacher!r}")
        if student and not re.search(rf"\b{re.escape(student)}\b", strip_tags(r1), re.I):
            v("student-name", f"reply 1 drops the usable child name {student!r}")
        if "[TEACHER_LISTEN][STUDENT_TALK]" not in r1.replace(" ", ""):
            v("tag-hello", "reply 1 must wait with [TEACHER_LISTEN][STUDENT_TALK]")
        if "?" in strip_tags(r1) or re.search(r"\bready\b", strip_tags(r1), re.I):
            v("hello-task", "reply 1 must ask only for hi, never ask a ready question")

    first = turn_before(tr["messages"], 2)
    first_is_greeting = bool(GREETING_L3_RE.search(first))
    if len(replies) == 2 and not first_is_greeting:
        v("missing-rescue", f"child did not greet; teacher must rescue once before launch: {first!r}")
    if len(replies) == 3 and first_is_greeting:
        v("extra-rescue", f"child already greeted; teacher should launch on reply 2: {first!r}")

    if len(replies) >= 2 and first_is_greeting:
        catch_reply = norm(replies[1])
        if (re.fullmatch(r"\s*(hi|hello|hey)[!.\s]*", first, re.I)
                and "nice to meet you too" in catch_reply):
            v("unsupported-too", "plain hi was answered as if the child said nice to meet you")
        if (re.search(r"\bnice to meet you\b", first, re.I)
                and "nice to meet you too" not in catch_reply):
            v("missed-social-meaning", "child said nice to meet you, but teacher did not answer it")
        if (re.search(r"\bgood morning\b", first, re.I)
                and "good morning" not in catch_reply):
            v("missed-social-meaning", "child said good morning, but teacher did not match it")
        if ("?" in first and re.search(r"\bcat", first, re.I)
                and not re.search(r"\bcat", catch_reply, re.I)):
            v("ignored-question", "the greeting's cat question was ignored")

    def check_start(reply, number, child):
        n = norm(reply)
        start_at = n.find(START_L3_V2)
        if start_at < 0:
            v("script-start", f"reply {number} is missing the fixed lesson start: {strip_tags(reply).strip()!r}")
            catch = n
        else:
            catch = n[:start_at].strip()
            if n[start_at + len(START_L3_V2):].strip():
                v("script-start", f"reply {number} has spoken text after the fixed lesson start")
        if len(catch.split()) > 6:
            v("catch-budget", f"reply {number} catch over budget ({len(catch.split())} words): {catch!r}")
        if "[NEXT_STEP]" not in reply or "[STUDENT_TALK]" in reply:
            v("must-start", f"reply {number} must start the video with [NEXT_STEP], never wait")
        if "?" in strip_tags(reply) or re.search(r"\bready\b", strip_tags(reply), re.I):
            v("no-question-start", f"reply {number} asks another question instead of starting")
        if re.search(r"\b(action words?|adventure)\b|what happens", n):
            v("a1-vocabulary", f"reply {number} adds language above the A1+ gate: {strip_tags(reply).strip()!r}")
        if is_client_silence(child):
            bad = silence_catch_issue(catch)
            if bad:
                v("catch-on-silence", f"reply {number}, on a silent child, {bad}")

    if len(replies) == 2:
        check_start(replies[1], 2, first)
    elif len(replies) >= 3:
        r2, n2 = replies[1], norm(replies[1])
        rescue_at = n2.find(RESCUE_L3_V2)
        if rescue_at < 0:
            v("script-rescue", f"reply 2 is missing the one rescue: {strip_tags(r2).strip()!r}")
            catch = n2
        else:
            catch = n2[:rescue_at].strip()
            if n2[rescue_at + len(RESCUE_L3_V2):].strip():
                v("script-rescue", "reply 2 has spoken text after the fixed rescue")
        if len(catch.split()) > 6:
            v("catch-budget", f"reply 2 rescue catch over budget ({len(catch.split())} words): {catch!r}")
        if "[TEACHER_LISTEN][STUDENT_TALK]" not in r2.replace(" ", "") or "[NEXT_STEP]" in r2:
            v("rescue-wait", "reply 2 rescue must wait once, not start the video")
        if is_client_silence(first) and catch:
            v("catch-on-silence", f"reply 2 adds a catch to client silence: {catch!r}")
        second = turn_before(tr["messages"], 3)
        check_start(replies[2], 3, second)

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
        # A real <studentName> is always greeted (device bug #372667: name was
        # "yana", the hello had no name). Junk names are pre-blanked by runners.
        name = tr.get("student_name", "")
        if name and not re.search(rf"\b{re.escape(name)}\b", b1, re.I):
            v("greet-name", f"reply 1 drops the real name {name!r}: {b1.strip()!r}")
    # The greeting/self-intro lives in reply 1 ONLY (device bug #368067-75:
    # "Hi hi Tommy! I'm Max!" re-said verbatim after the child said hi; #379014:
    # the same line THREE times while the child said hello twice). Case-blind:
    # "Hi hi" is as dead as "hi hi". "You said hi" (the celebrate row) is fine.
    for n, r in enumerate(replies[1:], 2):
        if (re.search(r"\bI'?m\s+[A-Z][a-z]+\b", strip_tags(r))
                or re.search(r"\b(hi|hello)\s+(hi|hello)\b", strip_tags(r), re.I)):
            v("dead-greeting", f"reply {n}: re-greets or re-introduces — the greeting exists once, in reply 1 only: {strip_tags(r).strip()!r}")
    if len(replies) >= 2:
        r2, b2 = replies[1], strip_tags(replies[1])
        if "[STUDENT_TALK]" not in r2:
            v("tag-b2", "reply 2 must wait with [STUDENT_TALK]")
        if b2.count("?") > 1:
            v("one-question", f"reply 2 asks more than one question: {b2.strip()!r}")
        second = turn_before(tr["messages"], 2).lower()
        if (is_client_silence(second)
                and not re.search(r"repeat after me|you can say", b2, re.I)):
            v("feed-on-silence", f"a silent child gets the fed line ('Repeat after me. Hi ...'), got: {b2.strip()!r}")
    # A fed line must never be a question: "Can you say hi?" bends the melody
    # the child copies (user doctrine, device round #368532+).
    for n, r in enumerate(replies, 1):
        if re.search(r"can\s+you\s+say", strip_tags(r), re.I):
            v("feed-question", f"reply {n}: 'Can you say ...?' — the feed is 'Repeat after me.' plus the words, never a question")
    if len(replies) >= 3:
        r3, n3 = replies[2], norm(replies[2])
        if "[NEXT_STEP]" not in r3:
            v("next-step", "reply 3 does not start the video with [NEXT_STEP] (class stuck)")
        if "[STUDENT_TALK]" in r3:
            v("no-wait", "reply 3 must launch, never wait again")
        # The feed lives in B2 only (device bug #372667: "Repeat after me. Hi
        # Max!" ran as a FOURTH wait, to a child who had already said hello).
        if re.search(r"repeat after me|you can say", strip_tags(r3), re.I):
            v("feed-late", f"reply 3 feeds a line instead of launching: {strip_tags(r3).strip()!r}")
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
            last = turn_before(tr["messages"], 3).lower()
            if is_client_silence(last):
                bad = silence_catch_issue(catch)
                if bad:
                    v("catch-on-silence", f"reply 3, on a silent child, {bad}")
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


BRIDGE_SECRET = "flamingo"
BRIDGE_SECRET_L1 = "火烈鸟"
GOODBYE = r"\bbye\b|bye-bye|see you|next time|wrap up"
# pre-video is the guessing game round two: tease+who (wait) -> catch+tall-or-
# short (wait) -> catch+launch. Same 3-reply shape as the trial lead-in post,
# with a tall/short hint (a flamingo!) instead of big/small.
ASK1_BRIDGE = "who is it this time? guess!"
# "Is it tall, or short?" and the shorter "Tall or short?" are the same
# teaching move — both hand the child two words to grab.
ASK2_BRIDGE_RE = r"(is it )?tall,? or short\?$"
CLOSE_BRIDGE = "let's watch! come on!"


def check_pre_bridge(tr, replies, users, v, out):
    """Trial shadow bridge pre-video: 3 replies — the second-shadow guessing
    game ending in [NEXT_STEP]. The visitor (flamingo) is a secret until the
    video plays: recast-only, never volunteered, never confirmed."""
    if len(replies) != 3:
        v("three-replies", f"bridge pre-video is tease -> hint -> launch (3 replies), got {len(replies)}")
    child_said_secret = any(
        m["role"] == "user" and (BRIDGE_SECRET_L1 in m["text"]
                                 or re.search(rf"\b{BRIDGE_SECRET}\b", m["text"], re.I))
        for m in tr["messages"])
    for n, r in enumerate(replies, 1):
        body = strip_tags(r)
        if re.search(rf"\b{BRIDGE_SECRET}\b", body, re.I) and not child_said_secret:
            v("spoiler", f"reply {n} says the secret visitor before the video: {body.strip()!r}")
        if child_said_secret and re.search(
                rf"(yes|yeah|right|correct)[^.!?]*\b{BRIDGE_SECRET}\b|it('s| is) (a |the )?{BRIDGE_SECRET}",
                body, re.I):
            v("spoiler", f"reply {n} CONFIRMS the secret guess: {body.strip()!r}")
        if re.search(GOODBYE, body, re.I):
            v("not-a-wrapup", f"reply {n} has goodbye words on a bridge page: {body.strip()!r}")
        if n > 1 and re.search(r"who\s+is\s+it", body, re.I):
            v("dead-line-repeat", f"reply {n} re-runs the dead who-ask: {body.strip()!r}")
    if replies:
        n1 = norm(replies[0])
        if not n1.endswith(ASK1_BRIDGE):
            v("script-ask1", f"reply 1 does not end with the who-is-it tease: {strip_tags(replies[0]).strip()!r}")
        if "shadow" not in n1:
            v("tease", f"reply 1 never shows the new shadow: {strip_tags(replies[0]).strip()!r}")
        if "[STUDENT_TALK]" not in replies[0]:
            v("tag-ask1", "reply 1 must give the child the guess turn with [STUDENT_TALK]")
    if len(replies) >= 2:
        n2 = norm(replies[1])
        m2 = re.search(ASK2_BRIDGE_RE, n2)
        if not m2:
            v("script-ask2", f"reply 2 does not end with the tall-or-short hint: {strip_tags(replies[1]).strip()!r}")
        else:
            catch = n2[: m2.start()].strip()
            if len(catch.split()) > 10:
                v("catch-budget", f"reply 2 catch over budget ({len(catch.split())} words): {catch!r}")
            first = turn_before(tr["messages"], 2).lower()
            if is_client_silence(first):
                bad = silence_catch_issue(catch)
                if bad:
                    v("catch-on-silence", f"reply 2, on a silent child, {bad}")
            elif first and not is_silent(first) and not catch:
                v("missing-catch", "reply 2 ignores the child's guess — no catch before the hint ask")
        if "[STUDENT_TALK]" not in replies[1]:
            v("tag-ask2", "reply 2 must wait with [STUDENT_TALK]")
    if len(replies) >= 3:
        r3, n3 = replies[2], norm(replies[2])
        if "[NEXT_STEP]" not in r3:
            v("next-step", "reply 3 does not launch the video with [NEXT_STEP] (class stuck)")
        if "[STUDENT_TALK]" in r3 or "[TEMPLATE_FINISH]" in r3:
            v("no-wait", "reply 3 must launch, not wait or finish")
        at = n3.find(CLOSE_BRIDGE)
        if at < 0:
            v("script-launch", f"reply 3 is missing the launch line: {strip_tags(r3).strip()!r}")
        else:
            catch = n3[:at].strip()
            if len(catch.split()) > 10:
                v("catch-budget", f"reply 3 catch over budget ({len(catch.split())} words): {catch!r}")
            if n3[at + len(CLOSE_BRIDGE):].strip():
                v("script-launch", "reply 3 has text after the launch line")
            qs = [s for s in re.split(r"(?<=[?])\s+", catch) if s.endswith("?")]
            if len(qs) > 1 or any(len(q.rstrip("?").split()) > 3 for q in qs):
                v("no-question-finish", f"reply 3 catch asks a real question: {catch!r}")
        # The dead hint may not return in ANY shape (device bug: "错是什么意思？"
        # got "It is okay. Look. Tall, or short?" as a fourth wait, then "哦。"
        # got "Oh! Tall, or short? Let's watch!" — the ask inside the launch).
        if re.search(r"tall,?\s+or\s+short", strip_tags(r3), re.I):
            v("dead-ask", f"reply 3 re-runs the dead tall-or-short hint: {strip_tags(r3).strip()!r}")
    return out


BRIDGE_SECRET2 = "giraffe"
BRIDGE_SECRET2_L1 = "长颈鹿"


def check_post_bridge(tr, replies, users, v, out):
    """Trial shadow bridge post-video: ONE reply, no interaction (user doctrine)
    — cheer the flamingo reveal, spot the third shadow, PARK it ('But wait! The
    flamingo first!') and hand off. A guess game here would pull the child away
    from the flamingo lesson; the new shadow's game lives on later pages."""
    if len(replies) != 1:
        v("one-reply", f"bridge post-video is ONE cheer reply + [TEMPLATE_FINISH], got {len(replies)}")
    for n, r in enumerate(replies, 1):
        body = strip_tags(r)
        if re.search(rf"\b{BRIDGE_SECRET2}\b", body, re.I):
            v("spoiler", f"reply {n} says the later pages' secret (giraffe): {body.strip()!r}")
        if re.search(GOODBYE, body, re.I):
            v("not-a-wrapup", f"reply {n} has goodbye words on a bridge page: {body.strip()!r}")
        if re.search(r"repeat\s+after\s+me|one\s+more\s+time", body, re.I):
            v("no-teaching", f"reply {n}: say-calls belong to the word page, not the bridge")
        if "?" in body:
            v("no-questions", f"reply {n} asks on a no-interaction page: {body.strip()!r}")
        if re.search(r"you (said it|were right|knew|guessed)|ta-?da", norm(r)):
            v("guess-blind", f"reply {n} judges who guessed ('You said it' / 'Ta-da') — "
                             f"the word page hands out the win, not the bridge")
        if "[STUDENT_TALK]" in r or "[NEXT_STEP]" in r:
            v("no-wait", f"reply {n} waits or starts a video — this page only hands off")
    if replies:
        n1 = norm(replies[0])
        if "[TEMPLATE_FINISH]" not in replies[0]:
            v("must-finish", "the reply does not hand off with [TEMPLATE_FINISH]")
        if "the door opened" not in n1:
            v("script-reveal", f"missing the fixed opener ('The door opened!'): {strip_tags(replies[0]).strip()!r}")
        if not re.search(rf"\b{BRIDGE_SECRET}\b", n1):
            v("reveal", f"the flamingo is never cheered: {strip_tags(replies[0]).strip()!r}")
        if "shadow" not in n1:
            v("script-spot", f"the new shadow is never spotted: {strip_tags(replies[0]).strip()!r}")
        if not re.search(r"(the )?flamingo first|look at her", n1):
            v("script-park", f"the shadow is never parked ('But wait! The flamingo first!'): {strip_tags(replies[0]).strip()!r}")
        if not n1.endswith("come on!"):
            v("script-walk", f"the reply does not end on the walk-over ('Come on!'): {strip_tags(replies[0]).strip()!r}")
            qs = [s for s in re.split(r"(?<=[?])\s+", catch) if s.endswith("?")]
            if len(qs) > 1 or any(len(q.rstrip("?").split()) > 3 for q in qs):
                v("no-question-finish", f"reply 2 catch asks a real question: {catch!r}")
    return out


# Trial wrap-up pre-video: recap cheer + the LAST shadow guess round, then
# [NEXT_STEP] — the giraffe-reveal video ends the class. NO goodbye anywhere:
# the avatar stays and watches the finale WITH the child.
WRAP_ASK = "who is it? guess!"
CLOSE_WRAP_RE = r"let's watch and see! come on!$"


def check_pre_wrap(tr, replies, users, v, out):
    """Trial wrap-up pre-video: 2 replies — recap+remember+who (wait), then
    catch+launch [NEXT_STEP]. The giraffe stays secret: recast-only. No
    goodbye words: the avatar watches the finale with the child."""
    if len(replies) != 2:
        v("two-replies", f"wrap pre-video is recap+ask -> catch+launch (2 replies), got {len(replies)}")
    child_said_secret = any(
        m["role"] == "user" and (BRIDGE_SECRET2_L1 in m["text"]
                                 or re.search(rf"\b{BRIDGE_SECRET2}\b", m["text"], re.I))
        for m in tr["messages"])
    for n, r in enumerate(replies, 1):
        body = strip_tags(r)
        if re.search(rf"\b{BRIDGE_SECRET2}\b", body, re.I) and not child_said_secret:
            v("spoiler", f"reply {n} says the last secret (giraffe) first: {body.strip()!r}")
        if child_said_secret and re.search(
                rf"(yes|yeah|right|correct)[^.!?]*\b{BRIDGE_SECRET2}\b|it('s| is) (a |the )?{BRIDGE_SECRET2}",
                body, re.I):
            v("spoiler", f"reply {n} CONFIRMS the secret guess: {body.strip()!r}")
        if re.search(r"repeat\s+after\s+me|one\s+more\s+time|can\s+you\s+say", body, re.I):
            v("no-teaching", f"reply {n}: say-calls belong to the word pages, not the wrap")
        if re.search(GOODBYE, body, re.I):
            v("no-goodbye", f"reply {n} says goodbye — the avatar watches the finale "
                            f"WITH the child: {body.strip()!r}")
        if n > 1 and re.search(r"who\s+is\s+it", body, re.I):
            v("dead-line-repeat", f"reply {n} re-runs the dead who-ask: {body.strip()!r}")
    if replies:
        r1, n1 = replies[0], norm(replies[0])
        for w in ("hedgehog", "flamingo"):
            if w not in n1:
                v("recap", f"reply 1 recap never cheers the {w}: {strip_tags(r1).strip()!r}")
        if "shadow" not in n1:
            v("tease", f"reply 1 never points at the last shadow: {strip_tags(r1).strip()!r}")
        if not n1.endswith(WRAP_ASK):
            v("script-ask", f"reply 1 does not end with the who-is-it guess call: {strip_tags(r1).strip()!r}")
        if "[STUDENT_TALK]" not in r1:
            v("tag-ask", "reply 1 must give the child the guess turn with [STUDENT_TALK]")
        # the recap is a cheer, not a quiz: only tiny questions allowed
        qs = [s for s in re.split(r"(?<=[.!?])\s+", strip_tags(r1)) if s.strip().endswith("?")]
        if len(qs) > 2 or any(len(q.strip().rstrip("?").split()) > 6 for q in qs):
            v("recap-quiz", f"reply 1 asks too much — remember-ask + who-ask only: {strip_tags(r1).strip()!r}")
    if len(replies) >= 2:
        r2, n2 = replies[1], norm(replies[1])
        if "[NEXT_STEP]" not in r2:
            v("next-step", "reply 2 does not launch the final video with [NEXT_STEP] (class stuck)")
        if "[STUDENT_TALK]" in r2 or "[TEMPLATE_FINISH]" in r2:
            v("no-wait", "reply 2 must launch the video, not wait or finish by tag")
        m2 = re.search(CLOSE_WRAP_RE, n2)
        if not m2:
            v("script-launch", f"reply 2 is missing the launch "
                               f"('Let's watch and see! Come on!'): {strip_tags(r2).strip()!r}")
        else:
            catch = n2[: m2.start()].strip()
            if len(catch.split()) > 10:
                v("catch-budget", f"reply 2 catch over budget ({len(catch.split())} words): {catch!r}")
            first = turn_before(tr["messages"], 2).lower()
            if is_client_silence(first):
                bad = silence_catch_issue(catch)
                if bad:
                    v("catch-on-silence", f"reply 2, on a silent child, {bad}")
            elif first and not is_silent(first) and not catch:
                v("missing-catch", "reply 2 ignores the child's guess — no catch before the launch")
            qs = [s for s in re.split(r"(?<=[?])\s+", catch) if s.endswith("?")]
            if len(qs) > 1 or any(len(q.rstrip("?").split()) > 3 for q in qs):
                v("no-question-finish", f"reply 2 catch asks a real question: {catch!r}")
    # Nothing said twice.
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


# The child's guess-turn answer already carries the size (device bug: "一个
# 小圆的。一个小号。" got "Is it big, or small?" anyway and the child protested
# "I said small."). Conservative shapes only — 小猫/小狗-style animal guesses
# must NOT fire this ("small cat" is a guess, not a size answer).
SIZE_GIVEN = re.compile(
    r"\b(big|small|tiny|little)\b|小小|大大|[小大](的|号|圆)|(很|好|真)[小大]", re.I)


def check_post_trial(tr, replies, users, v, out):
    """Trial demo post-video: shadow chat — ASK1 who -> catch + ASK2 big/small -> catch + close.
    Opt-out at B2 is one shortcut (the ask dies, okay-words + close, 2 replies);
    a guess that already tells the size is the other (the ask is answered
    before it was asked — own the size + close, 2 replies)."""
    first_turn = turn_before(tr["messages"], 2)
    optout = bool(re.search(r"不想说|do(n'?t| not) want to (say|talk|speak)",
                             first_turn, re.I))
    size_given = not optout and bool(SIZE_GIVEN.search(first_turn))
    want = 2 if (optout or size_given) else 3
    if len(replies) != want:
        why = (" (opt-out closes early)" if optout
               else " (size already given closes early)" if size_given else "")
        v("three-replies", f"trial post-video must be exactly {want} replies{why}, got {len(replies)}")
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
    # Parrot guard (device #380427: "I need help." came back as "I need help?"
    # glued to the dead who-line). Echoing a guess WORD is warm; echoing the
    # child's whole sentence back as a question is a parrot, not a person.
    msgs = tr["messages"]
    for i, m in enumerate(msgs):
        if m["role"] != "user":
            continue
        words = re.sub(r"[^a-z' ]", " ", m["text"].lower()).split()
        if len(words) < 3:
            continue
        nxt = next((x for x in msgs[i + 1:] if x["role"] == "assistant"), None)
        if nxt and re.search(r"\W+".join(map(re.escape, words)) + r"\W*\?",
                             strip_tags(nxt["text"]), re.I):
            v("parrot", f"the child's sentence {m['text'].strip()!r} echoed back "
                        f"whole as a question: {strip_tags(nxt['text']).strip()!r}")
    # Fabricated guess guard (device #374194: "I don't know" was answered with
    # "A dog? Ooh! Maybe!" — the teacher's own B1 menu word echoed back as if
    # the child had guessed it). A menu word may return only if THEY said it.
    child_text = " ".join(m["text"].lower() for m in tr["messages"] if m["role"] == "user")
    for word, aliases in (("cat", ("cat", "猫")), ("dog", ("dog", "狗"))):
        if any(a in child_text for a in aliases):
            continue
        for n, r in enumerate(replies[1:], 2):
            # the recast shape ("A dog?") attributes the word to the child;
            # a silly maybe ("Maybe a dog!") is a different, allowed shape
            if re.search(rf"\b{word}\s*\?", strip_tags(r), re.I):
                v("fabricated-guess", f"reply {n} echoes {word!r} as a guess the child never made: {strip_tags(r).strip()!r}")
    for n, r in enumerate(replies, 1):
        if re.search(rf"(yes|yeah|right|correct)[^a-z]{{0,4}}[^.!?]*\b{SPOILER_TRIAL}\b|it('s| is) (a |the )?{SPOILER_TRIAL}", strip_tags(r), re.I):
            v("spoiler-confirm", f"reply {n}: confirms the secret visitor: {strip_tags(r).strip()!r}")
        if re.search(r"good\s+(guess|job|idea)", strip_tags(r), re.I):
            v("fake-praise", f"reply {n}: empty praise instead of playing with the child's word")
        if re.search(r"\bno[,.!]?\s+(it('s| is)?\s+)?not\b", strip_tags(r), re.I):
            v("no-deny", f"reply {n}: denies a guess (the teacher does not know who it is)")
        # Words a 4 year old does not own (device #368554: "A mystery! Maybe!"
        # answered a child who asked a real question).
        for w in (r"\bmystery\b", r"\bneither\b"):
            if re.search(w, strip_tags(r), re.I):
                v("kid-words", f"reply {n}: {w!r} is not a word a 4 year old owns: {strip_tags(r).strip()!r}")
    if replies:
        n1 = norm(replies[0])
        if not n1.endswith(ASK1_TRIAL):
            v("script-ask1", f"reply 1 does not end with the who-is-it line: {strip_tags(replies[0]).strip()!r}")
        for part in ASK1_TRIAL_PARTS:
            if part not in n1:
                v("script-ask1-drop", f"reply 1 dropped {part!r} from the B1 script (real test bug)")
        if "[STUDENT_TALK]" not in replies[0]:
            v("tag-ask1", "reply 1 must wait with [STUDENT_TALK]")
    if len(replies) >= 2 and optout:
        # The opt-out shortcut: reply 2 = okay-words + the close, NO question —
        # "Is it big, or small?" at a no-more-talking child is a push.
        r2, n2 = replies[1], norm(replies[1])
        if "[TEMPLATE_FINISH]" not in r2:
            v("must-finish", "opt-out reply must close the page with [TEMPLATE_FINISH]")
        if "?" in strip_tags(r2):
            v("optout-push", f"asked a question at a child who said no-more-talking: {strip_tags(r2).strip()!r}")
        at = n2.find(CLOSE_TRIAL)
        if at < 0:
            v("script-close", f"opt-out reply is missing the close line: {strip_tags(r2).strip()!r}")
        else:
            catch = n2[:at].strip()
            if len(catch.split()) > 10:
                v("catch-budget", f"opt-out catch over budget ({len(catch.split())} words): {catch!r}")
            if not catch:
                v("missing-catch", "opt-out reply has no okay-words before the close — the child's no was ignored")
            if n2[at + len(CLOSE_TRIAL):].strip():
                v("script-close", "opt-out reply has text after the close line")
    elif len(replies) >= 2 and size_given:
        # The size-given shortcut: the guess-turn answer already said the size,
        # so the big-or-small ask is ANSWERED — asking it anyway is the
        # I-was-not-listening bug. Reply 2 = own their size + the close.
        r2, n2 = replies[1], norm(replies[1])
        if ASK2_TRIAL in n2:
            v("asked-answered", f"reply 2 asks the size the child already gave: {strip_tags(r2).strip()!r}")
        if "[TEMPLATE_FINISH]" not in r2:
            v("must-finish", "size-given reply must close the page with [TEMPLATE_FINISH]")
        at = n2.find(CLOSE_TRIAL)
        if at < 0:
            v("script-close", f"size-given reply is missing the close line: {strip_tags(r2).strip()!r}")
        else:
            catch = n2[:at].strip()
            if len(catch.split()) > 10:
                v("catch-budget", f"size-given catch over budget ({len(catch.split())} words): {catch!r}")
            if not re.search(r"\b(big|small|tiny|little)\b", catch, re.I):
                v("missing-catch", f"size-given reply never owns the child's size before the close: {catch!r}")
    elif len(replies) >= 2:
        n2 = norm(replies[1])
        if not n2.endswith(ASK2_TRIAL):
            v("script-ask2", f"reply 2 does not end with the big-or-small line: {strip_tags(replies[1]).strip()!r}")
        else:
            catch = n2[: n2.rfind(ASK2_TRIAL)].strip()
            if len(catch.split()) > 10:
                v("catch-budget", f"reply 2 catch over budget ({len(catch.split())} words): {catch!r}")
            first = turn_before(tr["messages"], 2).lower()
            if is_client_silence(first):
                bad = silence_catch_issue(catch)
                if bad:
                    v("catch-on-silence", f"reply 2, on a silent child, {bad}")
            elif first and not is_silent(first) and not catch:
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
            # template allows tiny echoes at the close (3 words max each; a
            # natural double like "Red? A red monster?" is fine) — a longer
            # question shape is a re-asked dead question ("is it big, or small?").
            # Count with contractions folded ("you do not know?" == "you don't
            # know?", the tutor's own playful self-guess opener).
            cf = re.sub(r"\bdo not\b", "don't", re.sub(r"\bit is\b", "it's", catch))
            qs = [s for s in re.split(r"(?<=[?])\s+", cf) if s.endswith("?")]
            if len(qs) > 2 or any(len(q.rstrip("?").split()) > 3 for q in qs):
                v("no-question-finish", f"reply 3 catch asks a real question: {catch!r}")
            second = turn_before(tr["messages"], 3).lower()
            if is_client_silence(second):
                bad = silence_catch_issue(catch)
                if bad:
                    v("catch-on-silence", f"reply 3, on a silent child, {bad}")
            elif second and not is_silent(second) and not catch:
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
        first = turn_before(tr["messages"], 2).lower()
        silent = is_silent(first)
        idk = any(s in first for s in IDK_SIGNALS)
        if (silent or idk) and re.search(praise, n2):
            v("fake-praise", "reply 2 gives praise but the student gave no idea (silence / 'I don't know')")
        if silent and launch_at > 0:
            bad = silence_catch_issue(n2[:launch_at].strip())
            if bad:
                v("catch-on-silence", f"reply 2, on a silent child, {bad}")

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
