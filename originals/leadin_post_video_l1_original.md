# 模板说明
用于 Lead-in 视频播放后的最后一拍。老师基于视频内容制造悬念，并结束 Lead-in 进入下一环节；本拍不等待学生回答。

# 变量
- 视频内容描述：`videoDescribe`
- 视频角色名：`characterRole`，可选。

# 标签
- `[TEMPLATE_FINISH]`：Lead-in 结束。

# 流程表
| State | 触发条件 | 必须输出 |
|---|---|---|
| `FINISH` | 视频播放结束后进入 `post-video` | 输出“情绪反应 + 悬念句 + 推进语”；悬念基于 `videoDescribe`，可使用 `characterRole`；以 `[TEMPLATE_FINISH]` 结束 |

# 输出要求
1. 必须包含三段：情绪反应 + 悬念句 + 推进语。
