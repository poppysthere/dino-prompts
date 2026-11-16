# L4 Lesson 2 阅读理解互动修订

Test02 的 Landforms on Earth 原先会在孩子不会读或答不上来时转入反复跟读。本次让阅读以理解问答为主，已发布并回读核验。

- 范围：Test02MCL1_6U1 → Level4 → Unit 1 → Lesson 2，passage_teach，instance 6921。
- 封面做一次预测；正文先问当前页的意思，答对后可追问一个不同的信息点。
- 例如 Where does a valley lie? → Between mountains. → What may flow through a valley?
- 孩子不会时给一次简短解释、线索或选择题。每页最多两次回答机会，不要求反复读句子。单句页面答对即推进。
- 正确短答和有意义的中文答案被接纳，再自然用英语回应；不强迫抄读英语。
- 保留原占位符、控制标签、六页顺序和最后一页结束方式。只为此阅读创建独立 common，原共享 common 2125 保持不变。

22 个固定案例与 7 段完整六页合成对话均完成；最终文本已逐段人工审阅，理解问答和推进检查通过。保留 3 处封面弯撇号 Today’s 的格式提示，不宣称所有格式规则零偏差。[评测](evaluation.json) · [对话](transcripts.md) · [语义审阅和历史问题](semantic-review.md)。这是 Forge gpt-5.6-luna 的文本回放，真实 App、ASR、TTS 和儿童体验仍由手测确认。

[映射](mapping.json)记录 8 个绑定、4 份原始规则和实际版本 ID。[发布记录](release.json)确认回读一致，其他 38 个 L4 上下文、原共享 common 和课程树未变。production_acceptance 保持 false。

本修订仅替代 2026-11-16 广泛修复包中 instance 6921 的 common、template 和 6 个 page 绑定。先前包及其评测保持历史原样，其他实例继续使用原发布版本。

`prompts/` 是原始可编辑规则；`before-prompts/` 与 `diffs/` 用于审阅变化。`evaluation/history/` 保留此前失败或人工发现问题的合成回答，不以重试覆盖旧记录。本包不含凭据、真实学生资料或课堂启动链接。

运行 `python3 verify.py` 可离线核对文件及规则哈希。
