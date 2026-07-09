# Dino Prompts

Version-controlled source of truth for the AI teacher prompts managed in Prompt Forge
(`ai-dino-prompt-forge-web` / prompt-forge-api).

Prompt Forge stores prompts in its own database with internal versioning; this repo mirrors
the latest reviewed text so changes are diffable and recoverable.

## Files → Prompt Forge codes

| File | Prompt Forge code | Used by |
|---|---|---|
| `prompts/common_teaching_simple_rules.md` | `common_teaching_simple_rules` | Prepended to all lesson stage templates (公共规则) |
| `prompts/warmup_teaching_rules_l1l2.md` | `warmup_teaching_rules_l1l2` | Warm-Up stage, Level 1-2 (ages 4-6, CEFR pre-A1) |

## Placeholders

`{{roleDescription}}`, `{{renderContent}}`, `{{studentProfile}}`, `{{name}}`, `{{teacherName}}`
are filled by the backend at class time. Keep them intact.

## Design notes

- Target learner: 4-6 years old, CEFR pre-A1. Very short sentences, simplest words; fun comes
  from performance (sound effects, silliness, pretend actions), not vocabulary.
- Turn shape: CATCH (react to the child's exact words) → FOLLOW (child's topic) or STEP (checklist).
- FOLLOW budget: max 2 per warm-up, never 2 in a row — student-centered but always finishes.
- Hard guarantees: one control tag per reply ([STUDENT_TALK] / [TEMPLATE_FINISH]); after the
  READY question the next turn always ends the template; 2 failed tries on an item → skip it.
- English only: never echo or translate Chinese; show meaning by acting it out.

## Workflow

1. Edit the markdown here (or paste from chat after review).
2. Paste into Prompt Forge as a NEW version of the matching prompt code.
3. Test in the debug console (拼接 prompt with the common rules + placeholder replacement),
   then via classroom debug with real audio.
4. Only 设为生产最新版 after tests pass — it goes live to real students immediately.
5. Commit the change here with a note about what was fixed and why.
