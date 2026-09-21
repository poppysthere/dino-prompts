# L3 V2 A1+ language evaluation — 2026-09-21

## Scope

- Prompt version: `prompts/l3-v2`
- Lesson flow: lead-in first; no warm-up
- Model: Prompt Forge `gpt5.6LunaChatModel` (`gpt-5.6-luna`)
- Language policy: English only, with no translator or second teacher

## Changes under test

- The common rule now assumes only familiar A1+ words and short phrases.
- Most spoken sentences are limited to 2–7 words and one idea.
- The teacher gives one clear action at a time and models the answer when the
  child is lost.
- Abstract labels, idioms, irony, pretend mistakes, and unexplained jokes are
  blocked unless they are explicit lesson targets.
- The opening now says:

  `Hi, {{name}}! Welcome! Today, let's learn three new words. Climb. Jump. Fly. First, watch the story. Then, say the words. Ready?`

- The story launch is now:

  `Look! Dino and Mia are here. The story starts now!`

- The wrap-up no longer uses `adventure` or a long fixed celebration line.
- The production sentence flow is now represented exactly: intro, video,
  `Can you climb?`, then `I can climb.` The obsolete `Can you fly?` and
  `Piece of cake!` prompt files were removed from V2.
- Word teaching uses the natural classroom pattern `Listen. ... Your turn. ...`
  and must briefly respond when a child shares a personal sentence.
- The post-video lead-in now asks the easy yes-or-no question `Can they fly
  together?` instead of the broad `What fun will they have together?`.

## Results

| Stage | Cases | Result |
|---|---:|---:|
| Lead-in | 13 | 13 passed |
| Word teaching | 35 | 35 passed |
| Sentence teaching and wrap-up | 19 | 19 passed |
| **Total** | **67** | **67 passed** |

The cases include ready/not ready, silence, confusion, meaning questions,
another-language input, junk names, ASR near-misses, retry limits, off-topic
answers, ask-backs, and fresh-step state resets.

The word suite exposed two useful issues during iteration. First, the teacher
passed personal sentences without reacting to the child's idea; the prompt now
requires a tiny natural echo. Second, Luna occasionally treated the ASR form
`Junk` as a near miss instead of `jump`; the prompt now marks it as an immediate
PASS. Both repairs were retested successfully.

## Example repairs

- Child: `What do I do?`
  Teacher: `Say, can you climb? Listen again. Can you climb? Your turn. Can you climb?`
- Child: `What is climb?`
  Teacher: `Climb. Go up, up, up.`
- Child: `I jump on my bed!`
  Teacher: `On your bed? Wow! Yes! Great job!`
- Child: silence
  Teacher: `Let's start.`
- Child: `Did YOU like it?`
  Teacher: `Yes! I liked it! Now it's song time. Let's sing together!`
