# L1 V4

Source: `main/prompts/l1` at commit `829e768bb58a7302ed6987867a36ccc9431419b3`.
This is a separate copy of that source, not a continuation of L1 V2.

Teaching changes from the source are:

1. Remove written laughter and cheering noises from spoken examples and forbid
   their generation in the common rule. Use normal warm words instead.
2. Wrap-up asks `So, what do you like?` Accept one food word and respond to the
   child's actual preference before the existing song handoff.
3. Vocabulary opens with a short first-sound bounce and the whole word.
   Later support uses one useful phoneme, cluster, chunk, or syllable rather
   than a compulsory full breakdown. Every repetition invitation puts the
   instruction before the final spoken target word. Questions are answered
   first; understandable attempts do not trigger unnecessary drills.

| Word | Opening bounce | Examples of targeted support |
| --- | --- | --- |
| apple (two syllables) | `/æ/ /æ/ apple` | `/æp/` or `/əl/`, then apple |
| bread | `/b/ /b/ bread` | `/b/ /rɛd/ bread` for joining help; one requested sound, then bread |
| juice | `/dʒ/ /dʒ/ juice` | `/dʒuː/` or `/s/`, then juice |

Separate units with spaces, not dots. `/dʒ/` is one phoneme, not two.
For a specific difficulty, model one useful unit or support group and immediately model
the whole word before any invitation or other speech. For example,
`/s/ juice. Your turn. Juice.`, not `/s/. Your turn. Juice.`
For "slower", use a smaller chunk, not a speed-change promise. Put
"Your turn" or "Now you try" before the final target word, never after it.
ASR substitutions can guide tentative support, not a definite diagnosis.
Silence or unclear ASR gets a neutral model. Accept understandable attempts;
do not count "I can't say apple" as success or a part attempt as a whole word.
These cues represent sounds, not alphabet letter names. Actual pronunciation
must be checked through the new TTS voice. Text eval cannot verify audio.

The lesson flow, tag vocabulary, and turn limits are retained. Vocabulary
handoff wording is now shorter and natural. Apple leads to games with apple,
not letter A. Bread now leads to games with bread, not letter B. The Boo
drinking destination is unchanged. Vocabulary actions play after all speech.
Warm-up, both sentence pages, lead-in placeholders and wrap-up are unchanged.

## Forge update

Latest handoff correction: re-paste ONLY the bread template. Its final line
is now `Let's play with bread.` Pronunciation support and all other teaching
behaviour are unchanged by this correction.

Latest bread joining-help change: re-paste ONLY
`word_teaching_rules_l1l2_bread.md`. For a likely bed-like repeat or joining
request, use `Listen. /b/ /rɛd/ bread. Your turn. Bread.` The chunks are a
practice split, not two syllables. Common rules and other words are unchanged.
Check the new chunk with your TTS voice; this revision was text-tested only.

For the sound-to-whole-word correction, update the common rule and all three
word templates. Apple now ends with `Let's play with apple.` Every sound or
sound group connects immediately to its whole word, including in final-turn
help, before the invitation or handoff. Other teaching decisions are unchanged.

For the 2026-10-23 natural-response follow-up, update ONLY the common rule
and apple, bread, and juice vocabulary templates. This distinguishes likely
ASR attempts from real comments/questions, offers one useful retry for partial
attempts, removes scripted victory/noise lines, and moves vocabulary actions
after speech. The existing IPA notation is retained; the user reports that
phoneme playback now works. No independent audio check was performed here.

For the 2026-10-23 first-sound/chunk revision, re-paste ONLY the common rule
and the apple, bread, and juice vocabulary templates from this folder.
The word openings now invite repetition rather than asking a preference
question. Other stage files, source handoffs, tag rules and turn limits are
unchanged. No changes are made to L2 V3.

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

Latest bread-game handoff correction: **21/21 focused bread Forge cases passed**.
Only the handoff and its example changed to `Let's play with bread.`
Model: `gpt5.6LunaChatModel`, through Prompt Forge. Local evidence with
hashes and transcripts: `eval/runs/l1_v4_bounce_20261023T103353Z/`.
This is the bread-only suite (19 generated conversations and two seeded-context
scenarios), not a full-lesson or TTS audio test. No Forge templates were deployed.

Earlier bread joining-help change: **21/21 focused bread Forge cases passed**.
See [results and limits](../../eval/L1_V4_BREAD_JOINING_EVAL_2026-10-23.md).

Earlier sound-to-word/ apple-game correction: **52/52 focused Forge cases passed**.
See [results and limits](../../eval/L1_V4_SOUND_WORD_LINK_EVAL_2026-10-23.md).

Earlier natural-response follow-up: **52/52 focused Forge scenarios passed**,
including 51 generated conversations and one seeded context contrast.
See [results and limits](../../eval/L1_V4_NATURAL_RESPONSE_EVAL_2026-10-23.md).

Earlier 2026-10-23 first-sound/chunk revision: **36/36 focused Forge cases passed**.
See [scope, iteration history and limitations](../../eval/L1_V4_BOUNCE_EVAL_2026-10-23.md).
This verifies text behaviour, not actual TTS pronunciation or learning outcomes.

For the current pronunciation policy, run `python3 eval/run_l1_v4_bounce.py`
for scope checks and checker fixtures. Add `--live` with `FORGE_TOKEN` in the
environment for 54 focused cases on `gpt5.6LunaChatModel` through Prompt Forge.
Use `--live --word bread` for the 21-case scope tested in this revision.
The older `run_l1_v4_forge.py` contains superseded full-decomposition and
small-unit-only expectations; do not use its pronunciation scores for this revision.
The runner saves prompt hashes, transcripts and failures under
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

Earlier adaptive syllable/phoneme revision: **42/42 cases pass** under the final
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
