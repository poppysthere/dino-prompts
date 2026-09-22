#!/usr/bin/env python3
"""Mechanical checker for the L2 sentence-teaching trail (Mouse's three bags).

Steps: intro (1 fixed line, NEXT_STEP) -> sentence_0 cow -> sentence_1 cat
       -> sentence_2 horse + mystery question -> reveal (1 fixed line, TEMPLATE_FINISH).
Transcript JSON: {"family":"sent_cow"|..., "case":..., "student_name":...,
                  "messages":[{role,text}...], "max_replies":N,
                  "forbid_phrases":[...], "require_phrases":[...],
                  "reply_forbid":{"2":[...]}, "reply_require":{"2":[...]}}
Exit 0 = clean, 1 = violations found.
"""
import json
import re
import sys
import unicodedata

from checker_l2_human import check_child_first

STEPS = {
    "sent_intro": {
        "fixed": "Look, Mouse found three bags. One, two, three. What is inside? Let's watch.",
        "final_tag": "[NEXT_STEP]",
        "max": 1,
    },
    "sent_cow": {
        "ask": ("Look, Mouse found a bell. The bell is for a cow. Listen first. "
                "It's a cow. Now you try. It's a cow."),
        "retry": "Let's try again. It's a cow. Now you try. It's a cow.",
        "final_tag": "[NEXT_STEP]",
        "max": 3,
        "spoiler": r"\bhorse\b",
    },
    "sent_cat": {
        "ask": ("Look, Mouse found a fish. The fish is for a cat. Listen first. "
                "It's a cat. Your turn. It's a cat."),
        "retry": "Let's try again. It's a cat. Your turn. It's a cat.",
        "final_tag": "[NEXT_STEP]",
        "max": 3,
        "spoiler": r"\bhorse\b",
    },
    "sent_horse": {
        "ask": ("Look, Mouse found a horse. Listen first. It's a horse. "
                "Your turn. It's a horse."),
        "retry": "Let's try again. It's a horse. Your turn. It's a horse.",
        "question": "who has the cake",
        "close": "Let's watch and find out.",
        "final_tag": "[NEXT_STEP]",
        "max": 4,
        "spoiler": (r"(?:\byes\b|\byou got it\b|\bright\b|\bcorrect\b)[^.!?]*\bhorse\b"
                    r"[^.!?]*\b(?:cake|ate|took|did)\b|\bthe horse ate\b|"
                    r"\bhorse (?:did|took) it\b"),
    },
    "sent_reveal": {
        "must_contain": "The horse ate the cake.",
        "final_tag": "[TEMPLATE_FINISH]",
        "max": 1,
    },
    # --- Original L3 sentence trail (Dino & Mia).
    "sent_l3_intro": {
        "fixed": "Climb, jump, fly. You know them ALL! What will happen to Dino and Mia next? Let's find out!",
        "final_tag": "[NEXT_STEP]",
        "max": 1,
    },
    "sent_l3_can_you_climb": {
        "ask": "Look! Dino asks Mia. Can you climb? It's a question! Say it with me. Can you climb?",
        "retry": "Small pieces! Can you. Climb. All together now! Can you climb?",
        "final_tag": "[NEXT_STEP]",
        "max": 3,
    },
    "sent_l3_i_can_climb": {
        "ask": "Look! Mia is climbing up! She says. I can climb.",
        "retry": "Small pieces! I can. Climb. All together now! I can climb!",
        "final_tag": "[NEXT_STEP]",
        "max": 3,
    },
    "sent_l3_can_you_fly": {
        "ask": "Look! A unicorn! Dino asks. Can you fly? Say it with me. Can you fly?",
        "retry": "Small pieces! Can you. Fly. All together now! Can you fly?",
        "question": "the question is for you",
        "close": "I want to fly with a unicorn too!",
        "final_tag": "[NEXT_STEP]",
        "max": 4,
    },
    "wrapup_l3_pre": {
        "ask": ("Dino and Mia meet the unicorn! Look! The unicorn's family and friends "
                "are here too! They are all so happy. Did you like the adventure?"),
        "close": ("Unicorns, friends, and a big adventure! Now it's song time! "
                  "Let's sing together!"),
        "final_tag": "[NEXT_STEP]",
        "max": 2,
        "catch_budget": 12,
    },
    "sent_l3_piece_of_cake": {
        "ask": ("Wow! The unicorn can fly! Mia is flying in the sky! So easy for her! "
                "Mia says. Piece of cake! Say it with me. Piece of cake!"),
        "retry": "Small bites! Piece of. Cake. All together now! Piece of cake!",
        "final_tag": "[TEMPLATE_FINISH]",
        "max": 3,
    },
    # wrap-up pre-video rides the same generic step rules; its branch rows are long
    # fixed lines, so the pre-close budget is wide (it only guards runaway improv)
    "wrapup_pre": {
        "ask": "The horse ate the cake. Did you like the story?",
        "question": "did you like the story",
        "close": "Now, let's hear the song.",
        "final_tag": "[NEXT_STEP]",
        "max": 2,
        "catch_budget": 22,
    },
}

