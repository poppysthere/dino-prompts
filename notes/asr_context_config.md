# ASR context config — redesign (kids' English lessons, L1, ages 4-6)

## Problem observed
"I is Heidi" was transcribed as "i dino". Root cause: the old config boosted "Dino"
at 15, listed it in terms, AND instructed the ASR to canonicalize "similar variants"
to Dino — while the student's actual name appeared nowhere. Any /aɪ/-heavy name
(Heidi, Daisy, Diana) lost to the mascot.

Kids in class only ever address the teacher, so "Dino" has no business being biased
at all.

## Design principles
1. Three layers: static classroom vocab → per-session (student/teacher name) →
   per-lesson, DERIVED from the lesson's existing knowledge-point field (词汇/句型/
   拼读 → speakable surface forms; skill/can-do knowledge points excluded — the ASR
   list is "what might come out of the child's mouth", not "what the lesson teaches").
   Do not maintain a parallel word list; derive it so it can't drift from the lesson.
2. Everything specific is a placeholder filled by the backend at class start —
   the same moment it fills {{name}} in the prompts. Nothing hardcoded. This includes
   the child's native language ({{nativeLanguage}}) — students can be from anywhere.
3. Boost hierarchy = cost of mishearing:
   student name (10) > lesson words (6) > phonics letters (5) > characters (4) >
   teacher name (3). Nothing above 10.
4. Describe the speaker and environment honestly in `general` (short, mispronounced,
   syllabified utterances; home environment with background voices) — helps ASR
   priors more than rules do.
5. Never fix the child's grammar in transcription — the teacher prompts rely on
   hearing "I is Heidi" as-is so they can recast it.
6. Never hallucinate: silence/noise/unintelligible → return nothing. The teacher's
   silence-escalation ladder depends on silences actually arriving as silences.
7. Keep letters as letters (phonics answers: "A!", "buh!") — no autocorrect to words.
8. Keep vocal play and onomatopoeia ("meow", "rawr", "poof") — the teacher prompts
   deliberately elicit these, and CATCH-ing them is the rapport strategy.
9. Join stretched/syllabified attempts ("a... pple" → "apple") — core word-teaching loop.
10. Transcribe only the primary child speaker; ignore background adult coaching.

## Scenarios accounted for
- Any native language (placeholder, not hardcoded Mandarin)
- ASR hallucination on silence/noise (breaks the silence ladder if unhandled)
- Parents/siblings/TV in the background
- Child repeats teacher, stretched or syllable by syllable
- Phonics: bare letter names and letter sounds as answers
- Onomatopoeia and vocal play the teacher itself teaches
- Casual yes/no variants (yeah/yep/nah/uh-huh/uh-uh)
- Ages and counting (numbers one-ten static)
- Singing/humming during song segments

## Deliberately NOT in the config
- Echo cancellation: TTS leakage vs. the child legitimately repeating the teacher
  cannot be separated at text level — needs AEC in the audio pipeline.
- Profanity/content filtering: transcribe faithfully; the teacher prompt's
  off-limits-topics rule does the redirecting. Filtering at ASR blinds the teacher.

## Config template

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
    # --- Layer 2: per-session ---
    - "{{studentName}}"
    - "{{teacherName}}"
    # --- Layer 3: derived from the lesson's knowledge-point field ---
    # Mapping by knowledge-point type (one entry per item, deduped, cap ~20,
    # prefer 本课新授 over review items, dedupe against Layer 1):
    #   词汇类   → the word itself                (boost 6)
    #   句型类   → full target sentence as phrase (boost 5)
    #   拼读/字母 → letter names                   (boost 5)
    #   技能/理解类 (can-do, grammar concepts)     → EXCLUDED, child never says these
    - "{{lessonKnowledgeSpeech.words}}"
    - "{{lessonKnowledgeSpeech.letters}}"
    - "{{lessonCharacters}}"   # on-screen characters (from lesson resources), e.g. Chef Boo

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
    - "{{lessonKnowledgeSpeech.sentences}}"  # 句型类知识点 → target sentences

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

## Implementation notes
- {{lessonKnowledgeSpeech.*}} / {{lessonCharacters}} must expand to one entry per
  item, not a comma-joined string — speech adaptation APIs treat each phrase as a
  separate bias entry.
- {{lessonKnowledgeSpeech.*}} is derived from the lesson's knowledge-point field at
  class-start; no separate list to maintain. Cap ~20 items (what the child is
  expected to SAY this lesson); prefer 新授 over review; drop skill/can-do points.
- {{nativeLanguage}} comes from the account locale; if unknown, fall back to
  "their native language, whichever it is".
- If a lesson genuinely features Dino as an on-screen character, it enters via
  {{lessonCharacters}} for that lesson only, at boost 4.
- Expect residual misrecognition with 4-year-olds regardless; the teacher prompts
  are the second line of defense (unusable answer → kind catch → move on).
- Separately from this config: ask about AEC (acoustic echo cancellation) in the
  audio pipeline so avatar TTS doesn't get transcribed as the child.
