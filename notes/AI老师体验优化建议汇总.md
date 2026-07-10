# AI 老师体验优化建议汇总

**提交对象**：开发 / 算法团队
**背景**：在测试少儿一对一在线英语课的 AI 老师过程中，发现三个方向的问题，整理如下，附具体建议方案，供开发排期参考。

---

## 问题总览表

| 编号 | 问题 | 优先级建议 |
|---|---|---|
| 1 | Filler words 机制与 Prompt 效果混淆，无法单独验证 | P2 |
| 2 | ASR 识别错误率高，人名被误识别为 "Dino" | P0（根因已定位，改动小） |
| 3 | ASR context 配置整体过于简单，需按少儿场景重新设计 | P1 |
| 4 | 说话结束判定时间过短，孩子说话被截断 | P0 |
| 5 | 无语音超时机制"一刀切"，未按环节区分 | P1 |
| 6 | VAD 竞态：孩子已开口，静默提示语仍触发打断 | P0（体验影响大） |

---

## 一、Filler Words 与 Prompt 效果混淆

**问题**：
目前 filler words 的表现无法在 prompt 层面单独体现出来。例如老师反复用 "take your time" 作为开头口头禅,同样的 filler 反复出现。

**建议**：
搭建一个去掉 filler words 机制的测试环境,单独观察 prompt 本身对语气/节奏的调控效果,排除 filler words 机制的干扰,便于判断问题到底出在哪一层。

---

## 二、ASR 识别问题

### 2.1 已定位的具体 bug：误识别为 "Dino"

**现象**：孩子说话时,被识别成 "I, Dino"。

**根因**：排查 setting 后发现,"Dino" 这个词的 boost 值被设置成了 **15**（当前所有词条中权重最高）。但在本课程中,用户全程只跟老师对话,并不会主动触发 "Dino" 这个词。

**猜测**（待技术确认）：怀疑这是沿用了之前"双师智学"项目的遗留配置,与当前课程业务无关。

**建议**：核实并清理当前 context/boost 词表中与本课程无关的词条。

### 2.2 当前 ASR 配置（现状）

```yaml
context:
  general:
    - key: setting
      value: Children's English lesson. The primary spoken language is English.
    - key: language
      value: Prioritize English transcription. The child may occasionally mix English with their native language, but ambiguous sounds should be interpreted as English whenever reasonable.
    - key: instructions
      value: Keep English greetings, simple responses, classroom phrases, and vocabulary in English when spoken in English. Do not translate English words into the child's native language. If an utterance could be either English or the native language, prefer the English transcription. When you hear the pronunciation of Dyno, Daino, or similar variants, transcribe it as Dino.
  terms:
    - hi
    - hello
    - thanks
    - sorry
    - goodbye
    - cool
    - bye
    - yes
    - no
    - okay
    - cow
    - dino
  phrases:
    - What's this?
    - What's your name?
    - I don't know.
    - Yes, it is.
    - No, it isn't.
    - My name is ...
    - Thank you!
    - I don't like it.
    - It's fun!
    - I can do it.
    - What happened?
    - I forgot.
speech_context:
  entries:
    - phrases: ["Dino"]
      boost: 15
```

**现状问题小结**：
- 场景描述（setting）过于笼统,没有说明孩子的年龄、发音特点、语速、可能的背景噪音等,模型缺少"这是一个 4-6 岁孩子在说话"的先验信息。
- 没有区分"学生本人""老师""课程重点词"等不同优先级,只有一个孤立的 "Dino" boost=15,且与本课程业务无关。
- 没有规则处理静音/听不清、语法不修正、拆音节拼词、字母保留等常见少儿语音场景。
- 学生姓名、老师姓名、课程目标词汇等完全没有动态注入机制。

### 2.3 建议的新 ASR 配置

按"场景设定 → 语言规则 → 分层词表 → 分级权重"四层逻辑重新设计,并做 A/B 测试对比效果：

