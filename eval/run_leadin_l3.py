#!/usr/bin/env python3
"""Run the L3 lead-in battery straight against the Forge debug API.

First battery to use the direct connection (sandbox allowlist, 2026-07-15) —
no browser puppetry. Composes common_l3 + the step template per case, drives
the scripted child turns, saves one transcript JSON per case, then checks.

Usage:
  FORGE_TOKEN=... python3 eval/run_leadin_l3.py [--model gpt-5.4-mini]
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
RUNS = ROOT / "eval/runs/leadin_l3"

ROLE = (
    "You are Max, a bold, energetic jungle captain who turns every lesson into a thrilling mission. "
    "Your voice is loud and bright. You inspire children to be brave and speak up."
)
UI_READY = ("The UI is ready. Continue the lesson from where you left off,"
            "or start if nothing has begun yet.")
STEP_FILES = {
    "pre_video": "prompts/l3/leadin_teaching_rules_l3_step_pre_video.md",
    "post_video": "prompts/l3/leadin_teaching_rules_l3_step_post_video.md",
}
DEFAULT_NAME = "tom"
STOP_TAGS = ("[TEMPLATE_FINISH]", "[NEXT_STEP]")


def compose(step: str, name: str) -> str:
    common = (ROOT / "prompts/l3/common_teaching_simple_rules_l3.md").read_text()
    tmpl = (ROOT / STEP_FILES[step]).read_text()
    text = common.rstrip() + "\n\n" + tmpl.rstrip()
    for k, val in {
        "roleDescription": ROLE,
        "renderContent": "Lead-in stage.",
        "studentProfile": "No relevant information.",
        "name": name,
    }.items():
        text = text.replace("{{" + k + "}}", val)
    return text


def run_case(backend, step, case):
    prompt_name = case.get("student_name", DEFAULT_NAME)
    system = compose(step, prompt_name)
    messages = [{"role": "user", "content": UI_READY}]
    transcript = []
    turns, ti = case.get("turns", []), 0
    for _ in range(5):
        reply = backend.chat(system, messages)
        messages.append({"role": "assistant", "content": reply})
        transcript.append({"role": "assistant", "text": reply})
        if any(t in reply for t in STOP_TAGS):
            break
        child = turns[ti] if ti < len(turns) else "The student has been silent for 5 seconds"
        ti += 1
        messages.append({"role": "user", "content": child})
        transcript.append({"role": "user", "text": child})
    # junk default => checker must see no usable name
    checker_name = "" if prompt_name in ("test_user", "11") else prompt_name
    return {
        "family": "leadin_l3",
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
    ap.add_argument("--run-dir", type=pathlib.Path, default=RUNS,
                    help="where to save transcripts (default: the historical L3 directory)")
    ap.add_argument("--skip-existing", action="store_true",
                    help="reuse saved transcripts, then check the whole selected battery")
    args = ap.parse_args()

    os.environ.setdefault("FORGE_BASE_URL",
                          "http://dino-test-alb-2087276790.ap-southeast-1.elb.amazonaws.com/cms/api")
    os.environ.setdefault("FORGE_PROVIDER", "Azure OpenAI")
    os.environ["FORGE_MODEL"] = args.model
    backend = ForgeBackend()

    battery = yaml.safe_load((ROOT / "eval/cases_leadin_l3.yaml").read_text())
    run_dir = args.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for step, cases in battery.items():
        for case in cases:
            if args.only and case["id"] != args.only:
                continue
            p = run_dir / f"{case['id']}.json"
            if args.skip_existing and p.exists():
                print(f"reusing {case['id']} ...", flush=True)
            else:
                print(f"running {case['id']} ...", flush=True)
                tr = run_case(backend, step, case)
                p.write_text(json.dumps(tr, ensure_ascii=False, indent=1))
            paths.append(str(p))
    print(f"\n{len(paths)} transcripts -> {run_dir}")
    import subprocess
    sys.exit(subprocess.run(
        [sys.executable, str(ROOT / "eval/checker_leadin.py"), *paths]).returncode)


if __name__ == "__main__":
    main()
