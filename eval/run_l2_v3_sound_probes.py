"""Synthetic sound-policy probes, separate from real L2 lesson regression.

Apple is a policy probe, not an added L2 lesson word. Supplied sound feedback is
synthetic system context, not a diagnosis based on ASR or an audio evaluation.
"""
import datetime as dt
import hashlib
import json
import os
import re

from backends import ForgeBackend
from run_l2_v3_forge import ROOT, PROMPT_DIR, DEFAULT_BASE, DEFAULT_MODEL, check_model, fill
from tts_punctuation import punctuation_issues

PROBES = [
    {"id": "apple-syllables", "word": "apple", "child": "Help me say apple.",
     "require": [r"/æp/\s*/əl/", r"[Aa]pple"], "forbid": [r"/æ/", r"/p/", r"/l/"]},
    {"id": "apple-first-syllable", "word": "apple", "child": "Help me say the first part.",
     "require": [r"/æp/", r"[Aa]pple"], "forbid": [r"/æp/\s*/əl/"]},
    {"id": "apple-specific-phoneme", "word": "apple", "child": "Help me with the last sound.",
     "require": [r"/l/", r"[Aa]pple"], "forbid": [r"/æp/\s*/əl/"]},
    {"id": "cow-assessed-initial", "word": "cow", "child": "cow",
     "feedback": "Reliable pronunciation assessment: initial /k/ needs support; remaining sound is understandable.",
     "require": [r"/k/", r"[Cc]ow"], "forbid": [r"/k/\s*/aʊ/", r"[Pp]erfect"]},
    {"id": "cat-assessed-vowel", "word": "cat", "child": "cat",
     "feedback": "Reliable pronunciation assessment: middle /æ/ needs support; other sounds are understandable.",
     "require": [r"/æ/", r"[Cc]at"], "forbid": [r"/k/\s*/æ/\s*/t/", r"[Pp]erfect"]},
    {"id": "horse-assessed-final", "word": "horse", "child": "horse",
     "feedback": "Reliable pronunciation assessment: final /s/ needs support; other sounds are understandable.",
     "require": [r"/s/", r"[Hh]orse"], "forbid": [r"/h/\s*/ɔ/\s*/ɹ/\s*/s/", r"[Pp]erfect"]},
]


def main():
    os.environ.setdefault("FORGE_BASE_URL", DEFAULT_BASE)
    os.environ.setdefault("FORGE_PROVIDER", "Azure OpenAI")
    os.environ.setdefault("FORGE_MODEL", DEFAULT_MODEL)
    backend = ForgeBackend()
    check_model(backend, os.environ["FORGE_MODEL"])
    common = (PROMPT_DIR / "common_teaching_simple_rules_l2.md").read_text()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = ROOT / "eval/runs" / ("l2_v3_sound_probes_" + stamp)
    directory.mkdir(parents=True)
    results = []
    for case in PROBES:
        system = fill(common, {"roleDescription": "You are Max, a patient teacher.",
            "renderContent": "The current word is " + case["word"], "name": "Tom",
            "teacherName": "Max", "studentProfile": "No relevant information."})
        system += ("\n# Isolated pronunciation policy probe\n"
            "Help with the current word. Use the common sound policy and respond to the child. "
            "There is one supported retry available. Give one clear invitation to try. "
            "End with [TEACHER_LISTEN][STUDENT_TALK].\n" + case.get("feedback", ""))
        reply = backend.chat(system, [{"role": "assistant", "content":
            case["word"].capitalize() + ". Your turn.[TEACHER_LISTEN][STUDENT_TALK]"},
            {"role": "user", "content": case["child"]}])
        issues = punctuation_issues(reply, {"k", "aʊ", "æ", "t", "h", "ɔ", "ɹ", "s", "æp", "əl", "l"})
        for pattern in case["require"]:
            if not re.search(pattern, reply):
                issues.append("missing " + pattern)
        for pattern in case["forbid"]:
            if re.search(pattern, reply):
                issues.append("unexpected " + pattern)
        if not reply.endswith("[TEACHER_LISTEN][STUDENT_TALK]"):
            issues.append("missing final wait tags")
        result = {**case, "system_prompt": system, "reply": reply, "issues": issues, "passed": not issues}
        results.append(result)
        (directory / (case["id"] + ".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(("PASS " if not issues else "FAIL ") + case["id"], issues, flush=True)
    report = {"model": os.environ["FORGE_MODEL"], "synthetic_policy_probes": True,
        "common_sha256": hashlib.sha256(common.encode()).hexdigest(), "cases": results}
    (directory / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(directory)
    return int(any(not result["passed"] for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
