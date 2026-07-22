#!/usr/bin/env python3
"""Run the 足球课 (World Cup soccer festival) lead-in battery against the Forge debug API.

Usage:
  FORGE_TOKEN=... python3 eval/run_leadin_soccer.py [--model gpt-5.4-mini] [--only case-id]
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
RUNS = ROOT / "eval/runs/leadin_soccer"

ROLE = (
    "You are Coach Leo, a warm, playful soccer coach who makes every class feel like "
    "a happy game day. Your voice is bright and kind. You cheer for every little try."
)
UI_READY = ("The UI is ready. Continue the lesson from where you left off,"
            "or start if nothing has begun yet.")
RENDER = (
    "nextTopic: soccer (World Cup festival lesson). "
    "videoDescribe: Kids and a friendly dino play soccer at the World Cup. "
    "The dino kicks the ball high, high toward the goal. Everyone cheers. "
    "characterRole: Dino."
)
STEP_FILES = {
    "pre_video": "prompts/festival/leadin_teaching_rules_l1_soccer_step_pre_video.md",
    "post_video": "prompts/festival/leadin_teaching_rules_l1_soccer_step_post_video.md",
}
DEFAULT_NAME = "tom"
STOP_TAGS = ("[TEMPLATE_FINISH]", "[NEXT_STEP]")


def compose(step: str, name: str, render: str = RENDER) -> str:
    common = (ROOT / "prompts/festival/common_teaching_simple_rules_l1_soccer.md").read_text()
    tmpl = (ROOT / STEP_FILES[step]).read_text()
    text = common.rstrip() + "\n\n" + tmpl.rstrip()
    for k, val in {
        "roleDescription": ROLE,
        "renderContent": render,
        "studentProfile": "No relevant information.",
        "name": name,
    }.items():
        text = text.replace("{{" + k + "}}", val)
    return text


def run_case(backend, step, case):
    prompt_name = case.get("student_name", DEFAULT_NAME)
    system = compose(step, prompt_name, case.get("render", RENDER))
    # seed = chat from a PAST step (in the API conversation, not the transcript)
    messages = [{"role": m["role"], "content": m["text"]} for m in case.get("seed", [])]
    messages.append({"role": "user", "content": UI_READY})
    transcript = []
    turns, ti = case.get("turns", []), 0
    for _ in range(4):
        reply = backend.chat(system, messages)
        messages.append({"role": "assistant", "content": reply})
        transcript.append({"role": "assistant", "text": reply})
        if any(t in reply for t in STOP_TAGS):
            break
        child = turns[ti] if ti < len(turns) else "The student has been silent for 5 seconds"
        ti += 1
        messages.append({"role": "user", "content": child})
        transcript.append({"role": "user", "text": child})
    checker_name = "" if prompt_name in ("test_user", "11") else prompt_name
    return {
        "family": "leadin_l1_soccer",
        "step": step,
        "case": case["id"],
        "student_name": checker_name,
        "forbid_phrases": case.get("forbid_phrases", []),
        "require_phrases": case.get("require_phrases", []),
        "messages": transcript,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("FORGE_MODEL", "gpt-5.4-mini"))
    ap.add_argument("--only", help="run a single case id")
    args = ap.parse_args()

    os.environ.setdefault("FORGE_BASE_URL",
                          "http://dino-test-alb-2087276790.ap-southeast-1.elb.amazonaws.com/cms/api")
    os.environ.setdefault("FORGE_PROVIDER", "Azure OpenAI")
    os.environ["FORGE_MODEL"] = args.model
    backend = ForgeBackend()

    battery = yaml.safe_load((ROOT / "eval/cases_leadin_soccer.yaml").read_text())
    RUNS.mkdir(parents=True, exist_ok=True)
    paths = []
    for step, cases in battery.items():
        for case in cases:
            if args.only and case["id"] != args.only:
                continue
            print(f"running {case['id']} ...", flush=True)
            tr = run_case(backend, step, case)
            p = RUNS / f"{case['id']}.json"
            p.write_text(json.dumps(tr, ensure_ascii=False, indent=1))
            paths.append(str(p))
    print(f"\n{len(paths)} transcripts -> {RUNS}")
    import subprocess
    sys.exit(subprocess.run(
        [sys.executable, str(ROOT / "eval/checker_leadin.py"), *paths]).returncode)


if __name__ == "__main__":
    main()
