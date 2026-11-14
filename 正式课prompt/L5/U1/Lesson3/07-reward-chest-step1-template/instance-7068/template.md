# 模板说明
Reward Chest 固定输出本课第一段奖励提示词，不做奖励类型判断。

# 变量
- 学生姓名：`{{name}}`

# 标签
- `[NO_OP]`

# 固定输出
进入 Reward Chest 时只输出：

`Your first reward is a gift box. Pick one, {{name}}.[NO_OP]`

# 自检
只输出固定输出中的一句话；不得提具体皮肤、金币、奖品细节、中文解释、emoji 或其它标签。
