#!/usr/bin/env python3
"""Eval runner: drives the case battery against a live model and checks every transcript.

For each page (pages.yaml) x case (cases_*.yaml):
  1. Compose the system prompt exactly like production: common rules (placeholders
     filled) + the page template.
  2. Play the scripted child turns against the model, collecting teacher replies.
  3. Save the transcript JSON and run the mechanical checker on it.

Usage:
  python3 eval/runner.py --backend mock                     # pipeline self-test, no network
  python3 eval/runner.py --backend forge --runs 10          # real model via Prompt Forge /debug
  python3 eval/runner.py --pages bread --cases l1-word-for-target,gibberish

Backends and their env vars: see backends.py.
Exit code: 0 = all cases pass, 1 = failures (details printed + saved to eval/runs/).
"""
import argparse
import datetime
import json
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import checker  # noqa: E402
from backends import make_backend  # noqa: E402

ROOT = pathlib.Path(__file__).parent.parent
UI_READY = "The UI is ready. Continue the lesson from where you left off,or start if nothing has begun yet."
MAX_REPLIES = 6  # hard safety cap per page


def fill(text: str, mapping: dict) -> str:
    for k, v in mapping.items():
        text = text.replace("{{" + k + "}}", str(v).strip())
    return text


def compose_system_prompt(page: dict, defaults: dict) -> str:
    common = (ROOT / defaults["common_prompt"]).read_text()
    template = (ROOT / page["template"]).read_text()
    mapping = dict(defaults.get("placeholders", {}))
    mapping["renderContent"] = page["render_content"]
    return fill(common, mapping).rstrip() + "\n\n" + fill(template, mapping).rstrip()


def run_case(backend, page: dict, case: dict, subs: dict) -> dict:
    messages = [{"role": "user", "content": UI_READY}]
    transcript = []
    turns = [fill_case(t, subs) for t in case["turns"]]
    turn_i = 0
    while True:
        reply = backend.chat(page["_system_prompt"], messages)
        messages.append({"role": "assistant", "content": reply})
        transcript.append({"role": "assistant", "text": reply})
        n_replies = sum(1 for m in transcript if m["role"] == "assistant")
        if "[TEMPLATE_FINISH]" in reply or "[NEXT_STEP]" in reply or n_replies >= MAX_REPLIES:
            break
        if turn_i < len(turns):
            child = turns[turn_i]
            turn_i += 1
        else:
            child = "The student has been silent for 5 seconds"
        messages.append({"role": "user", "content": child})
        transcript.append({"role": "user", "text": child})
    return {
        "word": page["word"],
        "opener": page["opener"],
        "finish_line": page["finish_line"],
        "case": case["id"],
        "accept_variants": [v for k, v in subs.items() if k == "WORD_MESSY"],
        "messages": transcript,
    }


def fill_case(turn: str, subs: dict) -> str:
    for k, v in subs.items():
        turn = turn.replace("{" + k + "}", v)
    return turn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default=None, help="mock | forge | openai (default: $EVAL_BACKEND or mock)")
    ap.add_argument("--pages", default=None, help="comma-separated page ids (default: all)")
    ap.add_argument("--cases", default=None, help="comma-separated case ids (default: all)")
    ap.add_argument("--runs", type=int, default=1, help="runs per case (sampling variance; use 10 for real models)")
    ap.add_argument("--pass-rate", type=float, default=0.9, help="min fraction of clean runs for a case to pass")
    args = ap.parse_args()

    manifest = yaml.safe_load((ROOT / "eval" / "pages.yaml").read_text())
    defaults = manifest["defaults"]
    want_pages = args.pages.split(",") if args.pages else list(manifest["pages"].keys())

    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT / "eval" / "runs" / run_id
    out_dir.mkdir(parents=True)

    results = []
    for page_id in want_pages:
        page = dict(manifest["pages"][page_id])
        page["_system_prompt"] = compose_system_prompt(page, defaults)
        battery = yaml.safe_load((ROOT / "eval" / page["cases"]).read_text())
        subs = battery["words"][page_id]
        cases = battery["cases"]
        if args.cases:
            want = set(args.cases.split(","))
            cases = [c for c in cases if c["id"] in want]
        backend = make_backend(args.backend, page)

        for case in cases:
            clean = 0
            all_violations = []
            for i in range(args.runs):
                transcript = run_case(backend, page, case, subs)
                fname = out_dir / f"{page_id}__{case['id']}__{i}.json"
                fname.write_text(json.dumps(transcript, ensure_ascii=False, indent=2))
                violations = checker.check(transcript)
                if not violations:
                    clean += 1
                else:
                    all_violations.append({"run": i, "violations": violations})
            ok = clean >= args.pass_rate * args.runs
            results.append({
                "page": page_id, "case": case["id"], "clean": clean, "runs": args.runs,
                "pass": ok, "violations": all_violations,
            })
            mark = "PASS" if ok else "FAIL"
            print(f"[{mark}] {page_id:8s} {case['id']:28s} {clean}/{args.runs} clean")
            for av in all_violations:
                for v in av["violations"]:
                    print(f"         run {av['run']}: {v}")

    (out_dir / "summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    failed = [r for r in results if not r["pass"]]
    print(f"\n{len(results) - len(failed)}/{len(results)} cases passed. Transcripts: {out_dir}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
