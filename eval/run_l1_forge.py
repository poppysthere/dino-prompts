#!/usr/bin/env python3
"""Run the full L1 pre-A1 lesson battery through Prompt Forge.

Local Git prompts are composed and sent to Forge's debug API. The runner does
not edit or deploy Forge content. Exit 0 means all selected cases passed; exit
1 means quality failures; exit 2 means configuration or Forge preflight failed.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys
import urllib.request

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from backends import ForgeBackend
import checker_l1


ROOT = pathlib.Path(__file__).resolve().parent.parent
PROMPT_DIR = ROOT / "prompts/l1"
CASES_PATH = ROOT / "eval/cases_l1.yaml"
DEFAULT_BASE = "http://dino-test-alb-2087276790.ap-southeast-1.elb.amazonaws.com/cms/api"
DEFAULT_MODEL = "gpt5.6LunaChatModel"
CATALOG_IDS = {DEFAULT_MODEL: "gpt-5.6-luna"}
UI_READY = (
    "The UI is ready. Continue the lesson from where you left off,"
    "or start if nothing has begun yet."
)
STOP_TAGS = ("[NEXT_STEP]", "[TEMPLATE_FINISH]")

FAMILIES = {
    "leadin_pre": {
        "stage": "leadin",
        "template": "leadin_teaching_rules_l1_step_pre_video.md",
        "render": "Chef Boo begins a food lesson. A short video comes next.",
    },
    "leadin_post": {
        "stage": "leadin",
        "template": "leadin_teaching_rules_l1_step_post_video.md",
        "render": "Chef Boo has food. The child will learn apple, juice, and bread.",
    },
    "warmup": {
        "stage": "warmup",
        "template": "warmup_teaching_rules_l1l2.md",
        "render": "Warm-up before the food lesson.",
    },
    "word_apple": {
        "stage": "word",
        "template": "word_teaching_rules_l1l2_apple.md",
        "render": "Word teaching: apple. Chef Boo holds an apple.",
    },
    "word_bread": {
        "stage": "word",
        "template": "word_teaching_rules_l1l2_bread.md",
        "render": "Word teaching: bread. Chef Boo has bread.",
    },
    "word_juice": {
        "stage": "word",
        "template": "word_teaching_rules_l1l2_juice.md",
        "render": "Word teaching: juice. Chef Boo has juice.",
    },
    "sentence_intro": {
        "stage": "sentence",
        "template": "sentence_teaching_rules_l1l2_pre_video.md",
        "render": "Apple, juice, and bread are on screen. A video of Boo eating comes next.",
    },
    "sentence_like_bread": {
        "stage": "sentence",
        "template": "sentence_teaching_rules_l1l2_i_like_bread.md",
        "render": "Sentence teaching: I like bread. Boo eats bread.",
    },
    "sentence_dont_apples": {
        "stage": "sentence",
        "template": "sentence_teaching_rules_l1l2_i_dont_like_apples.md",
        "render": "Sentence teaching: I don't like apples. Boo says yuck.",
    },
    "wrapup": {
        "stage": "wrapup",
        "template": "wrapup_teaching_rules_l1l2.md",
        "render": "Wrap-up. Chef Boo has apple, juice, and bread. The song comes next.",
    },
}


def fill(text, mapping):
    for key, value in mapping.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


def prompt_hashes():
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(PROMPT_DIR.glob("*.md"))
    }


def compose(family, case):
    teacher = case.get("teacher_name", "Kim")
    student = case.get("student_name", "Mia")
    role = case.get("role_description") or (
        f"You are {teacher}, a warm and patient teacher. You speak naturally, "
        "answer the child first, and give one clear next action."
    )
    mapping = {
        "roleDescription": role,
        "renderContent": FAMILIES[family]["render"],
        "studentProfile": "No relevant information.",
        "name": student,
        "teacherName": teacher,
    }
    common = fill((PROMPT_DIR / "common_teaching_simple_rules.md").read_text(), mapping)
    template = fill((PROMPT_DIR / FAMILIES[family]["template"]).read_text(), mapping)
    return common.rstrip() + "\n\n" + template.rstrip(), student, teacher


def load_cases():
    data = yaml.safe_load(CASES_PATH.read_text())
    return {
        family: data[family]
        for family in FAMILIES
    }


def run_case(backend, family, case):
    system, student, teacher = compose(family, case)
    messages = [{"role": "user", "content": UI_READY}]
    transcript_messages = []
    turns = case.get("turns", [])
    turn_index = 0

    for _ in range(6):
        reply = backend.chat(system, messages)
        messages.append({"role": "assistant", "content": reply})
        transcript_messages.append({"role": "assistant", "text": reply})
        if any(tag in reply for tag in STOP_TAGS):
            break
        child = turns[turn_index] if turn_index < len(turns) else (
            "The student has been silent for 5 seconds"
        )
        turn_index += 1
        messages.append({"role": "user", "content": child})
        transcript_messages.append({"role": "user", "text": child})

    return {
        "family": family,
        "case": case["id"],
        "student_name": student,
        "teacher_name": teacher,
        "max_replies": case.get("max_replies"),
        "forbid_phrases": case.get("forbid_phrases", []),
        "require_phrases": case.get("require_phrases", []),
        "reply_forbid": case.get("reply_forbid", {}),
        "reply_require": case.get("reply_require", {}),
        "messages": transcript_messages,
    }


def check_model(backend, model):
    request = urllib.request.Request(
        f"{backend.base}/classroom-debug/models",
        headers={"Authorization": backend.token},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("code") != 200:
        raise RuntimeError(f"Forge model lookup failed with code {result.get('code')}")
    values = {
        value
        for item in (result.get("data") or [])
        for value in (item.get("id"), item.get("cmsModel"), item.get("classModel"))
        if value
    }
    catalog_id = CATALOG_IDS.get(model, model)
    if catalog_id not in values:
        raise RuntimeError(f"Forge does not list model {catalog_id!r}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--stage",
        choices=("leadin", "warmup", "word", "sentence", "wrapup"),
        action="append",
    )
    parser.add_argument("--only", help="run one case ID")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--resume", type=pathlib.Path)
    args = parser.parse_args()

    batteries = load_cases()
    stages = set(args.stage or ("leadin", "warmup", "word", "sentence", "wrapup"))
    selected = [
        (family, case)
        for family, cases in batteries.items()
        if FAMILIES[family]["stage"] in stages
        for case in cases
        if not args.only or case["id"] == args.only
    ]
    if not selected:
        parser.error("no selected L1 cases")

    print("Lesson: L1 food lesson, ages 4-6, CEFR pre-A1")
    print(f"Prompt source: {PROMPT_DIR}")
    print(f"Forge modelName: {args.model}")
    for stage in ("leadin", "warmup", "word", "sentence", "wrapup"):
        count = sum(FAMILIES[family]["stage"] == stage for family, _ in selected)
        if count:
            print(f"  {stage}: {count} cases")
    print(f"Total: {len(selected)} cases")
    if args.plan:
        return 0

    if not os.environ.get("FORGE_TOKEN") and not (
            os.environ.get("FORGE_EMAIL") and os.environ.get("FORGE_PASSWORD")):
        parser.error("Forge authentication missing")

    os.environ.setdefault("FORGE_BASE_URL", DEFAULT_BASE)
    os.environ.setdefault("FORGE_PROVIDER", "Azure OpenAI")
    os.environ["FORGE_MODEL"] = args.model
    try:
        backend = ForgeBackend()
        check_model(backend, args.model)
    except Exception as exc:
        print(
            f"Forge preflight failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2

    hashes = prompt_hashes()
    if args.resume:
        run_dir = args.resume.resolve()
        report = json.loads((run_dir / "report.json").read_text())
        if report["model"] != args.model or report["prompt_sha256"] != hashes:
            parser.error("model or prompt files changed; start a new run")
    else:
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = ROOT / "eval/runs" / f"l1_{args.model}_{stamp}"
        run_dir.mkdir(parents=True, exist_ok=False)
        report = {
            "model": args.model,
            "forge_picker_id": CATALOG_IDS.get(args.model, args.model),
            "lesson": "L1 food lesson, ages 4-6, CEFR pre-A1",
            "started_at_utc": stamp,
            "prompt_sha256": hashes,
            "cases": {},
        }

    failures = []
    for family, case in selected:
        stage = FAMILIES[family]["stage"]
        case_dir = run_dir / stage
        case_dir.mkdir(parents=True, exist_ok=True)
        case_path = case_dir / f"{case['id']}.json"
        if args.resume and case_path.exists():
            transcript = json.loads(case_path.read_text())
            print(f"reusing {case['id']} ...", flush=True)
        else:
            print(f"running {case['id']} ...", flush=True)
            transcript = run_case(backend, family, case)
            case_path.write_text(
                json.dumps(transcript, ensure_ascii=False, indent=2)
            )

        issues = checker_l1.check(transcript)
        report["cases"][case["id"]] = {
            "family": family,
            "path": str(case_path.relative_to(ROOT)),
            "passed": not issues,
            "issues": issues,
        }
        if issues:
            failures.append(case["id"])
            print(f"FAIL {case['id']}")
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"PASS {case['id']}")
        (run_dir / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2)
        )

    print(f"\nL1 result: {len(selected) - len(failures)}/{len(selected)} cases passed")
    print(f"Transcripts and report: {run_dir}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
