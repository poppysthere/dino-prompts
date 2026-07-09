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
   per-lesson (target words, on-screen characters, target sentences).
2. Everything specific is a placeholder filled by the backend at class start —
   the same moment it fills {{name}} in the prompts. Nothing hardcoded.
3. Boost hierarchy = cost of mishearing:
   student name (10) > lesson target words (6) > characters (4) > teacher name (3).
   Nothing above 10.
4. Describe the speaker honestly in `general` (short, mispronounced, 1-5 word
   utterances) — helps ASR priors more than rules do.
5. Never fix the child's grammar in transcription — the teacher prompts rely on
   hearing "I is Heidi" as-is so they can recast it.
6. Age numbers (one..ten, "I am five") live in the static layer — every warm-up
   asks for them.

## Config template

```yaml
context:
  general:
    - key: setting
      value: One-on-one online English lesson. The speaker is a child aged 4-6 with
        very limited English. Utterances are short (often 1-5 words), slowly spoken,
        and may be mispronounced. Expect single words, names, numbers, and simple
        phrases rather than full sentences.
    - key: language
      value: Prioritize English transcription. The child may mix in Mandarin; transcribe
        Mandarin as Mandarin when it clearly is, but interpret ambiguous sounds as
        English. Never translate between the two languages.
    - key: instructions
      value: The child is talking to their teacher, {{teacherName}}. The child's own
        name is {{studentName}} — when an utterance sounds close to this name
        (especially answering "What is your name?"), prefer transcribing it as
        {{studentName}}. Never replace a person's name with another word. Transcribe
        numbers spoken as ages ("five", "six") as words, not corrected or expanded.
        Do not fix the child's grammar in transcription — write what was said
        (e.g. keep "I is Heidi" style utterances as spoken).

  terms:
    # --- Layer 1: static kid-classroom vocabulary ---
    - hi
    - hello
    - bye
    - goodbye
    - yes
    - no
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
    # --- Layer 3: per-lesson ---
    - "{{lessonWords}}"        # e.g. apple, ...
    - "{{lessonCharacters}}"   # e.g. Chef Boo

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
    - "{{lessonPhrases}}"      # this lesson's target sentences

speech_context:
  entries:
    - phrases: ["{{studentName}}", "My name is {{studentName}}"]
      boost: 10
    - phrases: ["{{lessonWords}}"]
      boost: 6
    - phrases: ["{{lessonCharacters}}"]
      boost: 4
    - phrases: ["{{teacherName}}"]
      boost: 3
```

## Implementation notes
- {{lessonWords}} / {{lessonPhrases}} / {{lessonCharacters}} must expand to one
  entry per word/phrase, not a comma-joined string — speech adaptation APIs treat
  each phrase as a separate bias entry.
- If a lesson genuinely features Dino as an on-screen character, it enters via
  {{lessonCharacters}} for that lesson only, at boost 4.
- Expect residual misrecognition with 4-year-olds regardless; the teacher prompts
  are the second line of defense (unusable answer → kind catch → move on).
