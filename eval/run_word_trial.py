#!/usr/bin/env python3
"""Run the trial-demo word-teaching battery (hedgehog, flamingo) against Forge.

Usage:
  FORGE_TOKEN=... python3 eval/run_word_trial.py [--model gpt-5.4-mini] [--only case-id] [--family word_trial_flamingo]
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
RUNS = ROOT / "eval/runs/word_trial"

ROLE = (
    "You are Max, a bold, energetic jungle captain who turns every lesson into a "
    "thrilling mission. Your voice is loud and bright. Your energy is infectious. "
    "You inspire children to be brave and speak up."
)
UI_READY = ("The UI is ready. Continue the lesson from where you left off,"
            "or start if nothing has begun yet.")
DEFAULT_NAME = "nina"
FAMILY_CONF = {
    "word_trial_hedgehog": {
        "word": "hedgehog",
        "template": "prompts/trial/word_teaching_rules_trial_hedgehog.md",
        "render": "prompts/trial/render_content_trial_word_hedgehog.md",
    },
    "word_trial_flamingo": {
        "word": "flamingo",
        "template": "prompts/trial/word_teaching_rules_trial_flamingo.md",
        "render": "prompts/trial/render_content_trial_word_flamingo.md",
    },
}


def render_content(family: str) -> str:
    raw = (ROOT / FAMILY_CONF[family]["render"]).read_text()
    return "\n".join(l for l in raw.splitlines() if not l.startswith("#")).strip()


def compose(family: str, name: str) -> str:
    common = (ROOT / "prompts/trial/common_teaching_simple_rules_l1_trial.md").read_text()
    tmpl = (ROOT / FAMILY_CONF[family]["template"]).read_text()
    text = common.rstrip() + "\n\n" + tmpl.rstrip()
    for k, val in {
        "roleDescription": ROLE,
        "renderContent": render_content(family),
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
        "family": "word_trial",
        "word": FAMILY_CONF[family]["word"],
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
    ap.add_argument("--family", help="run a single family")
    args = ap.parse_args()

    os.environ.setdefault("FORGE_BASE_URL",
                          "http://dino-test-alb-2087276790.ap-southeast-1.elb.amazonaws.com/cms/api")
    os.environ.setdefault("FORGE_PROVIDER", "Azure OpenAI")
    os.environ["FORGE_MODEL"] = args.model
    backend = ForgeBackend()

    battery = yaml.safe_load((ROOT / "eval/cases_word_trial.yaml").read_text())
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
