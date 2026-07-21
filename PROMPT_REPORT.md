# Prompt Report — how our lesson prompts are tested, fixed, and proven

This document is for the team. It explains three things:

1. **The standards** — the mechanical checkers that every prompt template must pass, page by page.
2. **The mock kids** — the simulated children we run against every prompt, so fixes are grounded in how different kids actually react.
3. **The process and progression** — how a bug on a real device becomes a permanent, re-testable standard.

Everything below is enforced by code in `eval/`, not by opinion. A prompt change ships only when the whole battery passes live against a real model.

---

## 1. The fix pipeline (how every bug becomes a standard)

```
real device transcript (bug)
  → reproduce it as a regression case (eval/cases_*.yaml, with the device ID in the note)
  → fix the template (prompts/**)
  → add a mechanical checker rule so the bug CLASS can never silently return
  → run the full live battery against a real model (gpt-5.4-mini / gpt-5-mini / doubao-seed-16)
  → size lint (every template has a hard line + word budget, eval/lint_templates.py)
  → commit + push (every fix is versioned on GitHub with the reasoning in the message)
```

Two disciplines keep this honest:

- **Anti-bloat.** Every template has a line/word budget. A fix must usually pay for itself by trimming elsewhere; budgets are only raised for structural changes, with the reason written next to the budget.
- **Flakiness testing.** Fixed cases are re-run 3-4 times in a row before we trust them — LLMs fail intermittently, so one green run proves little.

Current coverage: **~319 test cases across 19 batteries**, covering warm-up, lead-in, word teaching, sentence teaching, and wrap-up at L1 (incl. 足球 festival), L2, L3, L5, and the 新手引导体验课 trial demo.

---

## 2. The standards — checkers per template family

Every reply the model produces is run through a checker. A checker is a set of named rules; any violation fails the case. Below, grouped by lesson page.

### 2.1 Universal rules (enforced in EVERY checker)

| Rule | What it catches |
|---|---|
| `tts-stretched` | Stretched spellings the voice engine cannot say ("Hiiii", "SOOOO", "BIIIG") |
| `tts-giggle` | Written giggles that break TTS ("hee hee", "teehee", "hehe") — only "Ha ha!" allowed |
| `tts-safety` / `tts-dash` / `tts-ellipsis` | Em dashes, "...", and other punctuation that sounds broken when spoken |
| `english-only` | Any non-English output (CJK characters etc.) — the teacher answers *meaning* in English instead |
| `one-tag` / `tag-last` / `tag-at-end` | Exactly one control tag (`[STUDENT_TALK]` / `[TEMPLATE_FINISH]` / `[NEXT_STEP]`) per reply, at the very end, nothing after it |
| `unknown-action` / `forbidden-tag` | Invented or off-whitelist action tags (only registered avatar actions from `notes/teacher_actions.md`) |
| `require-phrase` / `forbid-phrase` | Per-case content assertions (e.g. "must greet Kim, must NOT say Max") |

### 2.2 Warm-up (`checker_warmup.py` — L1 足球, L2, L3, L5)

The warm-up is a fixed-length "counter law" page: the number of teacher replies decides the beat; nothing the child says adds a beat.

| Rule | Standard it enforces |
|---|---|
| `path-a-ask-name` / `path-a-name-leak` / `path-a-reunion` | First meeting: ask the name once, never speak the (unknown) default name, never say "you're back" to a brand-new kid |
| `path-b-name` / `path-b-again` / `stale-name` / `name-mix` | Returning kid: greet with `<studentName>` only (never profile nicknames like "Tommy"), reunion wording only when a real name exists, a spoken name kills the default, never two names in one reply |
| `happy-once` | "Are you happy today?" is asked ONCE — the device bug where it was asked 3-4 times verbatim |
| `question-repeat` / `sentence-repeat` / `no-repeat-beat` | No question or sentence (3+ words) said twice on the page, not even reworded loops |
| `one-question` | One question per reply, maximum |
| `beat-budget` | Hard cap on total replies (the page must END — no infinite warm-up) |
| `no-question-on-finish` | No question in the same breath as `[TEMPLATE_FINISH]` — a question you don't wait for is fake |
| `child-job` | Every waiting reply gives the child a clear, tiny job |
| `silence-escalation` | Silence handling: re-ask shorter → yes/no choice → move on; never repeat verbatim |
| `invisible-action` | No stage directions in speech ("I wave at you") — actions are tags, not narration |
| `word-teach-leak` | The warm-up never starts teaching lesson words early |
| `age-question` / `register` | Age-appropriate talk: no kindergarten phrasing for 11-12 (L5), no adult phrasing for 4-6 |

