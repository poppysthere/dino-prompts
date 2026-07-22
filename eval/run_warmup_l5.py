#!/usr/bin/env python3
"""Run the L5 warm-up battery against the Forge debug API.

Usage:
  FORGE_TOKEN=... python3 eval/run_warmup_l5.py [--model gpt-5.4-mini] [--only case-id]
"""
import argparse
import json
import os
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from backends import ForgeBackend
import checker_warmup

ROOT = pathlib.Path(__file__).parent.parent
RUNS = ROOT / "eval/runs/warmup_l5"

# Default role: Max (one of the three production personas). Cases may
# override with their own role: to pin the name-comes-from-role rule.
ROLE = (
    "You are Max, a bold, energetic jungle captain who turns every lesson into a "
    "thrilling mission. Your voice is loud and bright. You inspire children to be "
    "brave and speak up."
)
TOMMY_PROFILE = (
    "基础信息: 称呼：Tommy\n"
    '行为画像: {"summary": "A shy but engaged learner", "personality": "Shy yet engaged; prefers a gentle tone."}'
)
UI_READY = ("The UI is ready. Continue the lesson from where you left off,"
            "or start if nothing has begun yet.")

# (group -> is_first_meet, prompt name, checker name, profile)
GROUPS = {
    "path_a": (True, "heidi", "heidi", None),
    "path_a_extra": (True, "heidi", "heidi", None),
    "path_b": (False, "nina", "nina", None),
    "path_b_heidi": (False, "heidi", "heidi", TOMMY_PROFILE),
    "l5_broken": (False, "test_user", "", None),
}


def compose(is_first_meet: bool, name: str, profile: str, role: str = ROLE) -> str:
    common = (ROOT / "prompts/l5/common_teaching_simple_rules_l5.md").read_text()
    tmpl = (ROOT / "prompts/l5/warmup_teaching_rules_l5.md").read_text()
    text = common.rstrip() + "\n\n" + tmpl.rstrip()
    for k, val in {
        "roleDescription": role,
        "renderContent": "Warm up stage. No lesson content yet.",
        "studentProfile": profile,
        "name": name,
        "isFirstMeet": "true" if is_first_meet else "false",
    }.items():
        text = text.replace("{{" + k + "}}", val)
    return text


def run_case(backend, group, case):
    first_meet, prompt_name, checker_name, profile = GROUPS[group]
    system = compose(first_meet, prompt_name, profile or "No relevant information.",
                     case.get("role", ROLE))
    messages = [{"role": "user", "content": UI_READY}]
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
    return {
        "family": "warmup_l5",
        "case": case["id"],
        "is_first_meet": first_meet,
        "student_name": checker_name,
        "spoken_name": case.get("spoken_name", ""),
        "spoken_name_l1": case.get("spoken_name_l1", ""),
        "forbid_phrases": case.get("forbid_phrases", []),
        "require_phrases": case.get("require_phrases", []),
        "max_beats": case.get("max_beats"),
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

    battery = yaml.safe_load((ROOT / "eval/cases_warmup_l5.yaml").read_text())
    RUNS.mkdir(parents=True, exist_ok=True)
    passed = failed = 0
    for group, cases in battery.items():
        for case in cases:
            if args.only and case["id"] != args.only:
                continue
            print(f"running {case['id']} ...", flush=True)
            tr = run_case(backend, group, case)
            (RUNS / f"{case['id']}.json").write_text(json.dumps(tr, ensure_ascii=False, indent=1))
            violations = checker_warmup.check(tr)
            if violations:
                failed += 1
                print(f"  FAIL {case['id']}:")
                for vi in violations:
                    print("    " + vi)
            else:
                passed += 1
                print(f"  PASS {case['id']}")
    print(f"\n{passed} passed, {failed} failed -> {RUNS}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
