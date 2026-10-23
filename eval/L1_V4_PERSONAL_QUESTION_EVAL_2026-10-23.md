# L1 V4 optional personal questions — 2026-10-23

Baseline: `f8a25fc`. Branch: `agent/l1-v4`.

## Scope

Apple, bread and juice vocabulary templates now allow one optional preference
question on reply 2 after an easy first word attempt. Questions are
`Do you like apples?`, `Do you like bread?`, and `Do you like juice?`.
This is not a pronunciation invitation and need not end in a target-word model.

Skip it after support/clarification, if the child already gave a preference,
or if available recent conversation already contains a food-preference question.
Respond to the answer and finish. Do not require a complete sentence, restart
a drill, ask why, or exceed four replies. Confusion and silence must not be
interpreted as yes. Questions and help requests still receive a response.

Common rules, openings, sound scaffolds, handoffs, action vocabulary and all
other teaching stages are unchanged. Re-paste only the three word templates.

## Evaluation and iteration

Backend: Prompt Forge / Azure OpenAI / `gpt5.6LunaChatModel`.
Local scope checks, checker fixtures and `git diff --check`: PASS.

The expanded suite has 78 cases: 55 generated conversations with scripted
student input and 23 seeded-teacher-context cases. Of the seeded cases, 21
place the optional question in history to test the response path whether or
not the model chooses that optional branch spontaneously. Two older seeded
contexts cover colour meaning and unsuccessful pronunciation support.
Seeded teacher lines are not model-generated evidence.

Initial run: 67/78 under the initial checker. It exposed late questions after
practice, restarted practice after an optional question, and a repeated
preference question from earlier-page history. One earlier-page case changed
the fixed opening. Three confusion replies were false positives: the checker
mistook `I asked if you like...` for asserting the child's preference.

The prompt now checks the personal-question state before the ordinary flow.
The checker distinguishes statements from explanations and accepts a whole-word
model for a general request to hear the word again. Earlier-page tests explicitly
mark the page boundary, while retaining the previous food question in history.

Revised full run: **77/78**. All 24 new personal-question/recent-history cases
passed. The sole failure was a curly apostrophe in an apple silence response,
unrelated to the personal-question branch. An unchanged-prompt isolated rerun
passed **1/1**. Every case therefore has a passing final-revision observation,
but this is NOT a clean 78/78 single run and does not establish punctuation
reliability. Production TTS punctuation normalization remains advisable.

Local ignored evidence directories (report, hashes, transcripts):

- Initial: `eval/runs/l1_v4_bounce_20261023T104247Z/`
- Revised full run: `eval/runs/l1_v4_bounce_20261023T104625Z/`
- Unchanged apple-silence rerun: `eval/runs/l1_v4_bounce_20261023T104924Z/`

README/report edits after testing do not change the tested teaching prompts.

## Reviewed examples

Generated easy-success path:

> Apple. Nice work. Do you like apples?[TEACHER_LISTEN][STUDENT_TALK]

After a seeded preference question and a request to hear apple again:

> Sure. Listen. /æ/ apple. Let's play with apple.[TEMPLATE_FINISH]

After a seeded juice preference question and `I like bananas.`:

> You like bananas. That is okay. Now let's drink like Boo.[TEACHER_DRINK_JUICE][TEMPLATE_FINISH]

With a recent banana-preference exchange present in earlier-page history,
the bread case finished without another question:

> Bread. Nice work. Let's play with bread.[TEACHER_APPLAUD][TEMPLATE_FINISH]

## Limits

These are synthetic text tests, not child comprehension, CEFR certification,
TTS audio, or whole-lesson naturalness measurements. Cross-word question
frequency can only use conversation actually supplied by Forge; without that
history, the prompt cannot guarantee lesson-wide spacing. No Forge templates
were deployed and no other level was changed.
