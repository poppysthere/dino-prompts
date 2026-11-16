# L5 Lesson 2 Wrap Up 时态修订

用户发现收尾时老师仍说 Today we will learn。旧模板只要求提到今天的内容，没有明确区分已学回顾和开课预告；课程资料也带有历史开课脚本。

现已更新 Test02 的 Level5 / Unit 1 / Lesson 2，Wrap Up instance 7055，只改一份 Lesson 级模板。视频前明确回顾已读内容，例如 We read about Emma and Stella helping each other. Now watch the video to look back at their caring friendship. 视频后继续回顾故事，再进入后续活动。

`lessonKnowledge` 中的教学目标、阅读策略和开课示例只作为课程资料，不能当作当前阶段的指令。一般事实仍可用现在时，例如 Good friends help each other。保留 pre-video → video → post-video，以及 NEXT_STEP / TEMPLATE_FINISH 协议。

旧版 3 个固定回放中，带历史开课内容的场景复现了用户报告的 Today we will learn how caring friends help each other。修改后 12/12 场景通过，覆盖就绪、旧开场上下文、孩子问学什么/学过什么、求助、中文、询问是否下课、视频完成及原生媒体步骤。所有实际回答均已阅读。原版证据保存在 baseline-results.json，未通过重复抽样掩盖问题。

[发布记录](release.json)确认模板回读一致，其他 38 个 L5 活动、原共享 common、三步结构、原视频 URL 和课程树均保持不变。此次只验证 Forge gpt-5.6-luna 文本回放；真实 App/TTS 效果待手测。未转写或修改预录视频配音。production_acceptance 仍为 false。

[当前模板](template.md) · [改动](template.diff) · [映射](mapping.json) · [评测](evaluation.json) · [实际回答](candidate-results.json)

本修订只替代 2026-11-16 广泛发布中 instance 7055 的 template。其他规则继续使用各自的已发布版本。运行 `python3 verify.py` 可离线核对本包。