```yaml
context:
  general:
    - key: setting
      value: One-on-one online English lesson. The speaker is a child aged 4-6 with
        very limited English, usually at home on a tablet. Utterances are short
        (often 1-5 words), slowly spoken, and may be mispronounced, stretched, or
        broken into syllables. Expect single words, names, letters, numbers, simple
        phrases, laughter, singing, and playful sounds rather than full sentences.
        Background voices (parents, siblings, TV) may be present.
    - key: language
      value: Prioritize English transcription. The child's native language is
        {{nativeLanguage}}; they may mix it with English. Transcribe native-language
        speech as that language when it clearly is, but interpret ambiguous sounds
        as English. Never translate between languages.
    - key: instructions
      value: The child is talking to their teacher, {{teacherName}}. The child's own
        name is {{studentName}} — when an utterance sounds close to this name
        (especially after "What is your name?"), prefer transcribing it as
        {{studentName}}. Never replace a person's name with another word.
        Transcribe only the primary child speaker; ignore background adult speech.
        If audio is silence, noise, or unintelligible, return nothing — never guess
        or invent words. Do not fix the child's grammar — write what was said.
        Join stretched or syllabified word attempts into the intended word
        ("a... pple" → "apple"). Keep single letter names and letter sounds as
        letters ("A", "B") — do not expand them into words. Keep playful sounds
        and interjections as heard ("meow", "wow", "uh-oh", "haha").

  terms:
    # --- Layer 1: static kid-classroom vocabulary ---
    - hi
    - hello
    - bye
    - goodbye
    - yes
    - yeah
    - yep
    - no
    - nah
    - uh-huh
    - uh-uh
    - okay
    - thank you
    - sorry
    - happy
    - sad
    - good
    - fine
    - fun
    - yummy
    - yucky
    - mom
    - dad
    - wow
    - yay
    - uh-oh
    - meow
    - woof
    - moo
    - rawr
    - boom
    - poof
    - one
    - two
    - three
    - four
    - five
    - six
    - seven
    - eight
    - nine
    - ten
    # --- Layer 2: per-session（开课时注入，与填充 prompt 中 {{name}} 同一时机）---
    - "{{studentName}}"
    - "{{teacherName}}"
    # --- Layer 3: per-lesson（从课程已有的知识点字段派生，不新建平行词表）---
    - "{{lessonKnowledgeSpeech.words}}"    # 词汇类知识点 → 单词本身
    - "{{lessonKnowledgeSpeech.letters}}"  # 拼读/字母类知识点 → 字母名
    - "{{lessonCharacters}}"               # 画面角色（来自课程资源，非知识点），如 Chef Boo

  phrases:
    # --- Layer 1: static ---
    - My name is ...
    - I am five.
    - I am six.
    - I don't know.
    - What's this?
    - I like it.
    - I don't like it.
    - I can do it.
    - It's fun!
    - Thank you!
    # --- Layer 2/3: injected ---
    - "My name is {{studentName}}."
    - "{{lessonKnowledgeSpeech.sentences}}"  # 句型类知识点 → 本课目标句

speech_context:
  entries:
    - phrases: ["{{studentName}}", "My name is {{studentName}}"]
      boost: 10
    - phrases: ["{{lessonKnowledgeSpeech.words}}"]
      boost: 6
    - phrases: ["{{lessonKnowledgeSpeech.sentences}}"]
      boost: 5
    - phrases: ["{{lessonKnowledgeSpeech.letters}}"]
      boost: 5
    - phrases: ["{{lessonCharacters}}"]
      boost: 4
    - phrases: ["{{teacherName}}"]
      boost: 3
```

### 2.3.1 Layer 3 派生规则（从知识点字段生成，不单独维护词表）

核心原则：**ASR 词表 = "孩子嘴里可能说出来的东西"，而不是"这节课教的东西"**。按知识点类型映射：

| 知识点类型 | 进 ASR 的内容 | boost |
|---|---|---|
| 词汇类 | 单词本身，每词一条 | 6 |
| 句型类 | 完整目标句作为 phrase 条目（短句效果最好，如 "I like apples"） | 5 |
| 自然拼读/字母类 | 字母名（如 "A"） | 5 |
| IP/角色名（来自课程资源，非知识点） | 角色名（如 "Chef Boo"） | 4 |
| 技能/理解类知识点（can-do 描述、语法概念） | **不进 ASR** —— 孩子不会把这些说出口 | — |

