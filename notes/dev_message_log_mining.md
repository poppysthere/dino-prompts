# 周一给研发的消息（对话日志自动质检 + 客户端兜底）

> 背景：单词教学模板已改为 talk-first（只用 [STUDENT_TALK]，不再用 [WORD_EVALUATION]）。
> prompt 层面能修的都修了，但模型偶尔还是会违规。有两件事需要研发配合，
> 都不大，但对规模化很关键。

---

## 复制粘贴版

各位，两个需求，都是给 AI 老师上保险的：

**1. 对话日志自动质检（离线跑，不影响线上）**

我们模板有一批"结构性硬规则"，违反了就等于课坏了，而且**用脚本就能检测，不用人看**：

- 每条老师回复末尾必须有且只有一个控制标签（[STUDENT_TALK] / [TEMPLATE_FINISH]）
- 单词页第一句必须是固定开场白，且之后不允许再重复输出开场白
- [TEMPLATE_FINISH] 只能出现在该页第 3 或第 4 条老师回复里，且必须带固定收尾台词
- 老师输出不能包含中文字符（英文沉浸硬规则）
- 每条 [STUDENT_TALK] 回复的最后一句必须是问题或跟读邀请（不能以陈述句结尾晾着孩子）
- 单页老师回复数不能超过 4 条；同一页不能输出重复句子

我这边已经写好了检测脚本（Python，单文件，无依赖，仓库里 eval/checker.py，
输入一个 JSON 对话记录，输出违规列表）。希望你们：
每天离线跑一遍全量课堂对话日志 → 违规的 session 打标记 → 给我一个每周违规清单
（classId + 违规类型就行）。这样上量之后不用靠家长投诉发现问题，
每个新问题我会变成回归测试用例，修一次就永久不再犯。

**2. 客户端兜底（把"不能靠模型自觉"的规则改成代码保证）**

有几条规则模型偶尔会违反，但客户端可以百分百兜底：

- 单词页老师回复满 6 条后，客户端强制结束本页（等价于 TEMPLATE_FINISH 兜底），
  不再等模型自己说结束。（模板设计是 3-4 条，但静默提醒会额外注入老师回合 ——
  07-11 实测一次静默就把页面推到 5 条，所以兜底阈值留到 6）
- 如果模型输出的回复和它上一条完全相同（比如重复开场白），客户端丢弃并重新请求一次
- 回复末尾没有任何控制标签时的兜底策略：默认当作 [STUDENT_TALK] 处理（继续听），
  不要卡死等待

Prompt 我会继续优化，但这三条属于"模型哪怕万分之一概率犯错也不能让孩子看到"的级别，
放代码里最稳。

有问题随时找我，checker 脚本和测试用例都在我们的 prompt 仓库里。

---

## 附：本周已发现并修复的违规类型（给研发参考，都是真实发生过的）

| 日期 | 违规 | 现在的防线 |
|---|---|---|
| 07-10 | 中文"苹果"被当成说了 apple，提前结课 | prompt 定义 + few-shot 示例 |
| 07-10 | 一次跟读失败就直接结课（孩子没有第二次机会） | 固定 3-4 轮页面结构 |
| 07-10 | 回复以陈述句结尾，孩子不知道该干嘛 | "child's job" 硬规则 + checker |
| 07-10 | 叫错名字（用了 profile 里的旧名字 Tommy） | studentName 唯一名字规则 |
| 07-11 | 第 2 轮原样重复固定开场白 | reply-1 gate 规则 + checker + 建议客户端去重 |
| 07-11 | 孩子说 "yummy" 被当成说对了单词，假庆祝 | "不是目标词的英文单词不算" 规则 + checker |
| 07-13 | 孩子只说了 "No"，ASR 转写成 "Yeah. No."（凭空多出 Yeah） | prompt 侧已加"矛盾回答以最后一个词为准"；**请研发查一下是不是 AEC 回声/噪声被识别成了 Yeah**——如果老师音频泄漏进麦克风，这类幻听会到处出现 |
| 07-13 | 00:20 和 00:21 两条 ASR final 相隔 1 秒，触发了两条老师回复（"Yes" + "You said hello..."），孩子被连珠炮 | **请研发确认客户端是否有 ASR final 去抖/合并**：短时间内的多条 final 应合并成一次生成，或丢弃前一条未播完的回复 |
| 07-13 | 热身后的奖励页把中文原名"张志桦"直接读给 TTS（热身内已按规则用 Zhang Zhihua） | prompt 公共层已有"名字必须用英文字母"规则；**请研发确认奖励页/后续页面的模板也挂了最新公共层**，以及传给模板的 name 值是不是拿了 ASR 原文——如果是，建议传热身里已经罗马化的名字 |
| 07-13 | #350425：studentName 传的是 "11"（像个 ID），真实称呼 Tommy 只在 profile 文本里 | prompt 侧已加兜底（非人名值一律不念）；**请研发查一下 studentName 字段的取数逻辑**——这个字段应该是孩子的称呼，不是数字 ID。profile 里的 称呼 和 studentName 应该一致 |
| 07-13 | 静默触发的收尾和孩子开口撞车：00:24 老师说"GO! Let's play!"收尾，孩子同一秒说了"不知道"，被完全忽略 | **请研发加 barge-in**：静默兜底回复在生成/播放中若收到 ASR final，应打断并重新生成（孩子好不容易开口，最不能忽略的就是这一句）。另外这孩子在第 24 秒开口，正好卡在两轮静默（约 10s x 2）的关口上——**建议热身第一问的 no-speech 超时放宽到 15s**：安静等待不花孩子的耐心，多问问题才花 |
| 07-13 | 同一节课热身 TEMPLATE_FINISH 之后又开了第二个热身会话（2 个会话，老师接着问 Are you happy today?） | 模板结束后应该进 lead-in 才对；**请研发查这个 classId 的 step 流转日志**——是孩子结束后开口触发了同一 step 重跑，还是 video 没起导致回退 |
| 07-13 | ASR 幻听第二例：#350750（classId 7640050001）测试者只说了"什么意思呀？"，转写成 "From. 什么意思呀？"——凭空多了个 "From" | 和 #348285 的幻听 "Yeah" 是同一类问题，现在有两个样本了；prompt 侧已加兜底（开头的孤立英文词当噪声处理），但**请优先查这两条的原始音频**：如果都是 AEC 泄漏或噪声误识别，这个问题会污染所有分支判断 |
| 07-13 | ASR 幻听第三例：测试者只说了"什么意思？"，转写成 "Sure. 什么意思？"——三个样本了（Yeah / From / Sure），全是句首凭空冒出的英文小词 | 同上，样本又多一个，模式很一致：**句首幻听英文虚词**，建议拿这三条音频一起归因 |
| 07-13 | 看过 ASR context 配置后基本定位：幻听大概率是配置自己造成的 | 三个改动，见下方"ASR 配置修改建议" |

