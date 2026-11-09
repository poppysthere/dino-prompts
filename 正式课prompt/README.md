# 正式课 prompt

本目录独立保存正式课规则，**不要与仓库原有体验课/历史版本目录混用**。

- 来源：Prompt Forge → **Test02MCL1_6U1**（测试环境）。
- 范围：L1–L6，Unit 1，Lesson 1–3，共 18 节。
- 同步日期：2026-11-09。逐项从 Forge 重新读取，与最后已核验版本比对一致。
- 本次包括：分级/课型调整、自然回应与帮助、废弃 WORD_EVALUATION、IP Call 所选角色与聊天规则。
- Git 保存不等于正式生产发布。没有修改其他课程树；本包也不包含课件、音视频或测评引擎。

## 按级别查看

|级别|CEFR / 年龄|课程|
|---|---|---|
|L1|pre-A1 / 4–6|[Lesson 1](L1/U1/Lesson1/) · [Lesson 2](L1/U1/Lesson2/) · [Lesson 3](L1/U1/Lesson3/)|
|L2|A1 / 5–7|[Lesson 1](L2/U1/Lesson1/) · [Lesson 2](L2/U1/Lesson2/) · [Lesson 3](L2/U1/Lesson3/)|
|L3|A1+ / 7–9|[Lesson 1](L3/U1/Lesson1/) · [Lesson 2](L3/U1/Lesson2/) · [Lesson 3](L3/U1/Lesson3/)|
|L4|A2 / 9–10|[Lesson 1](L4/U1/Lesson1/) · [Lesson 2](L4/U1/Lesson2/) · [Lesson 3](L4/U1/Lesson3/)|
|L5|A2+ / 11–12|[Lesson 1](L5/U1/Lesson1/) · [Lesson 2](L5/U1/Lesson2/) · [Lesson 3](L5/U1/Lesson3/)|
|L6|B1 / 12–13|[Lesson 1](L6/U1/Lesson1/) · [Lesson 2](L6/U1/Lesson2/) · [Lesson 3](L6/U1/Lesson3/)|

## 文件怎么放回 Forge

1. 先按级别、课次、环节和 instance ID 找到 `mapping.json`，不要仅凭相似文件名选规则。
2. `common.path` 指向该实例实际使用的公共规则，放在编辑区顶部的“公共规则”。同级可能有多份，不可随意互换。
3. `template.path` 是原始模板规则，放在“模板规则”。
4. `steps[].prompt.path` 是相应 step 的规则，按 `stepCode` 放在“分步规则”；`prompt: null` 表示没有可编辑 step 规则，不造空白替代文本。
5. 保留所有 `{{变量}}` 和标签。不把渲染后的学生资料或课程内容粘成永久规则。
6. 保持各实例原有作用范围；本次修改使用 Lesson 级隔离，不能覆盖共享 Template 规则。

所有 prompt 文件保留 Forge 原始正文，不添加说明性前言；仅对没有末尾换行的文件补一个换行。`manifest.json` 及各 `mapping.json` 记录代码、ID、路径、原始 `source_sha256` 和文件 `sha256`，可核对内容。

可在本目录运行 `python3 verify_snapshot.py` 离线校验；脚本不联网，也不会部署规则。

注意：L1 Lesson 2 的 `sentence_teach_explain`（instance 6546）原模板正文仅为 `/`，本包如实保留。真正的教学规则在其 `steps/` 中；不要把 `/` 当作完整教学 prompt，也不要为了填空而自行补写模板。

## 必须保持的协议

- Avatar 不输出 WORD_EVALUATION；原跟读等待已按用户确认改为 `[STUDENT_TALK]`。禁止条款中可能仍提及旧标签名称，不表示允许输出。
- 其他控制与动作标签不改，尤其 `[TEACHER_TALK]`、`[STUDENT_TALK]`、`[NEXT_STEP]`、`[TEMPLATE_FINISH]`、`[NO_OP]`。继续遵守每个模板原有使用范围与位置。
- IP Call 保留前端两个 IP 二选一、intro → ipcall、固定引导台词及触发格式。通话身份使用运行时所选 `roleDescription`，不冒用课堂老师或未选 IP；围绕已学知识做朋友式交流。
- 正式课不新增 IPA、音素或音节拆读。不删除原生媒体、游戏、测评功能，也不套用体验课取消 warm-up 的流程。

## 评测和边界

分级/课型版本通过 Forge GPT-5.6 Luna 做过 53 条合成文本路径测试：42 条观察路径通过，11 条有限观察。之后的标签/IP Call 定向修订另做了 14 条文本场景，检查等待标签、固定 intro 和角色注入。两批不是 67 条最终整课通过，也不代表真实儿童、TTS 或前端选角接线验收。

仍有个别弯撇号、机械反馈和话题转接生硬的观察记录；不要对外宣称自然度或发音效果全面通过。IP 身份仍依赖平台正确注入选择结果。

完整清单见 [manifest.json](manifest.json)。12 个无法导出的原视频上下文只记录在清单中，未伪造 prompt。其余空规则/原生步骤按原状登记。Git 中只含原始规则和必要映射，不含 Authorization token、学生个人资料或对话日志。