### 2.3 Lead-in pre/post video (`checker_leadin.py` — L1/L2, L3, L5, 足球, trial)

Lead-ins are script pages: fixed teaser/launch/close lines, with a small personal "catch" slot in front that must react to the child.

| Rule | Standard it enforces |
|---|---|
| `script-launch` / `script-ask1` / `script-ask2` / `script-close` | The fixed script lines are spoken exactly, in the right reply, nothing after them |
| `script-ask1-drop` | No sentence silently dropped from a fixed line (models love dropping "Someone is at the door!") |
| `two-replies` / `three-replies` | The page is exactly its designed length — never longer, never shorter |
| `next-step` / `must-finish` / `no-wait` | The right control tag in the right place: video actually starts, page actually ends |
| `missing-catch` | If the child SPOKE, the reply must react to them before the script line — a reply that starts straight at the script ignored the child (real bug: "Mommy!" got no echo) |
| `catch-on-silence` | The reverse: a silent child gets NO invented catch (no reacting to words never said) |
| `catch-budget` | The personal catch stays tiny (8-10 words) — react, don't lecture |
| `sentence-repeat` | Nothing said twice on the page (real device bug: the ding-dong line spoken verbatim twice to a confused child) |
| `fake-praise` | No empty "Good guess! Good job!" — the reply must play with the child's actual word |
| `spoiler` / `spoiler-confirm` | The secret (e.g. the hedgehog) is never volunteered and never confirmed/denied; recasting the child's OWN guess into English is allowed (that's teaching, not spoiling) |
| `no-deny` | Never "No, not a dog!" — the teacher doesn't know either; every guess gets "Maybe!" |
| `hello-only` (trial) | Reply 1 is the greeting alone — the child's first job is just saying hi back (the "small win") |
| `feed-on-silence` (trial) | A silent/lost child gets the words fed ("You can say, hi Max!") instead of another question |
| `no-question-launch` / `no-question-finish` | No real question glued to a launch/close — it stalls a 4-year-old while the video starts without them |
| `no-teaching` / `kid-words` | No vocabulary drilling on a lead-in page; no announcer talk ("the big match is on") for 4-6 |
| `no-name-ask` | The trial demo never asks the child's name — greet and go |

### 2.4 Word teaching (`checker_word.py`, `checker_word_l3.py`, `checker_word_soccer.py`)

The pages where the robotic-drilling disease lived. The standards here encode "max two invites, then let it go."

| Rule | Standard it enforces |
|---|---|
| `invite-budget` / `retry-once` / `one-retry` | Maximum TWO invitations to say the word, ever. One ASK + one guided retry, then close warmly |
| `opt-out` | "我不想说" is sacred — acknowledged, never pushed, no third invite, no guilt |
| `wait-job` | Every waiting reply ends with one clear tiny job (a question, a say-it call, a play shout) |
| `no-repeat` / `question-loop` | The same sentence/question never repeats — including "reworded" loops |
| `fake-praise` | No "YES! You know it!" when the child only said "好" — praise must match what actually happened |
| `no-word-eval` / `word-eval` | No dependence on `[WORD_EVALUATION]` machinery — the teacher judges by listening |
| `wrong-word` / `word-taught` / `meet-word` | The page teaches exactly the word in `renderContent` — never a different lesson word leaked from history (real bug: the "Come on!" page taught "Goal!") |
| `names-the-shout` | Shouts are used, not defined: never "That is COME ON!" |
| `guided-retry` / `bare-retry` | A retry re-teaches with context (chunking, gesture, example) — never a bare "say it again" |
| `rising-invite` / `rising-call` / `listen-pose` | Invites actually stop and listen (`[STUDENT_TALK]` present, listening action) |
| `close-line` / `must-finish` / `reply-count` / `beat-budget` | The page closes on time, warmly, with the right tag — hard cap on total replies |
| `invisible-action` / `kid-words` / `no-teaching` | No narrated actions, no grown-up register, no grammar lectures |

### 2.5 Sentence teaching (`checker_sentence_l2.py` — L2 + L3 trails)

| Rule | Standard it enforces |
|---|---|
| `script-ask` / `script-fixed` / `script-reveal` | Fixed ask/reveal lines spoken exactly (punctuation-tolerant) |
| `retry-once` | One guided retry max, then move on |
| `question-loop` / `question-missing` | The step's question asked exactly once — never looped, never skipped |
| `early-advance` / `must-advance` / `early-finish` | Steps advance exactly on their boundary — a new "UI is ready" resets to THIS step (no skipping "Piece of cake!" because history looked done) |
| `catch-budget` / `too-long` | Reactions stay small; page length capped |
| `spoiler` | No revealing the answer of a later beat early |