## ASR 配置修改建议（针对句首幻听 Yeah / From / Sure）

1. **`language` 里的 "interpret ambiguous sounds as English" 就是在命令模型瞎猜**，和 `instructions` 里的 "no guessing" 直接打架。孩子说中文时句首第一个音节往往轻、含糊，正好命中 "ambiguous"，于是被强行转成英文小词，后面再正常转中文——三个幻听全在中文句子开头，"Sure. 什么意思？" 就是 什(shén) 被解了两次。改成：模糊音**宁可丢弃也不猜**（新文案见下）。
2. **terms 里的 yeah/yep/nah/uh-uh 建议删掉**（yes/no 保留）：这些词声学上太短，boost 之后噪声很容易误命中；第一例幻听 "Yeah" 本身就是 boost 词。误报的 yes/no 会直接翻转课堂分支，是代价最高的错误。
3. **name 指令引用了一个从来没传进去的名字**："transcribe any sound matching this name" 但配置里根本没有孩子的名字。应把真实 studentName 插进 context 和 speech_context boost（像 Dino 一样）——但仅当它是真人名时（"11"/"test_user" 不注入，呼应 studentName 取数 bug）。
4. 小项：phrases 里 "My name is ..." 去掉字面 "..."；setting 里 "Expect single words..." 需要配一句反向约束（宁少勿多）。

建议替换的两段（英文原文，可直接粘）：

```
- key: language
  value: >-
    Prioritize English transcription. The child's native language is Chinese and they
    often mix the two. Transcribe Chinese speech as Chinese and English speech as
    English. If a sound is too unclear to confidently assign to either language, omit
    it entirely — transcribe only what was clearly spoken. Never translate.
- key: instructions
  value: >-
    The child speaks to their teacher. Only transcribe the child's primary voice;
    ignore background adult talking. Return blank output for silent, noisy, or
    unrecognizable audio — no guessing or making up words. Never prepend or append
    words that were not clearly spoken: a breath, a lip smack, or the first syllable
    of a Chinese word is NOT a short English word ("yeah", "sure", "from"). When in
    doubt, output less, not more. Do not fix the child's grammar; write speech
    verbatim. Combine split or stretched word attempts into the full target word
    ("a... pple" -> "apple"). Keep single letter names and letter sounds as raw
    letters ("A", "B"). Retain playful noises and interjections exactly as heard:
    "meow", "wow", "uh-oh", "haha".
```

验证方式：拿三条幻听样本的原始音频，用旧/新配置各跑一遍对比——改完 phantom 应消失，正常句子不受影响。
| 07-13 | 奖励页直接念了 studentName 的占位值："test_user, look! Today we have three rewards." | 热身/lead-in 的模板都有"垃圾名不念"的兜底，但**奖励页（rewards）模板没走 common 层**，名字槽是裸插值；请把 rewards 模板也接上 common 层的 name 规则，或客户端在 studentName 非人名时传空 |
| 07-13 | 同一节课 pre-video 台词 "my friend... shhh — someone's in the kitchen!" 用了 "..." 和 "—" | 这两个符号 TTS 念出来是破音（我们的 prompt 规范里明确禁用）；这个 lesson 的 pre-video 模板还是旧版，**建议排进模板迁移清单**（Farmer Bob 那节已经迁完，可以照抄结构） |
