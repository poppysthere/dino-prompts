# 正式课 prompt

最新修复源码：[候选修复/2026-11-16](候选修复/2026-11-16/README.md)，现已按用户要求发布到 Test02 供手测，322 段规则全部回读一致。详见[发布记录](发布记录/2026-11-16-Test02手测.md)。生产验收仍为 false；以下 L1–L6 目录保留 2026-11-14 的历史回读快照。

本目录独立保存正式课规则，**不要与仓库原有体验课/历史版本目录混用**。

- 来源：Prompt Forge → **Test02MCL1_6U1**（测试环境）。
- 范围：L1–L6，Unit 1，Lesson 1–3，共 18 节。
- 同步日期：2026-11-14。逐项从 Forge 重新读取，与最后已核验版本比对一致。
- 本次包括：整页共用回答预算、重复提问退出、有用的求助示范、真实回应，以及 IP Call 重复就绪事件保护。保留原分级/课型策略和标签协议。
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

本轮通过 Forge GPT-5.6 Luna 运行当前版本的合成文本回归和逐页扫测，检查重复提问、等待上限、已完成目标、求助与拒绝、真实问题回应以及标签。完整结果和仍需观察的问题见 [评测记录](评测记录/2026-11-14.md)。不能把文本测试解释为真实儿童、ASR、TTS 或 App 接线验收。

本目录只含原始规则及映射，不含登录凭据、学生个人资料或真实对话日志。12 个无法读取的视频上下文仍登记在 manifest 中，未伪造内容。空规则和原生步骤保持原状。旧公共规则文件可能仍服务于未修改环节；以每个实例 mapping.json 的实际引用为准。
