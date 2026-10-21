# L1 V4 adaptive pronunciation — 2026-10-21

## Teaching behavior

- Two or more syllables: model syllables, then the whole word. Apple uses
  `/æp/ /əl/ apple`, not four separate phonemes by default.
- One syllable: model phonemes, then the word. Bread uses `/b/ /r/ /ɛ/ /d/`;
  juice uses `/dʒ/ /uː/ /s/`.
- Specific difficulty: model the requested or reliably identified phoneme or
  syllable, then blend back to the word. One correction at a time.
- Continued struggle: invite one manageable part, not the whole word again.
  Acknowledge the part attempt accurately, then gently model the word.
- Understandable approximation: recast warmly and continue without drilling
  for perfection. A current request for help takes priority over success.
- Never diagnose an exact pronunciation error from ASR spelling alone.
  "I can't say apple" is a request for help, not a successful attempt.

Only the common pronunciation policy and three word templates change in this
revision. Existing openings, handoffs, action tags, and turn budgets remain.
The word-template decision rules were reconciled so old games and automatic
success do not bypass pronunciation help.

## Verification

Prompt Forge, Azure OpenAI, model `gpt5.6LunaChatModel`.
Final result: **42/42 cases pass** under the final checker, with the tested
prompt hashes verified against the saved common and stage templates.

| Group | Cases | Final result |
| --- | ---: | --- |
| Apple: ordinary teaching, syllables, specific sound, specific syllable, continued struggle, unclear ASR, help after a word attempt, approximation, synthetic assessment | 13 | 13 pass |
| Bread and juice: ordinary teaching, sound help, approximation, synthetic assessment | 18 | 18 pass |
| Existing wrap-up, warm-up, sentence introduction and sentence pages | 11 | 11 pass |

Earlier development runs exposed missing default models, automatic handoffs
that ignored help, and unclear practice invitations. A manual transcript check
also exposed a whole-word demand after a part-only request; the checker now
tests that explicitly, together with false whole-word praise.

The final grouped run originally reported 41/42: the checker incorrectly
required blending back to the whole word in a small-unit-only invitation after
repeated silence. Such an invitation is intended adaptive support. The checker
was corrected for that context; all 42 saved transcripts were rechecked, and
the bread-silence case also passed a fresh live rerun without prompt changes.
Repeating the same focused IPA unit is allowed; adding unrelated units is not.

Offline tests include valid and deliberately invalid IPA, default versus
focused models, clear practice instructions, premature handoffs, full-word
demands after a part-only request, and false praise for a part-only attempt.

## Observed examples

After "The last part of apple is hard":
`The last part is hard. Listen. /əl/. Apple. Your turn. Apple.`

After "I still can't. Can I try just the first bit?":
`Yes, try the first bit. /æp/. Your turn.`

After the child then tries `ap`:
`That was the first bit! Listen: apple!`
The source handoff follows; the child is not falsely credited with a whole word.

## Evidence and limits

Local run folders under `eval/runs/` (ignored by Git):

- `l1_v4_20261021T105623778634Z` — 13 apple cases.
- `l1_v4_20261021T105623515846Z` — 18 bread/juice cases; original report retains
  the checker false positive described above.
- `l1_v4_20261021T105619860867Z` — 11 other-stage regression cases.
- `l1_v4_20261021T105823166228Z` — fresh bread-silence rerun, 1/1 pass.

These are text-and-flow tests, not audio evaluation. The three assessment
cases inject synthetic trusted feedback to test the branch; they do not
establish that Forge supplies real pronunciation feedback. Without such input,
use explicit child requests and neutral models, not invented sound diagnoses.
TTS syllable/phoneme pronunciation still needs listening checks.

Both lead-in files remain source placeholders and are excluded. This report
does not certify a complete lesson, all possible interactions, or all longer
words: apple is the implemented multisyllable target. The common policy covers
longer words, but any new word template needs its own checked IPA syllable map.

For Forge, re-paste the common rule and all three vocabulary templates together.
No Forge lesson content is deployed by the harness.
