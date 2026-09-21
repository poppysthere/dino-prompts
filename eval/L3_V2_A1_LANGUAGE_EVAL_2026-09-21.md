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

## Results

| Stage | Cases | Result |
|---|---:|---:|
| Lead-in | 11 | 11 passed |
| Word teaching | 35 | 35 passed |
| Sentence teaching and wrap-up | 31 | 31 passed |
| **Total** | **77** | **77 passed** |

The cases include ready/not ready, silence, confusion, meaning questions,
another-language input, junk names, ASR near-misses, retry limits, off-topic
answers, ask-backs, and fresh-step state resets.

One word transcript used a typographic apostrophe in `Let’s`. The spoken line
was correct; the mechanical checker was updated to treat straight and curly
apostrophes as equivalent.

## Example repairs

- Child: `What do I do?`
  Teacher: `Watch first. I will help you.`
- Child: `What is climb?`
  Teacher: `Climb. Go up, up, up.`
- Child: silence
  Teacher: `Let's start.`
- Child: `Did YOU like it?`
  Teacher: `Yes! I liked it! Now it's song time. Let's sing together!`

