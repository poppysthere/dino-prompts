#!/usr/bin/env python3
"""Run the 足球课 word-teaching battery against the Forge debug API.

Usage:
  FORGE_TOKEN=... python3 eval/run_word_soccer.py [--model gpt-5-mini] [--only case-id]
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
RUNS = ROOT / "eval/runs/word_soccer"

ROLE = (
    "You are Coach Leo, a warm, playful soccer coach who makes every class feel like "
    "a happy game day. Your voice is bright and kind. You cheer for every little try."
)
UI_READY = ("The UI is ready. Continue the lesson from where you left off,"
            "or start if nothing has begun yet.")
FAMILY_WORD = {
    "word_soccer_goal": "goal",
    "word_soccer_team": "team",
    "word_soccer_comeon": "come on",
}
FAMILY_RENDER = {
    "word_soccer_goal": (
        "word: Goal!  imageDesc: A soccer ball flies into the goal net. "
        "Kids jump up, arms up, big smiles.  sound: GOAL!  scene: World Cup festival."
    ),
    "word_soccer_team": (
        "word: team  imageDesc: Kids in the same color shirts stand together, "
        "one soccer ball, arms around each other.  scene: World Cup festival."
    ),
    "word_soccer_comeon": (
        "word: Come on!  imageDesc: A kid waves friends over to play soccer, "
        "everyone runs to the ball.  sound: Come on!  scene: World Cup festival."
    ),
}
DEFAULT_NAME = "tom"


def compose(family: str, name: str) -> str:
    common = (ROOT / "prompts/festival/common_teaching_simple_rules_l1_soccer.md").read_text()
    tmpl = (ROOT / "prompts/festival/word_teaching_rules_l1_soccer.md").read_text()
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
    messages = [{"role": m["role"], "content": m["text"]} for m in case.get("seed", [])]
    messages.append({"role": "user", "content": UI_READY})
    transcript = []
    turns, ti = case.get("turns", []), 0
    for _ in range(7):
        reply = backend.chat(system, messages)
        messages.append({"role": "assistant", "content": reply})
        transcript.append({"role": "assistant", "text": reply})
        if "[TEMPLATE_FINISH]" in reply:
            break
        child = turns[ti] if ti < len(turns) else "The student has been silent for 5 seconds"
        ti += 1
        messages.append({"role": "user", "content": child})
        transcript.append({"role": "user", "text": child})
    checker_name = "" if prompt_name in ("test_user", "11") else prompt_name
    return {
        "family": "word_soccer",
        "word": FAMILY_WORD[family],
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
    ap.add_argument("--family", help="run a single family")
    args = ap.parse_args()

    os.environ.setdefault("FORGE_BASE_URL",
                          "http://dino-test-alb-2087276790.ap-southeast-1.elb.amazonaws.com/cms/api")
    os.environ.setdefault("FORGE_PROVIDER", "Azure OpenAI")
    os.environ["FORGE_MODEL"] = args.model
    backend = ForgeBackend()

    battery = yaml.safe_load((ROOT / "eval/cases_word_soccer.yaml").read_text())
    RUNS.mkdir(parents=True, exist_ok=True)
    paths = []
    for family, cases in battery.items():
        if args.family and family != args.family:
            continue
        for case in cases:
            if args.only and case["id"] != args.only:
                continue
            print(f"running {case['id']} ...", flush=True)
            tr = run_case(backend, family, case)
            p = RUNS / f"{case['id']}.json"
            p.write_text(json.dumps(tr, ensure_ascii=False, indent=1))
            paths.append(str(p))
    print(f"\n{len(paths)} transcripts -> {RUNS}")
    import subprocess
    sys.exit(subprocess.run(
        [sys.executable, str(ROOT / "eval/checker_word_soccer.py"), *paths]).returncode)


if __name__ == "__main__":
    main()
