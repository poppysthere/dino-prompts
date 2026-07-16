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
# Device bug #360356: the wonder used "cheer" — the child heard "chair" and
# was lost for the rest of the page. Grown-up nouns are out with the rest.
ANNOUNCER_TALK = [r"team\s+up", r"match\s+is\s+on", r"goal\s+or\s+no\s+goal",
                  r"we\s+will\s+see", r"\bmatch\b", r"\bversus\b", r"\bcompete\b",
                  r"\bchampionship\b", r"\bscore\b", r"\bcheer", r"\bchampion\b"]
AGREEMENT_ONLY = re.compile(r"^(好|好的|ok|okay|yes|嗯|恩)[。.!！]?$", re.I)
PRAISE = re.compile(r"great job|you got it|well done|you know it", re.I)
# An invite asks the child's MOUTH for the word: an invite phrase with the
# target word right after it ("One more time. Goal!"), OR a wait whose last
# words are the bare word as a call ("...Come on! Come on!" — the child WILL
# echo it; real device echo-loop bug ran four rounds). An invite phrase
# ALONE can be a legitimate answer-echo ("还要再读吗？" -> "Yes! One more
# time!") and is not counted. Budget: TWO invites (meet + one retry), both
# in the first two replies, and NONE after the child opts out.
INVITE_PHRASE = (r"(say\s+it|one\s+more\s+time|shout\s+with\s+me|your\s+turn"
                 r"|say\s+with\s+me|try\s+again)")
OPT_OUT = re.compile(r"不想说|不说了|不要说|不念|no\s+more|stop\s+it|i\s+don'?t\s+want", re.I)


def is_invite(body, word):
    w = word.rstrip("!")
    # invite phrase and the word in either order, close together
    # ("Say it with me. Goal!" / model variant "Team! Say it!")
    if re.search(INVITE_PHRASE + r"[^.!?]{0,20}[.!?,:\s]+\W{0,3}" + re.escape(w),
                 body, re.I):
        return True
    if re.search(re.escape(w) + r"\W{0,3}\s*" + INVITE_PHRASE, body, re.I):
        return True
    # ends on the word as a call, with no question to answer instead
    tail = re.sub(r"[^a-z\s']", " ", body.lower()).split()
    wl = w.lower().split()
    return "?" not in body and len(tail) >= len(wl) and tail[-len(wl):] == wl


