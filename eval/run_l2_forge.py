#!/usr/bin/env python3
"""Run the no-warm-up L2 prompt battery through Prompt Forge.

The runner composes local Git prompt files and sends them to Forge's debug API.
It never edits or deploys Forge content. Every transcript is saved before it is
checked. Exit 0 means all selected cases passed; exit 1 means quality failures;
exit 2 means configuration or Forge preflight failure.
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
import checker_leadin_l2
import checker_sentence_l2
import checker_word


ROOT = pathlib.Path(__file__).resolve().parent.parent
PROMPT_DIR = ROOT / "prompts/l2"
DEFAULT_BASE = "http://dino-test-alb-2087276790.ap-southeast-1.elb.amazonaws.com/cms/api"
DEFAULT_MODEL = "gpt5.6LunaChatModel"
CATALOG_IDS = {DEFAULT_MODEL: "gpt-5.6-luna"}
UI_READY = ("The UI is ready. Continue the lesson from where you left off,"
            "or start if nothing has begun yet.")
STOP_TAGS = ("[NEXT_STEP]", "[TEMPLATE_FINISH]")

FAMILIES = {
    "leadin_pre": {
        "stage": "leadin", "cases": "cases_leadin_l2.yaml",
        "template": "leadin_teaching_rules_l2_step_pre_video.md",
        "checker": checker_leadin_l2.check,
        "render": "First lesson step. Meet Farmer Bob and watch his birthday video.",
    },
    "leadin_post": {
        "stage": "leadin", "cases": "cases_leadin_l2.yaml",
        "template": "leadin_teaching_rules_l2_step_post_video.md",
        "checker": checker_leadin_l2.check,
        "render": "The birthday cake is gone. Mouse is here to help.",
    },
    "word_cow": {
        "stage": "word", "cases": "cases_word_cow.yaml",
        "template": "word_teaching_rules_l2_cow.md",
        "checker": checker_word.check,
        "render": "Word teaching: cow. Mouse sees a cow while looking for the cake.",
    },
    "word_cat": {
        "stage": "word", "cases": "cases_word_cat.yaml",
        "template": "word_teaching_rules_l2_cat.md",
        "checker": checker_word.check,
        "render": "Word teaching: cat. Mouse sees a cat while looking for the cake.",
    },
    "word_horse": {
        "stage": "word", "cases": "cases_word_horse.yaml",
        "template": "word_teaching_rules_l2_horse.md",
        "checker": checker_word.check,
        "render": "Word teaching: horse. Mouse sees a horse while looking for the cake.",
    },
    "sent_intro": {
        "stage": "sentence", "cases": "cases_sentence_l2.yaml",
        "template": "sentence_teaching_rules_l2_step_intro.md",
        "checker": checker_sentence_l2.check,
        "render": "Sentence story intro. Mouse finds three bags.",
    },
    "sent_cow": {
        "stage": "sentence", "cases": "cases_sentence_l2.yaml",
        "template": "sentence_teaching_rules_l2_step_cow.md",
        "checker": checker_sentence_l2.check,
        "render": "Sentence teaching: It's a cow. Mouse finds a bell.",
    },
    "sent_cat": {
        "stage": "sentence", "cases": "cases_sentence_l2.yaml",
        "template": "sentence_teaching_rules_l2_step_cat.md",
        "checker": checker_sentence_l2.check,
        "render": "Sentence teaching: It's a cat. Mouse finds a fish.",
    },
    "sent_horse": {
        "stage": "sentence", "cases": "cases_sentence_l2.yaml",
        "template": "sentence_teaching_rules_l2_step_horse.md",
        "checker": checker_sentence_l2.check,
        "render": "Sentence teaching: It's a horse. A reveal video comes next.",
    },
    "sent_reveal": {
        "stage": "sentence", "cases": "cases_sentence_l2.yaml",
        "template": "sentence_teaching_rules_l2_step_reveal.md",
        "checker": checker_sentence_l2.check,
        "render": "The reveal video shows that the horse ate the cake.",
    },
    "wrapup_pre": {
        "stage": "wrapup", "cases": "cases_wrapup_l2.yaml",
        "template": "wrapup_teaching_rules_l2_step_pre_video.md",
        "checker": checker_sentence_l2.check,
        "render": "Wrap-up before the cow, cat, and horse song.",
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


def load_cases():
    loaded = {}
    cache = {}
    for family, config in FAMILIES.items():
        path = ROOT / "eval" / config["cases"]
        if path not in cache:
            cache[path] = yaml.safe_load(path.read_text())
        loaded[family] = cache[path][family.replace("word_", "")]
        if family not in {"word_cow", "word_cat", "word_horse"}:
            loaded[family] = cache[path][family]
    return loaded


def compose(family, case):
    teacher = case.get("teacher_name", "Max")
    student = case.get("student_name", "tom")
    role = case.get("role_description") or (
        f"You are {teacher}, a warm, patient teacher. You listen carefully, answer the child "
        "like a real person, and give one clear next action."
    )
    mapping = {
        "roleDescription": role,
        "renderContent": FAMILIES[family]["render"],
        "studentProfile": "No relevant information.",
        "name": student,
        "teacherName": teacher,
    }
    common = fill((PROMPT_DIR / "common_teaching_simple_rules_l2.md").read_text(), mapping)
    template = fill((PROMPT_DIR / FAMILIES[family]["template"]).read_text(), mapping)
    return common.rstrip() + "\n\n" + template.rstrip(), student, teacher


def run_case(backend, family, case):
    system, student, teacher = compose(family, case)
    messages = [{"role": m["role"], "content": m["text"]} for m in case.get("seed", [])]
    messages.append({"role": "user", "content": UI_READY})
    transcript_messages = []
    turns = case.get("turns", [])
    turn_index = 0
    for _ in range(7):
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

    checker_student = "" if student in {"test_user", "11"} else student
    return {
        "family": family,
        "case": case["id"],
        "action_timing": True,
        "student_name": checker_student,
        "teacher_name": teacher,
        "forbid_phrases": case.get("forbid_phrases", []),
        "require_phrases": case.get("require_phrases", []),
        "reply_forbid": case.get("reply_forbid", {}),
        "reply_require": case.get("reply_require", {}),
        "allow_no_question": case.get("allow_no_question", False),
        "max_replies": case.get("max_replies"),
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
    parser.add_argument("--stage", choices=("leadin", "word", "sentence", "wrapup"),
                        action="append")
    parser.add_argument("--only", help="run one case ID")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--resume", type=pathlib.Path)
    args = parser.parse_args()

    batteries = load_cases()
    stages = set(args.stage or ("leadin", "word", "sentence", "wrapup"))
    selected = [
        (family, case)
        for family, cases in batteries.items()
        if FAMILIES[family]["stage"] in stages
        for case in cases
        if not args.only or case["id"] == args.only
    ]
    if not selected:
        parser.error("no selected L2 cases")

    print("Lesson flow: L2 lead-in -> word -> sentence -> wrap-up (no warm-up)")
    print(f"Prompt source: {PROMPT_DIR}")
    print(f"Forge modelName: {args.model}")
    for stage in ("leadin", "word", "sentence", "wrapup"):
        count = sum(FAMILIES[f]["stage"] == stage for f, _ in selected)
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
        print(f"Forge preflight failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    hashes = prompt_hashes()
    if args.resume:
        run_dir = args.resume.resolve()
        report_path = run_dir / "report.json"
        report = json.loads(report_path.read_text())
        if report["model"] != args.model or report["prompt_sha256"] != hashes:
            parser.error("model or prompt files changed; start a new run")
    else:
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = ROOT / "eval/runs" / f"l2_{args.model}_{stamp}"
        run_dir.mkdir(parents=True, exist_ok=False)
        report = {
            "model": args.model,
            "forge_picker_id": CATALOG_IDS.get(args.model, args.model),
            "lesson_flow": "lead-in -> word -> sentence -> wrap-up (no warm-up)",
            "started_at_utc": stamp,
            "prompt_sha256": hashes,
            "cases": {},
        }

    failures = []
    for family, case in selected:
        stage = FAMILIES[family]["stage"]
        case_dir = run_dir / stage
        case_dir.mkdir(parents=True, exist_ok=True)
        path = case_dir / f"{case['id']}.json"
        if args.resume and path.exists():
            transcript = json.loads(path.read_text())
            print(f"reusing {case['id']} ...", flush=True)
        else:
            print(f"running {case['id']} ...", flush=True)
            transcript = run_case(backend, family, case)
            path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2))
        issues = FAMILIES[family]["checker"](transcript)
        report["cases"][case["id"]] = {
            "family": family,
            "path": str(path.relative_to(ROOT)),
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
        (run_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))

    print(f"\nL2 result: {len(selected) - len(failures)}/{len(selected)} cases passed")
    print(f"Transcripts and report: {run_dir}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
