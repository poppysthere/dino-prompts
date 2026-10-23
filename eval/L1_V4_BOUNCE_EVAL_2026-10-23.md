# L1 V4 pronunciation revision — 2026-10-23

## Scope

Baseline: `b33ddefa9fa9a19949462b8670282a8737537c94` on `agent/l1-v4`.
Teaching edits are limited to the common vocabulary-pronunciation rules and
apple, bread, and juice word templates. Other stage files are byte-identical
to the baseline. Role, English-only policy, ordinary punctuation policy,
action/control tag rules, handoff lines, and page budgets are retained.

Agreed changes:

- First-sound bounce, whole word, instruction, final target word, then wait.
- Every repetition invitation ends its spoken text with the target word;
  no question-form repetition cue or instruction after that final model.
- Use one useful phoneme, cluster, chunk, or syllable for targeted support.
  No compulsory complete decomposition of every word.
- A request for slower speech receives a smaller model, not a speed promise.
- ASR substitutions guide tentative support, not certain error diagnoses.
  An isolated near-target transcription is not a new conversation topic.
- Answer questions first; accept understandable attempts; avoid correction
  loops. Final-turn help demonstrates briefly before the unchanged handoff.

## Verification

Runner: `eval/run_l1_v4_bounce.py`.
Model: `gpt5.6LunaChatModel`, provider `Azure OpenAI`, through Prompt Forge.
No production prompts were deployed or edited in Forge.

Local scope/tag/handoff assertions, checker fixtures, Python compilation,
and `git diff --check` passed.

Final live run: **36/36 cases passed** the focused automated checks.
Twelve scenarios for each of apple, bread, and juice:

1. Immediate target-word response.
2. Meaningful sentence using the word.
3. Understandable approximation.
4. Request to speak slowly.
5. Request for a specific sound.
6. Help request after a prior attempt.
7. Unclear transcription.
8. Ambiguous near-target ASR substitution.
9. Repeated silence.
10. Asking what to do.
11. Asking the teacher's name.
12. Request for help on the final allowed reply.

Final local evidence: `eval/runs/l1_v4_bounce_20261023T083258Z/` contains
`report.json`, prompt SHA-256 hashes, and all 36 conversation transcripts.
Runtime artifacts stay local under the repository's existing ignored runs
directory. A later README-only edit does not change the four tested prompts.

## Iteration and manual review

The first run passed 33/36 under the initial checker. It exposed unclear
repetition instructions and an extra practice turn on a terminal help request.
Transcript inspection also found premature success for ambiguous ASR; a
new assertion was added rather than treating those earlier passes as proof.

The second run passed 36/36 under that checker, but transcript review found
`A cozy bed` after the bread attempt was transcribed as bed. The final common
rule and checker now prevent echoing those isolated ambiguous substitutions
as an unrelated topic. The entire 36-case suite was then run again.

Final bread example, after ASR `bed`:

> I hear you. Let's try the beginning. /br/. Your turn. Bread.[TEACHER_LISTEN][STUDENT_TALK]

Final apple example, after a request for slower speech:

> Okay. Let's try the beginning. /æp/. Your turn. Apple.[TEACHER_LISTEN][STUDENT_TALK]

These are recorded outputs, not guarantees about every future generation.

## Limits

This is a focused vocabulary text regression, not a full-lesson evaluation
or independent naturalness assessment. ASR inputs are synthetic. No child
audio, real pronunciation scorer, TTS audition, or learning-outcome trial was
used. Correct IPA text does not certify correct audio or intonation.
The existing lead-in placeholders and legacy letter-practice handoffs remain
unchanged, outside this pronunciation-only revision.

## Forge update

Re-paste only `prompts/l1-v4/common_teaching_simple_rules.md` and the three
`word_teaching_rules_l1l2_apple.md`, `word_teaching_rules_l1l2_bread.md`, and
`word_teaching_rules_l1l2_juice.md` files. No L2 files were changed.
