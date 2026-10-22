# L1 V4

Source: `main/prompts/l1` at commit `829e768bb58a7302ed6987867a36ccc9431419b3`.
This is a separate copy of that source, not a continuation of L1 V2.

Teaching changes from the source are:

1. Remove written laughter and cheering noises from spoken examples and forbid
   their generation in the common rule. Use normal warm words instead.
2. Wrap-up asks `So, what do you like?` Accept one food word and respond to the
   child's actual preference before the existing song handoff.
3. Vocabulary invitations use IPA teaching units in separate `/ /` pairs:
   syllables for words with two or more syllables, phonemes for one-syllable
   words, then the whole word. The first invitation uses the model unless the
   child already made an understandable attempt. Targeted pronunciation help
   takes priority when requested or supported by reliable assessment.

| Word | TTS sound cues |
| --- | --- |
| apple (two syllables) | `/æp/ /əl/` |
| bread | `/b/ /r/ /ɛ/ /d/` |
| juice | `/dʒ/ /uː/ /s/` |

Separate units with spaces, not dots. `/dʒ/` is one phoneme, not two.
For a specific difficulty, model just that phoneme or syllable and blend back
to the word. For continued struggle, invite one small unit. Accept an
understandable approximation without drilling for perfection. Never infer an
exact sound error from ASR spelling alone or count "I can't say apple" as success.
These cues represent sounds, not alphabet letter names. Actual pronunciation
must be checked through the new TTS voice. Text eval cannot verify audio.

The source lesson flow, action tags, handoff lines, and turn limits are retained.
It includes warm-up, both sentence pages, and the source letter-practice handoffs.

## Forge update

For the 2026-10-22 punctuation-only revision, update the common rule, all three
word templates, warm-up, and both sentence-teaching templates. The stage-file
edits only replace punctuation in examples; their words, teaching decisions,
tag order, and IPA are unchanged. Wrap-up and sentence pre-video are unchanged.

For the adaptive syllable/phoneme revision, re-paste only the common rule and the apple, bread, and
juice vocabulary prompts. Other teaching templates are unchanged by this revision.

Copy the common rule, three vocabulary prompts, wrap-up, warm-up, and both
sentence prompts from this folder. Warm-up and sentence changes only remove
the unwanted laughter/cheering examples. Sentence pre-video is unchanged.

Both lead-in files inherited from main are placeholders marked "Do not paste."
Keep the working lead-in content in Forge; these files cannot be evaluated as
teaching prompts until the real source is supplied.

## Evaluation

Run `python3 eval/run_l1_v4_forge.py --offline` for source checks and synthetic
checker validation. Run `python3 eval/run_l1_v4_forge.py` with `FORGE_TOKEN` in
the environment for 46 live cases on `gpt5.6LunaChatModel` through Prompt Forge.
The runner saves prompt hashes, source diffs, transcripts and failures under
`eval/runs/`. It does not deploy or edit Forge content.

2026-10-22 punctuation-only revision: all **46 cases / 125 teacher replies**
passed the spoken-punctuation check, including 55 straight U+0027 apostrophes.
Full regression is **44/46**, not all green: apple/bread synthetic assessment
cases skipped focused help. No interaction rule was changed to fix those
out-of-scope failures. See
[`L1_V4_PUNCTUATION_EVAL_2026-10-22.md`](../../eval/L1_V4_PUNCTUATION_EVAL_2026-10-22.md).

Earlier phoneme-only IPA revision: offline checks and a fresh full Forge run passed,
**29/29 cases**, including all 18 vocabulary cases. See
[`L1_V4_IPA_EVAL_2026-10-21.md`](../../eval/L1_V4_IPA_EVAL_2026-10-21.md).
Actual TTS audio pronunciation remains untested.

Latest adaptive syllable/phoneme revision: **42/42 cases pass** under the final
checker, across three test groups with matching prompt hashes. One checker
false positive for a small-unit invitation after repeated silence was corrected;
that case also passed a fresh live rerun. See
[`L1_V4_ADAPTIVE_SOUND_EVAL_2026-10-21.md`](../../eval/L1_V4_ADAPTIVE_SOUND_EVAL_2026-10-21.md).
The lead-in placeholders remain excluded; this is not a complete lesson or
audio-pronunciation certification. Assessment-driven tests use synthetic
feedback, not actual child recordings or an integrated pronunciation scorer.

Earlier dot-format evaluation (superseded by the IPA revision): offline checks
passed. After refreshing Forge authorization, the
initial live run passed 28/29 cases. The wrap-up silence case repeated the
question because the common silence ladder overrode the two-turn stage rule.
An explicit stage override fixed that conflict; all six wrap-up cases then
passed. Combined coverage is 29/29: 23 unchanged cases plus six wrap-up reruns.
The runner verified text and tags, not TTS audio. See
[`L1_V4_EVAL_2026-10-21.md`](../../eval/L1_V4_EVAL_2026-10-21.md) for evidence.
