"""V3-specific cases and raw-text checks. Legacy V2 expectations stay unchanged.

Mechanical checks are regression signals, not proof of naturalness, CEFR level,
audio quality, or pronunciation diagnosis. Review saved transcripts separately.
"""
import copy
import re

from tts_punctuation import punctuation_issues

MODELS = {"cow": "/k/ /aʊ/", "cat": "/k/ /æ/ /t/", "horse": "/h/ /ɔ/ /ɹ/ /s/"}
UNITS = {"k", "aʊ", "æ", "t", "h", "ɔ", "ɹ", "s", "æp", "əl", "l"}


def extend_cases(original):
    cases = copy.deepcopy(original)
    # Old fixtures required exclamation marks even where V2 scripts used periods.
    # Accept either ASCII sentence ending; preserve semantic content/word order.
    for group in cases.values():
        for case in group:
            for patterns in case.get("reply_require", {}).values():
                for i, pattern in enumerate(patterns):
                    patterns[i] = re.sub(r"(?<=[A-Za-z])!", "[.!]", pattern)
            # A partial word needs acknowledgment and a full sentence model,
            # not two redundant instructions with specific wording.
            if case["id"] == "l2sent-cow-word":
                case["reply_require"]["2"] = [r"^Yes, cow\.", r"It's a cow\.",
                    r"(?:Now (?:you )?try|Your turn)"]
            if case["id"] == "cat-old-word":
                # Match the grammatical wording already required by the template.
                case["reply_require"]["2"] = [r"^Yes, cow was first\. This is a cat\."]
            if case["id"] == "l2sent-horse-observation-after-retry":
                # Plain acknowledgment is more accessible than figurative praise.
                case["reply_require"]["3"] = ["saw cake on its mouth", "Let's watch and find out"]
                case["reply_forbid"]["3"].append("Good eyes")
            if case["id"] == "cow-how-asr":
                # V3 resolves ambiguous 'How?' toward help, not assumed mastery.
                case.update(id="v3-cow-ambiguous-how-help", turns=["How?", "cow", "moo", "no"],
                    note="Ambiguous How gets sound help rather than assumed cow success.",
                    max_replies=5, reply_require={"2": [r"/k/\s*/aʊ/", r"Your turn"]},
                    reply_forbid={"2": [r"^Yes", r"says moo"]})
    cases["leadin_pre"].append({
        "id": "v3-plain-hi-not-meet-too", "turns": ["hi"], "max_replies": 2,
        "v3_require": {"1": [r"Say hi to me\. Hi\."]},
        "v3_forbid": {"2": [r"meet you too"]},
    })
    for word, model in MODELS.items():
        family = "word_" + word
        sound = {"cow": "moo", "cat": "meow", "horse": "neigh"}[word]
        unit = {"cow": "/aʊ/", "cat": "/æ/", "horse": "/s/"}[word]
        specific = {"cow": "last sound", "cat": "middle sound", "horse": "last sound"}[word]
        additions = [
            ("help-not-success", [f"I can't say {word}.", word, sound, "no"],
             {"2": [re.escape(model), r"Your turn"]}, {"2": [r"says", r"^Yes"]}),
            ("slow", ["Can you say it slowly?", word, sound, "no"],
             {"2": [re.escape(model), r"Your turn"]}, {"2": [r"says"]}),
            ("specific-sound", [f"Please help me say the {specific} in {word}.", word, sound, "no"],
             {"2": [re.escape(unit), word]}, {"2": [r"says", re.escape(model)]}),
            ("still-lost", [f"I can't say {word}.", "I still can't say it.", sound, "no"],
             {"3": [r"/[^/]+/"]}, {"3": [r"^Yes", r"[Gg]reat", r"[Pp]erfect"]}),
            ("help-after-success", [word, f"How do I say the {specific} in {word}?", "no"],
             {"3": [re.escape(unit), rf"Does the {word} have the cake"]}, {}),
            ("no-laugh-echo", ["Haha yay. " + word, sound, "no"], {}, {}),
            ("refusal", ["I don't want to say it.", sound, "no"], {},
             {"2": [rf"(?:Your turn|Now you try|Say)[., ]+{word}", r"Let's try again"]}),
            ("asr-not-diagnosis", [{"cow": "kao", "cat": "kat", "horse": "hoss"}[word], sound, "no"],
             {"2": ["says"]}, {"2": [r"you (?:missed|forgot)|wrong sound|Your turn\. " + word]}),
        ]
        for suffix, turns, required, forbidden in additions:
            cases[family].append({"id": f"v3-{word}-{suffix}", "turns": turns,
                "max_replies": 5 if len(turns) == 4 else 4,
                "v3_require": required, "v3_forbid": forbidden})
    return cases


def check_extra(transcript):
    replies = [m["text"] for m in transcript["messages"] if m["role"] == "assistant"]
    issues = []
    for i, reply in enumerate(replies, 1):
        issues += [f"[v3-punctuation] reply {i}: {x}" for x in punctuation_issues(reply, UNITS)]
        if re.search(r"\b(?:ha(?:\s*ha)+|he(?:\s*he)+|hee\s*hee|yay|yaya|woohoo)\b", reply, re.I):
            issues.append(f"[v3-laughter] reply {i}: written laughter or cheering")
    for key, should_match in (("v3_require", True), ("v3_forbid", False)):
        for index, patterns in transcript.get(key, {}).items():
            i = int(index)
            if i > len(replies):
                issues.append(f"[{key}] missing reply {i}")
                continue
            for pattern in patterns:
                if bool(re.search(pattern, replies[i - 1], re.I)) != should_match:
                    issues.append(f"[{key}] reply {i}: {pattern!r}")
    return issues


def self_test():
    assert not check_extra({"messages": [{"role": "assistant", "text":
        "I'm here. /k/ /aʊ/ Cow.[TEACHER_LISTEN][STUDENT_TALK]"}]})
    for bad in ["Let’s try.", "Ha ha.", "Yay.", "Cow...", "Cow，", "/unknown/"]:
        assert check_extra({"messages": [{"role": "assistant", "text": bad}]})
    assert check_extra({"messages": [], "v3_require": {"2": ["/æ/"]}})


if __name__ == "__main__":
    self_test()
    print("V3 checker fixtures: PASS")
