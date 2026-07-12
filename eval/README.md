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

# real run against the same model the app uses (Prompt Forge /debug endpoint):
export FORGE_BASE_URL=http://<forge-host>/api FORGE_EMAIL=... FORGE_PASSWORD=...
export FORGE_PROVIDER=... FORGE_MODEL=...        # as shown in the forge model picker
python3 eval/runner.py --backend forge --runs 10  # pass = >=9/10 clean per case

# judge the transcripts with a strong model (OpenAI-compatible endpoint):
export EVAL_API_BASE=... EVAL_API_KEY=... EVAL_MODEL=...
python3 eval/judge.py eval/runs/<run_id>/ --backend openai

# check one transcript by hand:
python3 eval/checker.py path/to/transcript.json
```

Deps: `pip3 install pyyaml` (runner/judge; checker is stdlib-only).

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
