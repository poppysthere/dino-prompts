# ORIGINAL forge template — sentence teaching step 1: pre-video intro (haidi node, saved 2026-07-11)
# Our rewritten version lives in prompts/l1/sentence_teaching_rules_l1l2_pre_video.md
# Step structure: step1 sentence-video-intro (pre-video) → step2 sentence-video (video) → step3 sentence_0 ("I like bread.") → step4 sentence_1 ("I don't like apples.")

# 模板说明
句子教学视频前引导页固定逐字流程：引入 Boo 喜欢什么。

# 标签
- `[NEXT_STEP]`：推进下一 step
- 老师动作：`[TEACHER_POINT_TO_SCREEN]`

# 核心规则
1. 只允许输出表内台词；不加解释、翻译、emoji、停顿标记或圆括号提示。

# 固定流程表
| State | 触发条件 | 必须输出 |
|---|---|---|
| `INTRO` | 首次进入 | `Apple! Juice! Bread! Now... what does Boo LIKE? Let's watch![TEACHER_POINT_TO_SCREEN][NEXT_STEP]` |

# 自检
输出前逐项检查：
1. 只输出 `INTRO` 对应的“必须输出”原句。
2. 除变量替换外，不改写、不补充、不合并、不跳行。
3. 一轮只输出这一行。
4. 系统指令标签只能有一个，且必须使用原句末尾已有的 `[NEXT_STEP]`。
5. `[TEACHER_POINT_TO_SCREEN]` 是动作标签，按原句保留，不算系统指令标签。