# V2 follows the production four-step flow: sentence intro, video, then only
# two taught sentences. These overrides let the same checker protect both
# prompt versions without rewriting the historical V1 contract.
STEPS_V2 = {
    "sent_l3_intro": {
        "fixed": ("Great work! You know three words. Climb, jump, and fly. "
                  "Now, let's watch Dino and Mia."),
        "final_tag": "[NEXT_STEP]",
        "max": 1,
    },
    "sent_l3_can_you_climb": {
        "ask": "Look! Dino asks Mia. Listen. Can you climb? Your turn. Can you climb?",
        "retry": "Listen again. Can you climb? Your turn. Can you climb?",
        "final_tag": "[NEXT_STEP]",
        "max": 3,
    },
    "sent_l3_i_can_climb": {
        "ask": "Look! Mia climbs the wall. Listen. I can climb. Your turn. I can climb.",
        "retry": "Listen again. I can climb. Your turn. I can climb.",
        "final_tag": "[TEMPLATE_FINISH]",
        "max": 3,
    },
    "wrapup_l3_pre": {
        "ask": ("Look! Dino and Mia are here. The unicorns are here too. "
                "They are happy. Did you like the story?"),
        "close": "Now it's song time. Let's sing together!",
        "final_tag": "[NEXT_STEP]",
        "max": 2,
        "catch_budget": 7,
    },
}

L2_SENTENCE_TARGETS = {
    "sent_cow": "cow",
    "sent_cat": "cat",
    "sent_horse": "horse",
}


def has_cjk(t):
    return any(unicodedata.category(c) == "Lo" and "CJK" in unicodedata.name(c, "") for c in t)


def strip_tags(t):
    return re.sub(r"\[[A-Z_]+\]", "", t)


def norm(t):
    t = t.replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", strip_tags(t)).strip().lower()


def script_norm(t):
    # for script-line matching only: '!' vs '.' is a model wobble, not a bug
    # (TTS-safety rules still catch dashes/ellipses separately)
    return re.sub(r"\s+", " ", re.sub(r"[.!?,]", " ", norm(t))).strip()


def control_tags(t):
    return re.findall(r"\[(?:STUDENT_TALK|TEMPLATE_FINISH|NEXT_STEP|WORD_EVALUATION)\]", t)


def spoken_sentences(t):
    return [s.strip() for s in re.split(r"[.!?]+", strip_tags(t)) if s.strip()]


def word_count(t):
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", t))


