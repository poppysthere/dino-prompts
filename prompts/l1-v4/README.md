# L1 V4

Source: `main/prompts/l1` at commit `829e768bb58a7302ed6987867a36ccc9431419b3`.
This is a separate copy of that source, not a continuation of L1 V2.

Only three changes are included:

1. Remove written laughter and cheering noises from spoken examples and forbid
   their generation in the common rule. Use normal warm words instead.
2. Wrap-up asks `So, what do you like?` Accept one food word and respond to the
   child's actual preference before the existing song handoff.
3. Vocabulary invitations can model sounds separated with three dots, then
   return to the whole word. The first invitation uses the model unless the
   child already said the target; a successful child is not asked to repeat.

| Word | TTS sound cues |
| --- | --- |
| apple | `a...p...uh...l` |
| bread | `b...r...e...d` |
| juice | `j...oo...s` |

These cues represent sounds, not alphabet letter names. Actual pronunciation
must be checked through the new TTS voice. Text eval cannot verify audio.

The source lesson flow, action tags, handoff lines, and turn limits are retained.
It includes warm-up, both sentence pages, and the source letter-practice handoffs.

## Forge update

Copy the common rule, three vocabulary prompts, wrap-up, warm-up, and both
sentence prompts from this folder. Warm-up and sentence changes only remove
the unwanted laughter/cheering examples. Sentence pre-video is unchanged.

Both lead-in files inherited from main are placeholders marked "Do not paste."
Keep the working lead-in content in Forge; these files cannot be evaluated as
teaching prompts until the real source is supplied.

## Evaluation

Run `python3 eval/run_l1_v4_forge.py --offline` for source checks and synthetic
checker validation. Run `python3 eval/run_l1_v4_forge.py` with `FORGE_TOKEN` in
the environment for 29 live cases on `gpt5.6LunaChatModel` through Prompt Forge.
The runner saves prompt hashes, source diffs, transcripts and failures under
`eval/runs/`. It does not deploy or edit Forge content.

2026-10-21: offline checks passed. After refreshing Forge authorization, the
initial live run passed 28/29 cases. The wrap-up silence case repeated the
question because the common silence ladder overrode the two-turn stage rule.
An explicit stage override fixed that conflict; all six wrap-up cases then
passed. Combined coverage is 29/29: 23 unchanged cases plus six wrap-up reruns.
The runner verified text and tags, not TTS audio. See
[`L1_V4_EVAL_2026-10-21.md`](../../eval/L1_V4_EVAL_2026-10-21.md) for evidence.