### 2.6 Wrap-up (`checker_wrapup_soccer.py`)

| Rule | Standard it enforces |
|---|---|
| `recap` / `recap-budget` | Recap covers the lesson words, briefly |
| `goodbye` / `watch-line` | A real warm goodbye; the fixed watch-video line where required |
| `no-question` | No new question at the end of class |
| `name` | Correct name discipline to the very last line |

---

## 3. The mock kids — who we play when testing

Every battery simulates real children, not ideal students. Each case is one kid's behavior pattern; a prompt only ships when it treats ALL of them well. The runner speaks the child's lines (including Chinese, silence markers, and babble) and the checker judges the teacher's reaction.

### The kids

| Kid | How they behave in the test | What the prompt must do |
|---|---|---|
| **The happy-path kid** | Answers correctly, says "yes!", plays along | Celebrate specifically (not generic praise) and keep moving — no dwelling |
| **The silent kid** | Says nothing; the system injects "The student has been silent for 5 seconds", sometimes twice in a row | Re-ask shorter → two-option choice → move on gracefully. Never repeat verbatim, never celebrate an answer that never came, never stall the class |
| **The lost/confused kid** | "什么？", "我听不懂", "我不会" | HELP, don't repeat louder: comfort + feed the words ("You can say, hi Max!") or ask a two-choice question they can answer |
| **The Chinese-only kid** | Answers meaning in Chinese: "我很开心！", "小猫！", "不知道" | React to the MEANING in easy English; never echo Chinese, never translate, never treat L1 as a wrong answer |
| **The babbling kid** | "hkajshd", random sounds | Greet the sound happily, never parrot it back as a word or adopt it as a name |
| **The sad/tired kid** | "no. 不开心。", "I'm sad" | Softness first, no games, no "YAY!", never told to smile; the fun (video) is offered as comfort |
| **The scared kid** | "我怕。" | "It's okay. I'm here." first — the page still flows, gently |
| **The opt-out kid** | "我不想说。" (twice) | Respected instantly. No third invite, no "just try!", no guilt. Opt-out is sacred |
| **The ask-back kid** | Turns the question around: "Are YOU happy?", "你说是谁呀？" | Answer like a person FIRST ("Me? SO happy!"), then take the turn back |
| **The question-at-the-worst-time kid** | Asks something right when the page should close ("门后面是什么呀？") | A tiny real answer INSIDE the same reply, then the close — a question never buys extra beats, and never revives a dead question |
| **The chatty/multi-guess kid** | "A dog! A cat! A monster!", off-topic words ("water!") | Echo the LAST guess only; tiny catch for off-topic, then back on track |
| **The secret-guesser** | Guesses the hidden answer, often in Chinese ("刺猬！") | Recast their guess into English + "Maybe!" — never confirm, never deny, never volunteer the secret first |
| **The menu-echo kid** | Shyly echoes a word the teacher fed ("Cat.") | That IS an answer — celebrated like any guess, never "that's not what I asked" |
| **The mistake-maker** | "Me happy!", "I goed to the park" | RECAST, never correct: say the good version back as a happy reaction and move on. No "say it like this" |
| **The kid who already knows it** | Embeds the target word in their own sentence ("I climb trees at home!") | Counts as a try — celebrated, not treated as off-topic |
| **The name-protest kid** | "我叫张志桦，你怎么叫我 Tommy？" | Apologize in a few words, use THEIR name forever, never resurrect the old one |

### The name and identity traps (system-level kids)

| Setup | What it simulates | What must happen |
|---|---|---|
| `studentName: test_user` / `"11"` | Junk placeholder names from the booking system (very common in trial classes) | Never spoken. "My friend" or no name at all |
| `studentName: heidi` + profile 称呼 "Tommy" | Stale profile nickname conflicting with the real name (real device bug) | Greet "heidi" — profile nicknames are dead data |
| Role = Max / Kim / Leo (rotated per case) | Our three teacher personas | The teacher introduces the name from `# Role` — never a name copied from an example in the template (real device bug: Leo said "I'm Kim") |
| Seeded history | A page starting mid-lesson with previous steps in context | "The UI is ready" resets to THIS page — history never lets the model skip a step |

### Default test identities

- Student names: `heidi` (first meeting), `nina` (returning), `lily` (real-name greeting), `test_user` (junk).
- Teacher roles: production personas for Max (jungle captain), Kim (big-sister), Leo (playful big brother), rotated to catch hardcoded names.
- Models: `gpt-5.4-mini` (primary), `gpt-5-mini`, `doubao-seed-16` — run live through the Forge API, exactly like production.

---

## 4. The teaching doctrines behind the rules

