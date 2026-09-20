#!/usr/bin/env python3
"""Run the GitHub L3 prompt battery on Prompt Forge's GPT-5.6 Luna model.

No prompt is changed or deployed in Forge. The stage runners send the local
common L3 rule plus each local stage template to Forge's debug endpoint.
Credentials come only from the process environment, never from this file.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import urllib.request

import yaml

from backends import ForgeBackend


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_BASE = "http://dino-test-alb-2087276790.ap-southeast-1.elb.amazonaws.com/cms/api"
# /debug expects the provider's configured modelName, while the Forge model
# picker exposes its separate catalog ID. Keep both names explicit.
DEFAULT_MODEL = "gpt5.6LunaChatModel"
CATALOG_IDS = {DEFAULT_MODEL: "gpt-5.6-luna"}
STAGES = {
    "warmup": ("run_warmup_l3.py", "cases_warmup_l3.yaml"),
    "leadin": ("run_leadin_l3.py", "cases_leadin_l3.yaml"),
    "word": ("run_word_l3.py", "cases_word_l3.yaml"),
    "sentence": ("run_sentence_l3.py", "cases_sentence_l3.yaml"),
}


def cases_for(stage):
    data = yaml.safe_load((ROOT / "eval" / STAGES[stage][1]).read_text())
    return [case for group in data.values() for case in group]


def prompt_hashes():
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT / "prompts/l3").glob("*.md"))
    }


def check_model(backend, model):
    """Fail before paying for a test if Forge does not expose this model."""
    request = urllib.request.Request(
        f"{backend.base}/classroom-debug/models",
        headers={"Authorization": backend.token},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("code") != 200:
        raise RuntimeError(f"Forge model lookup failed (code {result.get('code')})")
    models = result.get("data") or []
    available = {
        value
        for item in models
        for value in (item.get("id"), item.get("cmsModel"), item.get("classModel"))
        if value
    }
    catalog_id = CATALOG_IDS.get(model, model)
    if catalog_id not in available:
        raise RuntimeError(f"Forge does not list model {catalog_id!r}; available IDs: {sorted(available)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Forge model ID")
    parser.add_argument("--stage", choices=STAGES, action="append",
                        help="run only this stage; repeat for multiple stages")
    parser.add_argument("--only", help="run one case ID, found in the selected stages")
    parser.add_argument("--plan", action="store_true", help="show cases without calling Forge")
    parser.add_argument("--resume", type=pathlib.Path,
                        help="continue a partial run without repeating saved cases")
    args = parser.parse_args()
    if args.resume and args.only:
        parser.error("--resume cannot be combined with --only")

    selected = list(dict.fromkeys(args.stage or STAGES))
    selected_cases = {
        stage: [c for c in cases_for(stage) if not args.only or c["id"] == args.only]
        for stage in selected
    }
    selected_cases = {stage: cases for stage, cases in selected_cases.items() if cases}
    if not selected_cases:
        parser.error(f"no L3 case matches {args.only!r}")
    print(f"Prompt source: {ROOT / 'prompts/l3'}", flush=True)
    print(f"Forge /debug modelName: {args.model}", flush=True)
    print(f"Forge picker ID: {CATALOG_IDS.get(args.model, args.model)}", flush=True)
    for stage, cases in selected_cases.items():
        print(f"  {stage}: {len(cases)} cases", flush=True)
    print(f"Total: {sum(map(len, selected_cases.values()))} cases", flush=True)
    if args.plan:
        return 0

    if not os.environ.get("FORGE_TOKEN") and not (
        os.environ.get("FORGE_EMAIL") and os.environ.get("FORGE_PASSWORD")
    ):
        parser.error("Forge authentication missing: set FORGE_TOKEN or FORGE_EMAIL + FORGE_PASSWORD")

    env = os.environ.copy()
    env.setdefault("FORGE_BASE_URL", DEFAULT_BASE)
    env.setdefault("FORGE_PROVIDER", "Azure OpenAI")
    env["FORGE_MODEL"] = args.model
    try:
        # ForgeBackend handles the existing login flow. Pass its token to every
        # child runner so we authenticate once and never print the credential.
        prior = {key: os.environ.get(key) for key in ("FORGE_BASE_URL", "FORGE_PROVIDER", "FORGE_MODEL")}
        os.environ.update({key: env[key] for key in prior})
        backend = ForgeBackend()
        check_model(backend, args.model)
        env["FORGE_TOKEN"] = backend.token
    except Exception as exc:
        print(f"Forge preflight failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        for key, value in prior.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    if args.resume:
        run_dir = args.resume.resolve()
        report = json.loads((run_dir / "report.json").read_text())
        if report["model"] != args.model or report["prompt_sha256"] != prompt_hashes():
            parser.error("model or prompt files differ from the saved run; start a new run")
    else:
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = ROOT / "eval/runs" / f"l3_{args.model}_{stamp}"
        run_dir.mkdir(parents=True, exist_ok=False)
        report = {
            "model": args.model,
            "forge_picker_id": CATALOG_IDS.get(args.model, args.model),
            "backend": "Prompt Forge /debug",
            "provider": env["FORGE_PROVIDER"],
            "started_at_utc": stamp,
            "prompt_sha256": prompt_hashes(),
            "stages": {},
        }
    for stage, cases in selected_cases.items():
        stage_dir = run_dir / stage
        previous = report["stages"].get(stage, {})
        if (args.resume and previous.get("exit_code") == 0
                and previous.get("saved_transcripts") == len(cases)):
            print(f"\n=== {stage} already clean; skipping ===", flush=True)
            continue
        command = [sys.executable, str(ROOT / "eval" / STAGES[stage][0]),
                   "--model", args.model, "--run-dir", str(stage_dir)]
        if args.only:
            command.extend(["--only", args.only])
        if args.resume:
            command.append("--skip-existing")
        print(f"\n=== {stage} ({len(cases)} cases) ===", flush=True)
        with (run_dir / f"{stage}.log").open("a" if args.resume else "w") as log:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in process.stdout:
                print(line, end="", flush=True)
                log.write(line)
            exit_code = process.wait()
        report["stages"][stage] = {
            "expected_cases": len(cases),
            "saved_transcripts": len(list(stage_dir.glob("*.json"))) if stage_dir.exists() else 0,
            "exit_code": exit_code,
        }
        (run_dir / "report.json").write_text(json.dumps(report, indent=2))

    failures = [stage for stage, result in report["stages"].items()
                if result["exit_code"] != 0 or result["saved_transcripts"] != result["expected_cases"]]
    print(f"\nL3 result: {len(selected_cases) - len(failures)}/{len(selected_cases)} stages clean")
    print(f"Transcripts and report: {run_dir}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
