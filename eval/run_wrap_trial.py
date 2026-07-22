#!/usr/bin/env python3
"""Run the 新手引导体验课 (trial demo) wrap-up battery against Forge.

The wrap has only two device steps: pre-video (teacher speaks) and the final
video (giraffe reveal, ends the class). Pre-video = recap cheer + one guess
round about the last shadow + the goodbye, launched with [NEXT_STEP].

Usage:
  FORGE_TOKEN=... python3 eval/run_wrap_trial.py [--model gpt-5.4-mini] [--only case-id]
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
RUNS = ROOT / "eval/runs/wrap_trial"

ROLE_MAX = (
    "You are Max, a bold, energetic jungle captain who turns every lesson into a "
    "thrilling mission. Your voice is loud and bright. Your energy is infectious. "
    "You inspire children to be brave and speak up."
)
UI_READY = ("The UI is ready. Continue the lesson from where you left off,"
            "or start if nothing has begun yet.")
TEMPLATE = "prompts/trial/wrapup_teaching_rules_trial_step_pre_video.md"
DEFAULT_NAME = "nina"
STOP_TAGS = ("[TEMPLATE_FINISH]", "[NEXT_STEP]")
# History the child carries in: the word game page just closed.
GAME_TAIL = [
    {"role": "assistant",
     "text": "WOW! Hedgehog! Flamingo! You know them! Super![TEACHER_APPLAUD][TEMPLATE_FINISH]"},
]


def render_content() -> str:
    raw = (ROOT / "prompts/trial/render_content_trial_wrap_giraffe.md").read_text()
    return "\n".join(l for l in raw.splitlines() if not l.startswith("#")).strip()


def compose(name: str) -> str:
    common = (ROOT / "prompts/trial/common_teaching_simple_rules_l1_trial.md").read_text()
    tmpl = (ROOT / TEMPLATE).read_text()
    text = common.rstrip() + "\n\n" + tmpl.rstrip()
    for k, val in {
        "roleDescription": ROLE_MAX,
        "renderContent": render_content(),
        "studentProfile": "No relevant information.",
        "name": name,
    }.items():
        text = text.replace("{{" + k + "}}", val)
    return text


def run_case(backend, case):
    prompt_name = case.get("student_name", DEFAULT_NAME)
    system = compose(prompt_name)
    seed = GAME_TAIL + case.get("seed", [])
    messages = [{"role": m["role"], "content": m["text"]} for m in seed]
    messages.append({"role": "user", "content": UI_READY})
    # Seeded assistant beats (earlier pages) stay out of the transcript so the
    # checker judges only this step; seeded user lines stay in for the spoiler
    # guard (the child may have brought the secret).
    transcript = [{"role": "user", "text": m["text"]}
                  for m in case.get("seed", []) if m["role"] == "user"]
    turns, ti = case.get("turns", []), 0
    for _ in range(3):
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
        "family": "wrap_trial",
        "step": "pre_video",
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

    battery = yaml.safe_load((ROOT / "eval/cases_wrap_trial.yaml").read_text())
    RUNS.mkdir(parents=True, exist_ok=True)
    paths = []
    for step, cases in battery.items():
        for case in cases:
            if args.only and case["id"] != args.only:
                continue
            print(f"running {case['id']} ...", flush=True)
            tr = run_case(backend, case)
            p = RUNS / f"{case['id']}.json"
            p.write_text(json.dumps(tr, ensure_ascii=False, indent=1))
            paths.append(str(p))
    print(f"\n{len(paths)} transcripts -> {RUNS}")
    import subprocess
    sys.exit(subprocess.run(
        [sys.executable, str(ROOT / "eval/checker_leadin.py"), *paths]).returncode)


if __name__ == "__main__":
    main()
