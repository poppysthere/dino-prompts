#!/usr/bin/env python3
"""Run the L3 sentence-trail battery straight against the Forge debug API.

Usage:
  FORGE_TOKEN=... python3 eval/run_sentence_l3.py [--model gpt-5-mini] [--only case-id]
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
RUNS = ROOT / "eval/runs/sentence_l3"

ROLE = (
    "You are Max, a bold, energetic jungle captain who turns every lesson into a thrilling mission. "
    "Your voice is loud and bright. You inspire children to be brave and speak up."
)
UI_READY = ("The UI is ready. Continue the lesson from where you left off,"
            "or start if nothing has begun yet.")
FAMILY_FILES = {
    "sent_l3_intro": "prompts/l3/sentence_teaching_rules_l3_step_intro.md",
    "sent_l3_can_you_climb": "prompts/l3/sentence_teaching_rules_l3_step_can_you_climb.md",
    "sent_l3_i_can_climb": "prompts/l3/sentence_teaching_rules_l3_step_i_can_climb.md",
    "sent_l3_can_you_fly": "prompts/l3/sentence_teaching_rules_l3_step_can_you_fly.md",
    "sent_l3_piece_of_cake": "prompts/l3/sentence_teaching_rules_l3_step_piece_of_cake.md",
    "wrapup_l3_pre": "prompts/l3/wrapup_teaching_rules_l3_step_pre_video.md",
}
FAMILY_RENDER = {
    "sent_l3_intro": "Sentence trail intro before the adventure video.",
    "sent_l3_can_you_climb": "Sentence teaching: Can you climb? Dino asks Mia.",
    "sent_l3_i_can_climb": "Sentence teaching: I can climb. Mia climbs the wall.",
    "sent_l3_can_you_fly": "Sentence teaching: Can you fly? A unicorn appears.",
    "sent_l3_piece_of_cake": "Sentence teaching: Piece of cake! Mia flies with the unicorn.",
    "wrapup_l3_pre": "Wrap up: Dino, Mia and the unicorn's family celebrate. A song video comes next.",
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
    # seed = chat from a PAST step (kept in the API conversation, but NOT in the
    # saved transcript: the checker judges only this step's replies)
    messages = [{"role": m["role"], "content": m["text"]} for m in case.get("seed", [])]
    messages.append({"role": "user", "content": UI_READY})
    transcript = []
    turns, ti = case.get("turns", []), 0
    for _ in range(6):
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
        "reply_forbid": case.get("reply_forbid", {}),
        "max_replies": case.get("max_replies"),
        "messages": transcript,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("FORGE_MODEL", "gpt-5-mini"))
    ap.add_argument("--only", help="run a single case id")
    ap.add_argument("--family", help="run only cases of one family")
    args = ap.parse_args()

    os.environ.setdefault("FORGE_BASE_URL",
                          "http://dino-test-alb-2087276790.ap-southeast-1.elb.amazonaws.com/cms/api")
    os.environ.setdefault("FORGE_PROVIDER", "Azure OpenAI")
    os.environ["FORGE_MODEL"] = args.model
    backend = ForgeBackend()

    battery = yaml.safe_load((ROOT / "eval/cases_sentence_l3.yaml").read_text())
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
    os.execvp(sys.executable, [sys.executable, str(ROOT / "eval/checker_sentence_l2.py"), *paths])


if __name__ == "__main__":
    main()
