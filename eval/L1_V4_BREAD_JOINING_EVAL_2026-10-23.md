# L1 V4 bread joining support — 2026-10-23

Baseline: `83a3b5a`. Branch: `agent/l1-v4`.

## Change

Only the bread teaching prompt changes. Likely bed-like repetition attempts
and explicit joining-help requests use:

> Listen. /b/ /rɛd/ bread. Your turn. Bread.

The support group connects immediately to the whole word. Bread remains one
syllable; no letter names, extra "buh", or written "read" cue is introduced.
An unsuccessful /br/ model can switch to this scaffold. Explicit requests for
one isolated sound still get that sound plus bread. The opening bounce,
handoff, turn limits, tags, common rules, other words and other levels stay
unchanged. ASR text suggests possible support, not a definitive diagnosis.

## Verification

- Local scope checks, checker fixtures and `git diff --check`: PASS.
- Prompt Forge, Azure OpenAI, `gpt5.6LunaChatModel`: **21/21 bread cases passed**.
- 19 generated conversations with scripted student messages and two seeded
  teacher-context scenarios. Seeded replies are not model-generated evidence.
- Coverage includes joining requests, switching after /br/, bed-like attempts,
  isolated-sound requests, silence, help, real questions and topic correction.
- The expanded full suite has 54 cases; this revision ran only the 21 bread
  cases. It does not claim a fresh full-suite or whole-lesson pass.

Evidence: local ignored directory
`eval/runs/l1_v4_bounce_20261023T102409Z/` contains the report, prompt hashes,
and per-case transcripts. Later README/checker-fixture edits do not change
the evaluated teaching prompt.

Manually reviewed joining-help response:

> Listen. /b/ /rɛd/ bread. Your turn. Bread.[TEACHER_LISTEN][STUDENT_TALK]

After the child clarified "No, I mean my bed.", the model responded:

> Oh, your bed. I understand. Listen. Bread. Your turn. Bread.[TEACHER_LISTEN][STUDENT_TALK]

This acknowledges the topic rather than diagnosing a pronunciation error.
It remains a brief return to practice, not an extended conversation.

No TTS audio or real-child learning outcome was tested. Audition /rɛd/ in
the actual voice. No Forge templates were deployed; re-paste only the bread
template if the previous common/word updates are already installed.
