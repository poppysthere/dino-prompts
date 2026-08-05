#!/usr/bin/env python3
"""Run the experimental cow language-rescue cases against Azure OpenAI.

Usage:
  AZURE_OPENAI_API_KEY=... python3 eval/run_word_language_rescue.py
  python3 eval/run_word_language_rescue.py --backend mock --only case-id
"""
import argparse
import json
import pathlib
import subprocess
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from backends import make_backend

ROOT = pathlib.Path(__file__).parent.parent
RUNS = ROOT / "eval/runs/word_language_rescue"
UI_READY = "The UI is ready. Continue the lesson from where you left off,or start if nothing has begun yet."
ROLE = (
    "You are Max, a bold, energetic jungle captain. You teach with tiny, warm, "
    "playful sentences and help every child feel brave."
)
RENDER = (
    '{"word":"cow","phonetic":"/kaʊ/","definition":"a large farm animal",'
    '"partOfSpeech":"n.","lessonStory":"Mouse is looking for who ate the cake."}'
)


def compose(support_language):
    common = (ROOT / "experiments/common_teaching_simple_rules_language_rescue.md").read_text()
    template = (ROOT / "experiments/word_teaching_rules_l2_cow_language_rescue.md").read_text()
    text = common.rstrip() + "\n\n" + template.rstrip()
    values = {
        "roleDescription": ROLE,
        "renderContent": RENDER,
        "studentProfile": "No relevant information.",
        "name": "nina",
        "supportLanguage": support_language,
    }
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def run_case(backend, case):
    messages = [{"role": "user", "content": UI_READY}]
    transcript = []
    turns = case["turns"]
    turn_i = 0
    for _ in range(7):
        reply = backend.chat(compose(case["support_language"]), messages)
        messages.append({"role": "assistant", "content": reply})
        transcript.append({"role": "assistant", "text": reply})
        if "[TEMPLATE_FINISH]" in reply:
            break
        child = turns[turn_i] if turn_i < len(turns) else "The student has been silent for 5 seconds"
        turn_i += 1
        if not child:
            child = "The student has been silent for 5 seconds"
        messages.append({"role": "user", "content": child})
        transcript.append({"role": "user", "text": child})
    return {
        "case": case["id"],
        "support_language": case["support_language"],
        "bridge": case["bridge"],
        "bridge_script": case.get("bridge_script"),
        "max_replies": case["max_replies"],
        "messages": transcript,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="azure", choices=["azure", "mock"])
    parser.add_argument("--only")
    args = parser.parse_args()

    cases = yaml.safe_load((ROOT / "eval/cases_word_language_rescue.yaml").read_text())["cases"]
    if args.only:
        cases = [case for case in cases if case["id"] == args.only]
    backend = make_backend(args.backend, {"word": "cow", "finish_line": "Let's keep looking. Come on, Mouse!", "opener": "Mouse sees a cow!"})

    RUNS.mkdir(parents=True, exist_ok=True)
    paths = []
    for case in cases:
        print(f"running {case['id']} ...", flush=True)
        result = run_case(backend, case)
        path = RUNS / f"{case['id']}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        paths.append(str(path))

    return subprocess.run(
        [sys.executable, str(ROOT / "eval/checker_word_language_rescue.py"), *paths]
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())