These are the human standards the checkers mechanize. They came out of real device transcripts where the avatar felt "too AI".

1. **Recast, never correct.** Any speaking is a win at this age. Say the good version back as a happy reaction; never "say it like this."
2. **Feed the words.** A stuck kid WANTS to answer and has no words. Hand them a tiny menu ("You can say, yes. Or, no." / "A cat? A dog? Guess!"). Any echo is their answer.
3. **Answer first.** When the child asks the teacher something, the teacher answers like a person before taking the turn back.
4. **The counter law.** The teacher counts her OWN replies; that count is the beat. Nothing the child says adds a beat — pages always end on schedule.
5. **Say nothing twice.** No sentence, question, or catch repeated on a page. A repeat sounds like a broken robot.
6. **Invite budget.** Max two invitations to say a word. The class is the kid's class — no drilling.
7. **Opt-out is sacred.** "I don't want to say" ends the asking, warmly, immediately.
8. **Wait is a job.** Every reply that waits gives the child one clear, tiny, answerable task.
9. **Questions a 4-year-old can answer.** Open questions ("Who is it?") get options built in ("A cat? A dog?"). Two-choice beats open-ended.
10. **Matched catches, no fake praise.** The reply must prove it heard the child: their word leads, praise fits what actually happened.
11. **Small win first.** The trial demo opens with just "hi" — the child's first act in English class is one they cannot fail.
12. **TTS-safe, English-only output.** Everything written will be spoken aloud by an English voice engine.

---

## 5. Progression — real device bugs that became standards

Each of these was found in a real class transcript, reproduced as a test case, fixed, and locked in with a checker rule.

| Device bug (what the child experienced) | Fix + permanent standard |
|---|---|
| Leo introduced himself as "I'm Kim" / "Coach Leo" / "I'm teacher Max" (#365995 class) | Templates now show TWO contrasting role→name examples so the model must read `# Role`; forbid-phrases on every warm-up battery for the wrong names |
| Student "heidii" greeted as "Tom" / "Tommy" (example name + stale profile nickname) | Name comes from `<studentName>` only; `stale-name`, `path-b-name` rules; Tommy-profile trap case |
| "Are you happy today?" asked 3-4 times verbatim; page never closed | Counter-law rewrite of all warm-ups; `happy-once`, `question-repeat`, `beat-budget` rules |
| Word pages drilled "say it again" endlessly, ignored "Team是什么意思？" and "我不想说了" | THE HUMAN RULE rework: `invite-budget`, `opt-out`, `wait-job`, answer-the-child-first; regression cases for each real utterance |
| "That is COME ON!" — a shout defined like a noun | `names-the-shout` rule; usage-based teaching for shouts |
| "Come on!" page accidentally taught "Goal!" (history leak) | WORD CHECK rule + `wrong-word` checker guard |
| Announcer talk to 4-year-olds ("Tiny bugs team up! The big match is on!") | `kid-words` register guard with the exact forbidden phrases |
| Trial post-video: ding-dong line repeated verbatim to a confused child; "A mystery! Ooh!" twice (#367710-15) | Fed guess menu in the ask; confusion branches; say-nothing-twice law + `sentence-repeat` rule |
| Trial pre-video: silent kid got "Hi hi! YAY!" (celebrating a hi that never happened); "Mommy!" got no echo | `feed-on-silence`, `missing-catch`, `catch-on-silence` rules |
| Secret spoiled / denied ("No, not a dog!") | `spoiler`, `spoiler-confirm`, `no-deny`; recast-of-their-own-guess allowed by design |
| TTS spoke "Hiiii", "hee hee", em dashes, "..." as broken audio | Universal TTS rules in every checker |

---

## 6. Where things stand

| Lesson family | Templates | Battery | Status |
|---|---|---|---|
| L1 (pre-A1, 4-6) core | warm-up, lead-in, 3 words, 2 sentences, wrap-up | word/sentence/lead-in batteries | live |
| L1 足球 festival (World Cup) | common, warm-up, lead-in ×2, word (Goal!/team/Come on!), wrap-up | 58 cases | live, all passing |
| L2 (6-8) | warm-up, lead-in, words (cat/cow/horse), sentence trail, wrap-up | 100+ cases | live |
| L3 (7-9, A1+) | common, warm-up, lead-in ×2, words (climb/jump/fly), 5 sentence steps, wrap-up | 97 cases | live, all passing |
| L5 (11-12, A2+) | common, warm-up, lead-in ×2 | 32 cases | live, all passing |
| 新手引导体验课 trial demo | common, render-content data file, lead-in pre+post | 24 cases | live, 24/24 |

All templates, checkers, cases, and this report are version-controlled; every fix is one commit with the device bug and reasoning in the message.
