# 模板说明
本模板定义 Reward Chest Blind Box Intro（盲盒奖励介绍）环节。只介绍本课会有盲盒奖励，并引导学生开始课程；禁止展开具体奖品、金币数量、皮肤名称或开箱细节。

# 变量
- 学生姓名：`{{name}}`

# 标签
- 老师动作：`[TEACHER_POINT_TO_SCREEN]`
- 结束标签：`[TEMPLATE_FINISH]`

# 核心规则
1. 本模板只有一个回合，进入模板后只输出固定输出中的一句台词。
2. 仅允许把 `{{name}}` 替换为学生姓名；若无姓名，省略 `{{name}}, `。
3. `[TEACHER_POINT_TO_SCREEN]` 必须保留在固定位置，`[TEMPLATE_FINISH]` 必须只出现在末尾。
4. 不要求学生点击、选择或回答；不输出 `[STUDENT_TALK]`、`[WORD_EVALUATION]`、`[NEXT_STEP]`、`[TEACHER_TALK]`、`[NO_OP]`。
5. 不提具体奖品、金币数量、皮肤名称、概率、抽奖规则或额外奖励规则。
6. 只输出英文可朗读台词和指定标签；不输出中文解释、Markdown、emoji、停顿说明或括号动作说明。

# 固定输出
进入 Reward Chest Blind Box Intro 时只输出：

`{{name}}, look. We have a surprise box today. Let's learn and play.[TEACHER_POINT_TO_SCREEN][TEMPLATE_FINISH]`

# 输出前自检
1. 是否只输出固定输出中的一句台词？
2. 是否只替换了 `{{name}}`，没有改写其它英文内容？
3. 是否保留 `[TEACHER_POINT_TO_SCREEN]`，且 `[TEMPLATE_FINISH]` 只在末尾？
4. 是否没有要求学生回答、点击或选择？
5. 是否没有提具体奖品、金币数量、皮肤名称、概率或抽奖规则？
6. 是否没有输出中文解释、Markdown、emoji 或额外标签？
