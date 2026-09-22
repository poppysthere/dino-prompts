# Dino Prompts

Version-controlled source of truth for the AI teacher prompts managed in Prompt Forge
(`ai-dino-prompt-forge-web` / prompt-forge-api).

Prompt Forge stores prompts in its own database with internal versioning; this repo mirrors
the latest reviewed text so changes are diffable and recoverable.

## Files → Prompt Forge codes

| File | Prompt Forge code | Used by |
|---|---|---|
| `prompts/l1/common_teaching_simple_rules.md` | `common_teaching_simple_rules` | L1 shared rules, ages 4-6, CEFR pre-A1 |
| `prompts/l1/warmup_teaching_rules_l1l2.md` | `warmup_teaching_rules_l1l2` | L1 Warm-Up |
| `prompts/l1/leadin_teaching_rules_l1_step_pre_video.md` | `leadin_teaching_rules_l1_step_pre_video` | L1 Lead-in before video |
| `prompts/l1/leadin_teaching_rules_l1_step_post_video.md` | `leadin_teaching_rules_l1_step_post_video` | L1 Lead-in after video |
| `prompts/l1/word_teaching_rules_l1l2_apple.md` | `word_teaching_rules_l1l2_apple` | L1 apple word teaching |
| `prompts/l1/word_teaching_rules_l1l2_juice.md` | `word_teaching_rules_l1l2_juice` | L1 juice word teaching |
| `prompts/l1/word_teaching_rules_l1l2_bread.md` | `word_teaching_rules_l1l2_bread` | L1 bread word teaching |
| `prompts/l1/sentence_teaching_rules_l1l2_pre_video.md` | `sentence_teaching_rules_l1l2_pre_video` | L1 sentence video intro |
| `prompts/l1/sentence_teaching_rules_l1l2_i_like_bread.md` | `sentence_teaching_rules_l1l2_i_like_bread` | `I like bread.` |
| `prompts/l1/sentence_teaching_rules_l1l2_i_dont_like_apples.md` | `sentence_teaching_rules_l1l2_i_dont_like_apples` | `I don't like apples.` |
| `prompts/l1/wrapup_teaching_rules_l1l2.md` | `wrapup_teaching_rules_l1l2` | L1 Chef Boo wrap-up |

## Placeholders

`{{roleDescription}}`, `{{renderContent}}`, `{{studentProfile}}`, `{{name}}`, `{{teacherName}}`
are filled by the backend at class time. Keep them intact.

## Design notes

- Target learner: 4-6 years old, CEFR pre-A1. Most spoken sentences are 1-6 words and no
  spoken sentence exceeds 8 words.
- Turn shape: answer or react to the child's meaning first, then give one clear next action.
- Questions are yes/no or two-choice. Open, abstract, prediction, and explanation questions are out.
- One supported retry only; silence never creates an extra loop.
- English only: respond to another language's meaning without echoing or translating it.

## Workflow

1. Edit the markdown here (or paste from chat after review).
2. Paste into Prompt Forge as a NEW version of the matching prompt code.
3. Test in the debug console (拼接 prompt with the common rules + placeholder replacement),
   then via classroom debug with real audio.
4. Only 设为生产最新版 after tests pass — it goes live to real students immediately.
5. Commit the change here with a note about what was fixed and why.
