# Prompt eval harness

Layered quality control for lesson templates. See repo README for the prompt files themselves.

## What's here

- `cases_word_teaching.yaml` — the case battery: scripted child-input sequences. Every real bug
  found in testing becomes a permanent regression case (id'd and dated in `desc`). Plus standard
  kid archetypes (shy, chatty, upset, curious, silent, gibberish...).
- `checker.py` — mechanical rule checker. Verifies the structural hard rules of the talk-first
  word-teaching templates on a transcript JSON. No LLM needed, zero false tolerance:
  - exactly one control tag per reply, at the end
  - fixed opener verbatim on reply 1, never repeated after
  - `[TEMPLATE_FINISH]` only in replies 3-4, always with the verbatim finish line,
    never as the first sentence of the turn
  - English-only teacher output (no CJK)
  - every `[STUDENT_TALK]` turn ends with the child's job (question / say-it call)
  - page length 3-4 replies; no repeated sentences; TTS safety (no naked letters);
    false-celebration floor check
- `fixtures/` — transcripts for testing the checker itself:
  - `bread_fail_20260711.json` — real production log from 2026-07-11 (opener-repeat bug). Checker must FAIL it.
  - `bread_good.json` — corrected version of the same session. Checker must PASS it.

## Usage

```bash
python3 eval/checker.py path/to/transcript.json
```

Transcript format: `{"word", "opener", "finish_line", "messages":[{"role","text"}]}`.

## Workflow

1. Every failure found (by testers or in production logs) → add a case to the YAML + a fixture if structural.
2. Every template change → run the battery before pasting into Prompt Forge.
3. A case passes only if the structural checks pass in >= 9/10 runs (sampling variance is real).

## Next steps (not built yet)

- `runner.py`: drive the case battery automatically against the Prompt Forge debug API
  (`POST /debug/stream` with the assembled system prompt), collect transcripts, run checker, report pass rates.
- LLM-as-judge pass for soft qualities: did the teacher answer the child's meaning? was the
  celebration matched to the child's energy? (mechanical checks can't judge warmth).
- Production log mining: run checker nightly over real conversation logs, flag violating sessions
  (see notes/dev_message_log_mining.md).
