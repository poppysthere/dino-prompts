# L2 V3 lesson prompts

Version: **V3**. Based on L2 V2 at 2393ae8. V2 remains unchanged.

V3 adds ASCII spoken punctuation, no written laughter/cheering, natural A1 responses, and adaptive IPA sound models. All active stages, including both lead-in steps, are in the evaluation scope.

Level 2 is for children ages 5 to 7 at CEFR A1.

There is no warm-up stage. The lesson starts with the lead-in, which owns the greeting and first child instruction.

Lesson flow:

1. Lead-in pre-video: greet, help the child say hi, explain the first action, launch the video.
2. Lead-in post-video: discover the missing cake and meet Mouse.
3. Word teaching: cow, cat, horse, with the existing reward/video nodes between teaching nodes.
4. Sentence teaching: intro video, `It's a cow.`, `It's a cat.`, `It's a horse.`, reveal.
5. Wrap-up and song handoff.

The common rule and every response stage enforce the same child-first contract:

- answer any safe child question naturally before continuing;
- respond to a personal comment or feeling before continuing;
- use short, reliable A1 English;
- give one clear child action at every wait;
- use `Now you try` to establish the routine, then the more natural `Your turn`;
- use no more than one exclamation mark in a reply;
- continue the next required stage row in the same reply, without adding a beat;
- never invent live visual facts, weather, or things the teacher cannot know.

The teacher's own name comes only from `{{teacherName}}`.

## What to paste into Forge

Use this folder as one version. Replace the common rules and all matching stage templates together. Keep the platform's existing variable names, action tags, video/reward nodes, and stage mapping. This repository update does not deploy content to Forge.

## V3 pronunciation and TTS contract

- Ordinary spoken punctuation: ASCII `. , ! ? '` only. Approved IPA uses separate `/ /` units; tags retain their original syntax and position.
- No written laughs/cheers or stretched spellings. Purposeful animal sounds remain.
- Cow `/k/ /aʊ/`, cat `/k/ /æ/ /t/`, horse `/h/ /ɔ/ /ɹ/ /s/`: General American, one phoneme per unit. A diphthong stays together.
- Multisyllabic words use syllables, e.g. apple `/æp/ /əl/`. Apple is only a general-policy example, not an added L2 word.
- Focus on a requested or reliably assessed difficult unit. ASR spelling alone is not evidence of a specific pronunciation error.
- Support uses the existing single retry; the lesson does not require perfect pronunciation before progressing.

## Evaluation

`eval/run_l2_v3_forge.py` runs 107 scripted dialogue cases across all 11 active stages using Prompt Forge `gpt5.6LunaChatModel`. It uses the common rules plus the actual stage template, saves raw model replies, and checks progression, child responses, tags, punctuation, and sound-help behavior.

`eval/run_l2_v3_sound_probes.py` separately tests 6 synthetic cases for syllables and trusted pronunciation feedback. These are not child recordings or actual pronunciation assessments. Both commands require Forge environment credentials; no token belongs in this repository.

Offline: `python3 eval/test_l2_v3.py` and `python3 eval/tts_punctuation.py`. The runner also requires PyYAML.

Automated results are not CEFR certification or a guarantee of natural teaching. Raw transcripts need review. TTS pronunciation, timing, and child comprehension still require listening and real lesson trials.