派生时的约束：
1. **每项展开成独立条目**，不能拼成一个逗号字符串（speech adaptation 按条目做偏置）。
2. **控制在 ~20 条以内**：只放本课孩子预期会说出口的内容；优先本课新授，不要把历史复习词全部塞入（词表越大偏置质量越差）。
3. **与 Layer 1 静态词表去重**（如 yes、数字等可能同时出现在知识点里）。
4. {{nativeLanguage}} 取账号地区/语言设置；取不到时降级为通用表述（"their native language, whichever it is"）。

### 2.4 新旧配置核心差异对比

| 维度 | 现状 | 建议方案 |
|---|---|---|
| 场景描述 | 一句话概括,无年龄/语速/发音特点 | 明确 4-6 岁儿童特征、短句、慢语速、可能拆音节、背景噪音等 |
| 静音/听不清处理 | 无规则 | 明确"返回空,不许瞎猜" |
| 语法处理 | 无规则 | 明确"不修正语法,如实转写" |
| 拆音节/拉长音处理 | 无规则 | 明确合并规则（如 "a...pple" → "apple"） |
| 字母/拟声词处理 | 无规则 | 明确保留字母形式和拟声词原样 |
| 姓名注入 | 无动态字段 | 学生名/老师名开课时注入；课程内容从知识点字段派生（见 2.3.1），无需单独维护词表 |
| Boost 权重 | 仅 "Dino" 一项,boost=15,与业务无关 | 按学生名 > 课程词 > 目标句/字母 > 角色名 > 老师名分级设置,最高仅 10 |

---

## 三、静默 / 断句判定机制

**问题**：少儿说话节奏慢、容易拖沓停顿,但目前的打断判定机制是按成人语速设计的,反应时间不够,经常话还没说完就被打断。

### 3.1 计时器 1：说话结束判定（孩子开口后,停顿多久算说完）

| 场景 | 现状 | 建议 |
|---|---|---|
| 普通对话 | 成人默认值 0.5-0.8s,容易截断（如 "I am... um...... five" 中间停顿 1-2 秒思考） | 尾部静音延长到 **1.5-2.0s** |
| 单词跟读评测（WORD_EVALUATION） | 同上 | 放宽到 **2.5s** |

### 3.2 计时器 2：无语音超时（孩子一直没开口,触发 silent 提示语）

| 场景 | 建议时长 |
|---|---|
| 开放式问题（问名字/心情/想不想） | 6-8s（现有 7s 合理,可保留） |
| 跟读类（Say it with me） | 4-5s（模仿是即时反应,等太久说明孩子已经懵了,不需要成人级别的思考时间） |
| 第一次重新提示后仍无反应 | 约 5s |
| 第二次之后仍无反应 | 4-5s,然后直接推进下一步,避免卡住 |
| 单个问题总"死气"时间上限 | 控制在 **20s 以内** |

### 3.3 必须修复的竞态条件（Race Condition）

VAD（声音活动检测）一旦检测到孩子开始说话,必须**立即取消**已经在倒计时、即将触发的静默提示语。

否则会出现：孩子在第 6.8 秒开口说话,但系统的"7 秒超时提示"已经在路上,结果孩子话说到一半被系统提示语打断——这是当前机制中对体验影响最大的问题,优先级应高于单纯调时长。

---

## 优先级建议汇总

- **P0（尽快修复,改动小/影响大）**：
  - "Dino" boost=15 误触发问题（2.1）
  - VAD 竞态条件导致打断孩子说话（3.3）
  - 说话结束判定时间过短（3.1）
- **P1（需要评估排期）**：
  - ASR context 整体重新设计（2.3）
  - 无语音超时按环节细化（3.2）
- **P2（先做小范围验证）**：
  - Filler words 与 Prompt 效果分离测试（一）
