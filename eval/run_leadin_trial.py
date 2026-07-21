#!/usr/bin/env python3
"""Run the 新手引导体验课 (trial demo) lead-in battery against the Forge debug API.

Usage:
  FORGE_TOKEN=... python3 eval/run_leadin_trial.py [--model gpt-5-mini] [--only case-id]
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
RUNS = ROOT / "eval/runs/leadin_trial"

ROLES = {
    "max": (
        "You are Max, a bold, energetic jungle captain who turns every lesson into a "
        "thrilling mission. Your voice is loud and bright. Your energy is infectious. "
        "You inspire children to be brave and speak up."
    ),
    "kim": (
        "You are Kim — a warm, patient big sister who makes every child feel safe, "
        "heard, and brave enough to speak. You speak softly and gently. Your energy "
        "is calm and healing — never rushed, never loud."
    ),
}
UI_READY = ("The UI is ready. Continue the lesson from where you left off,"
            "or start if nothing has begun yet.")
STEP_FILES = {
    "pre_video": "prompts/trial/leadin_teaching_rules_trial_step_pre_video.md",
    "post_video": "prompts/trial/leadin_teaching_rules_trial_step_post_video.md",
}
DEFAULT_NAME = "nina"
STOP_TAGS = ("[TEMPLATE_FINISH]", "[NEXT_STEP]")
# Real device trap (#368067): the booking profile carries a stale 称呼
# nickname that must never win over <studentName>.
TOMMY_PROFILE = (
    "基础信息: 称呼：Tommy\n"
    '行为画像: {"summary": "A shy yet participative learner who prefers slow, '
    'friendly instruction.", "personality": "Shy but engaged; prefers gentle, '
    'patient tutors."}'
)


def render_content() -> str:
    """The standalone renderContent data file, minus its comment header."""
    raw = (ROOT / "prompts/trial/render_content_trial_leadin.md").read_text()
    return "\n".join(l for l in raw.splitlines() if not l.startswith("#")).strip()


def compose(step: str, name: str, role: str, profile: str) -> str:
    common = (ROOT / "prompts/trial/common_teaching_simple_rules_l1_trial.md").read_text()
    tmpl = (ROOT / STEP_FILES[step]).read_text()
    text = common.rstrip() + "\n\n" + tmpl.rstrip()
    for k, val in {
        "roleDescription": role,
        "renderContent": render_content(),
        "studentProfile": profile,
        "name": name,
    }.items():
        text = text.replace("{{" + k + "}}", val)
    return text


def run_case(backend, step, case):
    prompt_name = case.get("student_name", DEFAULT_NAME)
    role = ROLES[case.get("role", "max")]
    profile = TOMMY_PROFILE if case.get("profile") == "tommy" else "No relevant information."
    system = compose(step, prompt_name, role, profile)
    messages = [{"role": m["role"], "content": m["text"]} for m in case.get("seed", [])]
    messages.append({"role": "user", "content": UI_READY})
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
    checker_name = "" if prompt_name in ("test_user", "11") else prompt_name
    return {
        "family": "leadin_trial",
        "step": step,
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

    battery = yaml.safe_load((ROOT / "eval/cases_leadin_trial.yaml").read_text())
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
