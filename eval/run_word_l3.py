#!/usr/bin/env python3
"""Run the L3 word-page battery straight against the Forge debug API.

Usage:
  FORGE_TOKEN=... python3 eval/run_word_l3.py [--model gpt-5-mini] [--only case-id]
"""
import argparse
import json
import os
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from backends import ForgeBackend

ROOT = pathlib.Path(__file__).parent.parent
RUNS = ROOT / "eval/runs/word_l3"

ROLE = (
    "You are Max, a bold, energetic jungle captain who turns every lesson into a thrilling mission. "
    "Your voice is loud and bright. You inspire children to be brave and speak up."
)
UI_READY = ("The UI is ready. Continue the lesson from where you left off,"
            "or start if nothing has begun yet.")
FAMILY_FILES = {
    "word_l3_climb": "prompts/l3/word_teaching_rules_l3_climb.md",
    "word_l3_jump": "prompts/l3/word_teaching_rules_l3_jump.md",
    "word_l3_fly": "prompts/l3/word_teaching_rules_l3_fly.md",
}
FAMILY_RENDER = {
    "word_l3_climb": "Word teaching: climb. Dino and Mia see a tall wall.",
    "word_l3_jump": "Word teaching: jump. Dino and Mia see some rocks in the water.",
    "word_l3_fly": "Word teaching: fly. Dino and Mia are with a unicorn, high in the sky.",
}
DEFAULT_NAME = "tom"


def compose(family: str, name: str) -> str:
    common = (ROOT / "prompts/l3/common_teaching_simple_rules_l3.md").read_text()
    tmpl = (ROOT / FAMILY_FILES[family]).read_text()
    text = common.rstrip() + "\n\n" + tmpl.rstrip()
    for k, val in {
        "roleDescription": ROLE,
        "renderContent": FAMILY_RENDER[family],
        "studentProfile": "No relevant information.",
        "name": name,
    }.items():
        text = text.replace("{{" + k + "}}", val)
    return text


def run_case(backend, family, case):
    prompt_name = case.get("student_name", DEFAULT_NAME)
    system = compose(family, prompt_name)
    messages = [{"role": "user", "content": UI_READY}]
    transcript = []
    turns, ti = case.get("turns", []), 0
    for _ in range(5):
        reply = backend.chat(system, messages)
        messages.append({"role": "assistant", "content": reply})
        transcript.append({"role": "assistant", "text": reply})
        if "[TEMPLATE_FINISH]" in reply or "[NEXT_STEP]" in reply:
            break
        child = turns[ti] if ti < len(turns) else "The student has been silent for 5 seconds"
        ti += 1
        messages.append({"role": "user", "content": child})
        transcript.append({"role": "user", "text": child})
    checker_name = "" if prompt_name in ("test_user", "11") else prompt_name
    return {
        "family": family,
        "case": case["id"],
        "student_name": checker_name,
        "forbid_phrases": case.get("forbid_phrases", []),
        "require_phrases": case.get("require_phrases", []),
        "messages": transcript,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("FORGE_MODEL", "gpt-5-mini"))
    ap.add_argument("--only", help="run a single case id")
    args = ap.parse_args()

    os.environ.setdefault("FORGE_BASE_URL",
                          "http://dino-test-alb-2087276790.ap-southeast-1.elb.amazonaws.com/cms/api")
    os.environ.setdefault("FORGE_PROVIDER", "Azure OpenAI")
    os.environ["FORGE_MODEL"] = args.model
    backend = ForgeBackend()

    battery = yaml.safe_load((ROOT / "eval/cases_word_l3.yaml").read_text())
    RUNS.mkdir(parents=True, exist_ok=True)
    paths = []
    for family, cases in battery.items():
        for case in cases:
            if args.only and case["id"] != args.only:
                continue
            print(f"running {case['id']} ...", flush=True)
            tr = run_case(backend, family, case)
            p = RUNS / f"{case['id']}.json"
            p.write_text(json.dumps(tr, ensure_ascii=False, indent=1))
            paths.append(str(p))
    print(f"\n{len(paths)} transcripts -> {RUNS}")
    os.execvp(sys.executable, [sys.executable, str(ROOT / "eval/checker_word_l3.py"), *paths])


if __name__ == "__main__":
    main()
