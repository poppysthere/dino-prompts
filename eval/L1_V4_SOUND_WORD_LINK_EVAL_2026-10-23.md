# L1 V4 sound-to-word link and apple games — 2026-10-23

Baseline: `ba8caeed1711de52f153e2a69ff45bf11ecd09aa`.
Branch: `agent/l1-v4`.

## Narrow changes

- Apple handoff is now exactly `Let's play with apple.`, not letter A.
  Bread and juice handoffs are unchanged by this correction.
- Every IPA sound or consecutive sound group is immediately followed by
  the whole target word BEFORE instructions, praise, actions or a handoff.
  Example: `/s/ juice. Your turn. Juice.`
- This applies to all three word templates, including final-turn help.
  The final target word remains last in repetition speech.
- Do not embed IPA in explanatory prose such as `The /s/ sound is hard`.
  It would be another isolated spoken cue even when a correct model follows.
- Existing IPA notation, intent handling, reply limits, action suffix rules,
  other stage templates, L2, and main are unchanged.

## Tests

Local scope/checker fixtures and `git diff --check`: PASS.
The checker rejects a cue separated from its whole word by an invitation,
praise, a handoff, or explanatory prose. It checks every cue/group, not just
the final occurrence.

First full Forge run: **50/52**. One reply omitted the listening tag; the
unchanged-prompt isolated rerun passed. Another used explanatory
`The /s/ sound is tricky` before a correct model. Explicitly disallowing
IPA in explanations addressed that sound-link loophole.

Final full Forge run: **52/52** on `gpt5.6LunaChatModel` / Azure OpenAI.
Evidence: local ignored directory
`eval/runs/l1_v4_bounce_20261023T101650Z/` contains prompt hashes,
`report.json`, and transcripts. README-only edits after this run do not
alter any tested teaching prompt.

The suite contains 51 generated conversations with scripted child messages
plus one seeded colour-question context contrast, as documented in
`L1_V4_NATURAL_RESPONSE_EVAL_2026-10-23.md`.

Manually inspected final output for a bread sound request:

> Let's try. /r/ bread. Your turn. Bread.[TEACHER_LISTEN][STUDENT_TALK]

Final-turn juice help:

> Let's try this part. /dʒuː/ juice. Now let's drink like Boo.[TEACHER_DRINK_JUICE][TEMPLATE_FINISH]

This is text/flow verification, not an audio or real-child outcome test.
No live Forge templates were deployed. Re-paste the common rule and all
three L1 V4 word templates.