def names_the_shout(body, word):
    # "That is COME ON!" (real device bug) — a phrase-shout named like a
    # thing on a shelf. Only phrase words ("come on"); "that is a goal"
    # pointing at the net is legitimate human speech.
    if " " not in word.strip():
        return False
    w = re.escape(word.rstrip("!"))
    return re.search(rf"(this|that|it)\s+is\s+(a\s+|the\s+)?\W{{0,3}}{w}\b",
                     body, re.I) is not None


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

    if len(replies) > 4:
        v("beat-budget", f"{len(replies)} teacher replies (max 4: meet, retry, wonder, close)")
    if replies and "[TEMPLATE_FINISH]" not in replies[-1]:
        v("must-finish", "last reply does not end the page with [TEMPLATE_FINISH]")

    retry_like = 0
    invites = 0
    opted_out = False
    wonder_asked = False
    last_user = None
    for i, m in enumerate(msgs):
        if m["role"] == "user":
            last_user = m["text"]
            if OPT_OUT.search(last_user):
                opted_out = True
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
        # A WAIT is a JOB, and after the two invites the only job is a real
        # question (device echo-loop bug: waits ending on the bare word made
        # the child echo forever).
        if "[STUDENT_TALK]" in r:
            # ONE-QUESTION LAW: once the wonder is out and the child has had
            # their turn, the next reply is the close — never another wait
            # (real bug: "Is the ball big?" four rounds, "你问过我了？…干嘛一直问？")
            if wonder_asked:
                v("second-question", f"reply {n}: still waiting after the wonder "
                                     f"— the reply after its answer is the close: {body.strip()!r}")
            inv = is_invite(body, word)
            if inv and n > 2:
                v("invite-late", f"reply {n}: still asks for the word after the two invites: {body.strip()!r}")
            if not inv and "?" not in body:
                v("wait-job", f"reply {n}: waits but hands the child no job: {body.strip()!r}")
            if not inv:
                wonder_asked = True
            if inv:
                invites += 1
                if opted_out:
                    v("opt-out", f"reply {n}: still invites after the child opted out: {body.strip()!r}")
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
        if names_the_shout(body, word):
            v("names-the-shout", f"reply {n}: names a shout like a thing "
                                 f"('That is {word}!' is not human speech): {body.strip()!r}")
        # request-shaped only: describing the PICTURE ("Friends wave.") is fine
        for pat in [r"show\s+me", r"let\s+me\s+see", r"(can|do|will)\s+you\s+(wave|smile|clap)"]:
            if re.search(pat, body, re.I):
                v("invisible-action", f"reply {n}: asks for something the teacher cannot see ({pat!r})")

        # say-it call shape: "Say it with me. X?" teaches a rising copy
        if re.search(rf"say\s+it\s+with\s+me[.,!\s]+{re.escape(word)}\s*\?", body, re.I):
            v("rising-call", f"reply {n}: say-it call ends on a question mark")

        if n == 1 and word.rstrip("!") not in body.lower():
            v("meet-word", f"reply 1 never says the target word {word!r}")
        # wrong-word guard (real device bug: the Come on! page taught goal —
        # examples + goal-heavy history outvoted renderContent). Mentioning
        # the goal as a place in the picture is fine; TEACHING another lesson
        # word (say-it call, "This is X", doubled shout) is not. "come on" is
        # everyday encouragement, so only goal/team are cross-checked.
        for other in ("goal", "team"):
            if other == word:
                continue
            teach_pats = [
                rf"(say (it )?with me|one more time|shout with me|together)\W*{other}\b",
                rf"this is\W*{other}\b",
                rf"\b{other}\W+{other}\b",
            ]
            if any(re.search(p, body, re.I) for p in teach_pats):
                v("wrong-word", f"reply {n}: teaches {other!r} on a {word!r} page")

        # at most ONE real question per reply. "Yes or no?" choice tails and
        # tiny echoes of the child's own words ("You say yes?") are free.
        child_words = set(re.findall(r"[a-z]{3,}", (last_user or "").lower()))

        def real_question(s):
            if not s.endswith("?"):
                return False
            if re.fullmatch(r"yes\s+or\s+no\s*\?", s.strip(), re.I):
                return False
            toks = re.findall(r"[a-z]+", s.lower())
            if len(toks) <= 2:
                return False
            if len(toks) <= 6 and child_words & set(t for t in toks if len(t) >= 3):
                return False
            return True

        segs = re.split(r"(?<=[.!?])\s+", body.strip())
        nq = sum(1 for s in segs if real_question(s))
        if nq > 1:
            v("one-question", f"reply {n}: {nq} real questions in one reply")
        # the close asks no REAL question. A short question OPENING the close
        # is a warm catch ("You don't know? That's okay." — echoing a CJK
        # answer leaves no shared tokens, so length+position stand in for
        # the echo test); a question later or last is a dangling re-ask.
        if "[TEMPLATE_FINISH]" in r and "?" in body:
            qs = [(i, s) for i, s in enumerate(segs) if real_question(s)]
            qs = [(i, s) for i, s in qs
                  if not (i == 0 and len(re.findall(r"[a-z]+", s.lower())) <= 4)]
            if qs or re.search(r"yes\s+or\s+no\s*\?", body, re.I):
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
    if invites > 2:
        v("invite-budget", f"{invites} invite-shaped replies (max 2: the meet call + one retry)")

    # THE HUMAN RULE: never the same CONTENT sentence twice on one page
    # (device bug #360356: "That is okay! GOAL! GOAL!" sent twice, the MEET
    # line re-read verbatim at a confused kid). Ritual call formulas and
    # word-shouts/praise stubs repeat freely — at this age ritual is a hug.
    # Repeated invites are caught by the invite budget, so all ritual call
    # formulas are exempt here.
    rituals = {"say it with me", "one more time", "shout with me", "yes or no"}
    seen = {}
    for n, r in enumerate(replies, 1):
        for s in re.split(r"(?<=[.!?])\s+", strip_tags(r).strip()):
            key = re.sub(r"[^a-z0-9\s]", "", s.lower()).strip()
            bare = re.sub(rf"\b{re.escape(word.rstrip('!'))}\b", "", key)
            bare = re.sub(r"\s+", " ", bare).strip()
            if len(bare.split()) < 3 or bare in rituals:
                continue
            if key in seen:
                v("no-repeat", f"reply {n} repeats a sentence from reply {seen[key]}: {s.strip()!r}")
            else:
                seen[key] = n

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
