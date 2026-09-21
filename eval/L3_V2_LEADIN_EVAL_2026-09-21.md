# L3 V2 lead-in eval — GPT-5.6 Luna — 2026-09-21

Prompt source: `prompts/l3-v2`.
Forge modelName: `gpt5.6LunaChatModel` (picker ID `gpt-5.6-luna`).

V2 removes warm-up and begins class in the pre-video lead-in. The first reply
welcomes the child, previews `climb`, `jump`, and `fly`, and tells the child to
listen, watch, and speak. The second reply reacts to the child once and starts
the Dino and Mia video.

Result: **10/10 lead-in cases passed**.

Covered cases include ready, not ready, asking what to do, asking what action
words are, answering in another language, silence, a junk default name, and
three post-video paths. Representative outputs:

- Ready: `Great, let's go!` then the story launch.
- Not ready: `That's okay. We'll start together.` then the story launch.
- “What do I do?”: `Listen and watch. I'll help you.` then the story launch.
- Silence: `Let's start together.` then the story launch.

The V2 full-battery plan contains 76 cases: 10 lead-in, 35 word, and 31
sentence/wrap-up. There is intentionally no warm-up stage. Word, sentence, and
wrap-up prompt files are byte-identical to V1 in this first V2 revision; only
the pre-video lead-in and lesson flow changed.
