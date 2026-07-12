#!/usr/bin/env python3
"""LLM judge: grades transcripts for the soft qualities the mechanical checker can't see.

The checker proves structure; the judge grades soul:
  - did the teacher react to the child's actual words (content, not category)?
  - was every celebration honest?
  - did invites stay playful and varied (games, not drills)?
  - was language simple enough for pre-A1?
  - open human feedback items (eval/feedback.yaml, status: open) become extra watch items.

Usage:
  python3 eval/judge.py eval/runs/<run_id>/            # judge a whole run dir
  python3 eval/judge.py transcript.json --backend openai
  python3 eval/judge.py transcript.json --backend mock  # pipeline self-test, no network

Use a STRONG model for judging (not the small teaching model):
  openai backend: EVAL_API_BASE / EVAL_API_KEY / EVAL_MODEL
  forge backend:  FORGE_* vars with a big model selected
Exit code: 0 = all judged transcripts pass, 1 = failures.
"""
import argparse
import json
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from backends import make_backend  # noqa: E402

ROOT = pathlib.Path(__file__).parent.parent

RUBRIC = [
    ("content-reaction", "Every teacher reply reacts to what the child ACTUALLY said (their words, question, or feeling) before moving on. Generic praise alone ('good', 'that's okay') without naming their content fails."),
    ("honest-celebration", "The teacher only celebrates 'you said it' when the child really made an English try at the target. Praising effort is fine; pretending is not."),
    ("playful-variety", "Invites are tiny games (count-down, say it big, chant), and no two teacher replies in a row have the same shape or repeat the same praise phrase."),
    ("simple-language", "Only words a pre-A1 4-6 year old knows. Sentences 3-8 words. No explanations, no meta-talk about words or grammar."),
    ("one-question", "At most one question per teacher reply."),
    ("meaning-answer", "When the child speaks another language, the teacher answers the MEANING in easy English, never echoes or translates the other language."),
    ("energy-match", "Tone matches the child: soft for shy/upset (no shouting, no games when crying), big for a loud kid."),
]


def load_watch_items():
    fb = yaml.safe_load((ROOT / "eval" / "feedback.yaml").read_text())
    return [
        (it["id"], f"HUMAN WATCH ITEM ({it['date']}, {it['page']}): {it['observation']}")
        for it in fb["items"] if it.get("status") == "open"
    ]


def build_judge_prompt(transcript: dict, criteria) -> str:
    convo = "\n".join(f"{m['role'].upper()}: {m['text']}" for m in transcript["messages"])
    crit_text = "\n".join(f"- {cid}: {desc}" for cid, desc in criteria)
    return f"""You are a strict but fair QA reviewer for a voice-based 1-on-1 English class for children aged 4-6 (CEFR pre-A1).
The teacher is an AI avatar teaching the target word/sentence: "{transcript['word']}".
Below is a real class transcript (USER = child via messy speech recognition, ASSISTANT = teacher).

Judge the TEACHER only, against each criterion. The child can do no wrong.

Criteria:
{crit_text}

Transcript:
{convo}

Reply with ONLY a JSON object, no markdown fences:
{{"verdicts": [{{"criterion": "<id>", "pass": true/false, "note": "<one short sentence, cite the exact teacher line if failing>"}}],
 "overall_pass": true/false,
 "summary": "<two sentences: what a real child would have felt in this class, and the single most important improvement>"}}
overall_pass is false if ANY criterion fails."""


class MockJudgeBackend:
    def chat(self, system_prompt, messages):
        # self-test: pass everything
        crit_ids = [cid for cid, _ in RUBRIC]
        return json.dumps({
            "verdicts": [{"criterion": c, "pass": True, "note": "mock"} for c in crit_ids],
            "overall_pass": True,
            "summary": "Mock judge: pipeline self-test only. Use a real backend for actual judging.",
        })


def judge_one(backend, transcript, criteria):
    prompt = build_judge_prompt(transcript, criteria)
    raw = backend.chat("You are a precise QA grader. Output only valid JSON.", [{"role": "user", "content": prompt}])
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").lstrip("json").strip()
    return json.loads(raw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="transcript .json or a runs/<id>/ directory")
    ap.add_argument("--backend", default=None, help="mock | forge | openai")
    args = ap.parse_args()

    target = pathlib.Path(args.target)
    files = sorted(target.glob("*__*.json")) if target.is_dir() else [target]
    if not files:
        print("no transcripts found")
        sys.exit(1)

    criteria = RUBRIC + load_watch_items()
    backend_name = args.backend or "mock"
    backend = MockJudgeBackend() if backend_name == "mock" else make_backend(backend_name)

    report, failed = [], []
    for f in files:
        transcript = json.loads(f.read_text())
        verdict = judge_one(backend, transcript, criteria)
        verdict["file"] = f.name
        report.append(verdict)
        mark = "PASS" if verdict.get("overall_pass") else "FAIL"
        print(f"[{mark}] {f.name}")
        if not verdict.get("overall_pass"):
            failed.append(f.name)
            for v in verdict.get("verdicts", []):
                if not v.get("pass"):
                    print(f"         {v['criterion']}: {v['note']}")

    out = (target if target.is_dir() else target.parent) / "judge_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n{len(files) - len(failed)}/{len(files)} transcripts passed judge. Report: {out}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
