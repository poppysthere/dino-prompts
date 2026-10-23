# L1 V4 natural response and ASR intent — 2026-10-23

Baseline: `dbf2ad092d74d0c332c0a0e8c4f4f24bb19f2dbc`.
Branch: `agent/l1-v4`. Model: `gpt5.6LunaChatModel` through Prompt Forge,
provider `Azure OpenAI`.

## Changes

Only the common vocabulary guidance and apple/bread/juice word templates
changed. The previously working slash-delimited IPA and sound-bounce strategy
are retained. The user reports successful phoneme playback; this run did not
independently audition audio.

- Use last teacher task, recent context, apparent sound similarity, and
  communicative intent together. Do not classify by isolated keyword or
  sentence length alone.
- Distinguish likely partial attempts from recognisable complete approximations.
  Offer one helpful model instead of prematurely declaring whole-word success.
- Answer genuine questions, personal comments, needs, and explicit corrections.
  Short, ungrammatical speech may still be genuine communication.
- For ambiguous attempt-like ASR, avoid dictionary-topic detours and certain
  pronunciation diagnoses. Neutral modelling or a short clarification is allowed.
- Remove forced victory speeches, CRUNCH/glug/munch noises and action narration.
  Use short natural recasts and acknowledgements.
- Move ALL word-stage actions after spoken text. Preserve tag vocabulary,
  listening/control suffixes, and the final juice drinking action.
- Shorten handoffs without changing destinations: A practice, B practice,
  and drinking like Boo. Preserve the four-reply budget and early success exits.

Warm-up, lead-in placeholders, sentence templates, wrap-up, L2 and main are
unchanged. Scope is checked against the baseline, with tag-vocabulary and
destination assertions. The common changes are vocabulary-scoped.

## Verification

`python3 eval/run_l1_v4_bounce.py`: local scope and checker-fixture checks pass.
Python compilation and `git diff --check` pass.

Initial live run: **46/51**. Three repeated-silence cases fell back to the
common yes/no ladder. Two explicit single-sound requests received larger
chunks instead. Stage overrides and exact requested-sound guidance were
clarified; the expected responses were not relaxed to hide those failures.

Final live run: **52/52** focused scenarios pass automated checks.
51 are generated multi-turn conversations with scripted child messages.
One is a seeded context contrast: the harness inserts the teacher question
"What color is your dog?" so the same child token "black" is genuinely an
answer. That teacher question is NOT claimed as a model-generated output.
The subsequent response is generated live and checked.

Coverage includes the previous 36 cases, partial app/bre/jew attempts,
short real comments, genuine target-word questions, a request for water,
bed → black → brad, an explicit correction of the bed interpretation,
an unseen ju fragment, and the seeded one-word answer contrast.

Checks cover action suffix placement, terminal tags, target-last repetition,
IPA units, ordinary punctuation, no written laughter/action noises, no
unsupported speed promises or confident error diagnoses, no premature
partial-word success, selected semantic acknowledgements, and the turn cap.

Final local evidence:
`eval/runs/l1_v4_bounce_20261023T100236Z/report.json`, with prompt hashes and
individual transcript JSON files in that directory. Runtime artifacts remain
local under the existing ignored runs directory. README-only edits after the
run do not change any tested teaching prompt.

## Manually inspected contrast examples

After a bread repetition invitation, ASR `black`:

> Listen. Bread. Your turn. Bread.[TEACHER_LISTEN][STUDENT_TALK]

After the seeded colour question, child `black`:

> A black dog. Now you try. Bread.[TEACHER_LISTEN][STUDENT_TALK]

After `No, I mean my bed.`:

> Oh, your bed. I see. Listen. Bread. Your turn. Bread.[TEACHER_LISTEN][STUDENT_TALK]

After a successful bread attempt:

> Bread. Nice work. Let's play with B.[TEACHER_APPLAUD][TEMPLATE_FINISH]

## Limits

These are synthetic text cases and targeted checks, not proof of intent
classification accuracy on real child ASR, universal naturalness, or learning
effectiveness. Some sound hypotheses may be unhelpful even when their format
is valid. Human transcript sampling supplements the checks but is not an
independent scored study. No child recording, TTS audition or production
deployment was performed.

## Forge

Re-paste only the L1 V4 common rule and the three vocabulary templates.
No Forge configuration was changed by this runner.
