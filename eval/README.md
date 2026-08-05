# Prompt eval pipeline

Automated version of the manual loop from the July 2026 testing week: simulate the child,
check hard rules, judge soft quality, feed in human classroom findings — and keep a human
on the approve button for every template change.

```
                 ┌─────────────────────────────────────────────┐
                 │  human tests in the real app classroom       │
                 │  (TTS sound, animations, ASR, kid feel)      │
                 └───────────────┬─────────────────────────────┘
                                 │ observations
                                 ▼
   feedback.yaml ──open items──► judge.py (extra watch items)
        │
        └─encoded──► checker.py rules + cases_*.yaml regression cases
                                 ▲
 pages.yaml ─► runner.py ─► transcripts (eval/runs/) ─► checker.py + judge.py ─► report
                                 │
                        template edit proposed ─► HUMAN approves diff ─► commit ─► re-paste to forge
```

## Pieces

- `pages.yaml` — per-page manifest: template file, verbatim opener/finish lines, renderContent.
- `cases_word_teaching.yaml` — scripted child inputs. Every real bug = a permanent regression case.
- `runner.py` — composes the production system prompt (common rules + template), plays each case
  against the model, saves transcripts, runs the checker. `--backend mock|forge|openai`.
- `checker.py` — mechanical hard rules (tags, opener, page length, English-only, TTS safety:
  no dashes/ellipses/naked letters, listen pose, honest celebration...). Zero LLM, zero tolerance.
- `judge.py` — a STRONG model grades soft quality: reacts to child's content, honest celebration,
  playful variety, simple language, meaning-answering, energy match. Open items from
  `feedback.yaml` are appended as watch items, so human observations steer machine review.
- `feedback.yaml` — the human classroom log. Device-only findings (TTS prosody, animation tags,
  ASR quirks) can ONLY come from here; each item is open / encoded / fixed.
- `fixtures/` — transcripts that test the checker itself (a real failing prod log + its corrected twin).

## Usage

```bash
# pipeline self-test, no network:
python3 eval/runner.py --backend mock

# real run against the same model the app uses (Prompt Forge /debug endpoint).
# Working values as of 2026-07-12 (test env):
export FORGE_BASE_URL=http://dino-test-alb-2087276790.ap-southeast-1.elb.amazonaws.com/cms/api
export FORGE_EMAIL=... FORGE_PASSWORD=...
export FORGE_PROVIDER="Azure OpenAI" FORGE_MODEL="gpt-5.4-mini"   # the model the app runs
python3 eval/runner.py --backend forge --runs 10  # pass = >=9/10 clean per case

# judge the transcripts with a strong model (OpenAI-compatible endpoint):
export EVAL_API_BASE=... EVAL_API_KEY=... EVAL_MODEL=...
python3 eval/judge.py eval/runs/<run_id>/ --backend openai

# direct Azure OpenAI run for the language-rescue experiment:
export AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com
export AZURE_OPENAI_API_KEY=...  # local shell only; never commit it
export AZURE_OPENAI_API_VERSION=2025-04-01-preview
export AZURE_OPENAI_DEPLOYMENT=gpt-5.4-mini
export AZURE_OPENAI_TIMEOUT=180
python3 eval/run_word_language_rescue.py

# check one transcript by hand:
python3 eval/checker.py path/to/transcript.json
```

Deps: `pip3 install pyyaml` (runner/judge; checker is stdlib-only).

If the machine you run on cannot reach the forge ALB directly (network policy), there is a
fallback: serve the repo with `python3 eval/_cors_server.py 8766` and drive the same /debug
calls from a browser page that CAN reach it (the forge login page works as a host). The
first live battery (`eval/runs/live_bread_20260712*`) was run this way.

## First live battery — bread, gpt-5.4-mini, 2026-07-12

17 cases, real model: **7/17 → 17/17 in three run-check-fix iterations.** Real bugs it caught
(all fixed in the templates, mirrored to apple/juice, logged as fb-013..fb-018):
- repeated silences made the model invite forever and never finish the page (STOP CHECK added),
- a child who said the word instantly was later consoled as if they had failed,
- give-up turns jumped to the handover line with no warm sentence first,
- say-it invites phrased as questions ("Can you say bread?"),
- comfort turns for a crying child repeated the same sentence three times.

## The workflow (human on the approve button)

1. **Template change** → run the battery (`runner.py --runs 10`) → checker + judge must pass
   before anything is pasted into Prompt Forge.
2. **Human classroom test** → observations go into `feedback.yaml`:
   - structural → new checker rule + regression case (status: encoded)
   - device-only or fuzzy → stays open → judge watches for it on every future run
3. **Failure found by the pipeline** → a fix is drafted, the full battery re-run proves the fix
   doesn't break anything else → a human reads the diff and approves → commit → re-paste.
4. Nothing auto-deploys. Ever.

## Not yet built

- CI gate (GitHub Action running `runner.py --backend forge` on every prompt commit).
- Sentence-page cases (`cases_sentence_teaching.yaml`) — word cases exist; sentence pages need
  their own battery including the "I like apples" don't-trap.
- Whole-lesson runs (page-to-page variety judging needs multi-page transcripts).
- Production log mining (run checker nightly over real class logs — see notes/dev_message_log_mining.md).