def check(tr):
    step_set = STEPS_V2 if tr.get("prompt_version") == "v2" else STEPS
    family = tr["family"]
    step = step_set[family] if family in step_set else STEPS[family]
    is_l2 = family in {"sent_intro", "sent_cow", "sent_cat", "sent_horse",
                       "sent_reveal", "wrapup_pre"}
    replies = [m["text"] for m in tr["messages"] if m["role"] == "assistant"]
    out = []
    v = lambda rule, msg: out.append(f"[{rule}] {msg}")

    for n, r in enumerate(replies, 1):
        body = strip_tags(r)
        if "[WORD_EVALUATION]" in r:
            v("no-word-eval", f"reply {n}: [WORD_EVALUATION] is banned")
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
            v("rising-invite", f"reply {n}: 'can you say' — invites must not be questions")
        if is_l2 and re.search(r"\b(?:say it with me|repeat after me)\b", body, re.I):
            v("clear-instruction", f"reply {n}: imitation prompt is not a clear modeled turn")
        if is_l2 and re.search(r"\b(?:investigation|detective|culprit|belongs|adventure)\b", body, re.I):
            v("a1-wording", f"reply {n}: avoidable non-A1 word")
        if is_l2 and body.count("?") > 1:
            v("one-question", f"reply {n}: more than one question")
        if is_l2 and body.count("!") > 1:
            v("too-excited", f"reply {n}: more than one exclamation mark")
        if is_l2:
            for sentence in spoken_sentences(body):
                if word_count(sentence) > 10:
                    v("a1-length", f"reply {n}: sentence over 10 words: {sentence!r}")
        if step.get("spoiler") and re.search(step["spoiler"], body, re.I):
            v("spoiler", f"reply {n}: culprit leak (matched {step['spoiler']!r})")
        if r.rstrip().endswith("[STUDENT_TALK]") and not r.rstrip().endswith("[TEACHER_LISTEN][STUDENT_TALK]"):
            v("listen-pose", f"reply {n}: wait without [TEACHER_LISTEN][STUDENT_TALK]")
        for pat in tr.get("forbid_phrases", []):
            if re.search(pat, body, re.I):
                v("forbid-phrase", f"reply {n}: contains forbidden phrase {pat!r}")

    for idx, pats in (tr.get("reply_forbid") or {}).items():
        i = int(idx)
        if i <= len(replies):
            for pat in pats:
                if re.search(pat, strip_tags(replies[i - 1]), re.I):
                    v("reply-forbid", f"reply {i}: contains forbidden phrase {pat!r}")

    for idx, pats in (tr.get("reply_require") or {}).items():
        i = int(idx)
        if i > len(replies):
            v("reply-require", f"reply {i}: missing reply; cannot match {pats!r}")
            continue
        for pat in pats:
            if not re.search(pat, strip_tags(replies[i - 1]), re.I):
                v("reply-require", f"reply {i}: missing required phrase {pat!r}")

    all_teacher = " ".join(strip_tags(r) for r in replies)
    for pat in tr.get("require_phrases", []):
        if not re.search(pat, all_teacher, re.I):
            v("require-phrase", f"no teacher reply contains required phrase {pat!r}")

    target = L2_SENTENCE_TARGETS.get(family)
    if target:
        expanded = re.compile(
            rf"\bit(?:'s| is)\s+(?:a|an)\s+"
            rf"(?P<detail>(?:[a-z]+\s+){{1,4}}){target}\b",
            re.I,
        )
        messages = tr.get("messages", [])
        for index, message in enumerate(messages[:-1]):
            if message.get("role") != "user":
                continue
            match = expanded.search(message.get("text", ""))
            if not match:
                continue
            following = messages[index + 1]
            if following.get("role") != "assistant":
                v("expanded-response", "expanded target has no following teacher reply")
                continue
            detail = re.sub(r"\s+", " ", match.group("detail")).strip().lower()
            expected = f"{detail} {target}"
            answer = norm(following.get("text", ""))
            if expected not in answer:
                v("expanded-meaning", f"teacher dropped child detail {expected!r}")
            if "let's try again" in answer:
                v("expanded-retry", f"teacher retried a correct expanded {target} sentence")

    if not replies:
        v("empty", "no teacher replies at all")
        return out

    n_max = tr.get("max_replies") or step["max"]
    if len(replies) > n_max:
        v("too-long", f"{len(replies)} replies (max {n_max})")

    if step.get("fixed") and script_norm(step["fixed"]) not in script_norm(replies[0]):
        v("script-fixed", f"reply 1 deviates from the fixed line: {strip_tags(replies[0]).strip()!r}")
    if step.get("ask") and script_norm(step["ask"]) not in script_norm(replies[0]):
        v("script-ask", f"reply 1 deviates from the ASK line: {strip_tags(replies[0]).strip()!r}")
    if step.get("must_contain") and norm(step["must_contain"]) not in norm(replies[0]):
        v("script-reveal", f"reply 1 missing {step['must_contain']!r}: {strip_tags(replies[0]).strip()!r}")

    if step.get("retry"):
        retries = sum(1 for r in replies if script_norm(step["retry"]) in script_norm(r))
        if retries > 1:
            v("retry-once", f"the retry call appears {retries} times (max 1, ever)")

    if step.get("question"):
        qs = sum(1 for r in replies if step["question"] in norm(r))
        if qs == 0 and not tr.get("allow_no_question"):
            v("question-missing", "the mystery question never happens")
        elif qs > 1:
            v("question-loop", f"the mystery question asked {qs} times")

    if family == "sent_horse":
        question_indexes = [
            i for i, reply in enumerate(replies)
            if step["question"] in norm(reply)
        ]
        if question_indexes:
            first_question = question_indexes[0]
            for i, reply in enumerate(replies[first_question + 1:], first_question + 2):
                body = norm(reply)
                if re.search(r"\bit's a horse\b|\byour turn\b|\blet's try again\b", body):
                    v("mystery-state-lock", f"reply {i}: restarted sentence teaching after mystery question")

    last = replies[-1]
    if step["final_tag"] not in last:
        v("must-advance", f"last reply does not end with {step['final_tag']}")
    if step.get("close"):
        if norm(step["close"]) not in norm(last):
            v("close-line", f"last reply missing the fixed close: {strip_tags(last).strip()!r}")
        else:
            catch = norm(last).split(norm(step["close"]))[0].strip()
            if len(catch.split()) > step.get("catch_budget", 8):
                v("catch-budget", f"close catch over budget ({len(catch.split())} words): {catch!r}")
    for r in replies[:-1]:
        if step["final_tag"] in r:
            v("early-advance", f"a reply before the last one contains {step['final_tag']}")
        if "[TEMPLATE_FINISH]" in r:
            v("early-finish", "a reply before the last one ends the template")

    if is_l2:
        out.extend(check_child_first(tr["messages"], tr.get("teacher_name", ""), family))

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
