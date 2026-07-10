# Teacher moves library (from Prompt System Design, Mar 2026)

Shared playbook for all stage templates. When writing or revising a template, pick moves
from here instead of inventing new ones — consistency across stages makes the teacher feel
like one person.

Source: internal design doc "AI Teaching Prompt System Design" (31 Mar 2026), adapted for
ages 4-6 / pre-A1 and for what the current pipeline actually supports.

## Moves currently usable (no infra needed)

| Move | What it is | Where we use it |
|---|---|---|
| RECAST | Repeat the child's utterance with the correct form, never say "wrong" | warm-up mistakes; word-teaching retry |
| PROMPTER_MODE | Hint chain: attributes first ("It's red! It's yummy!"), then hand over the word, wait for the child to produce it | word-teaching silence scaffold |
| SUPPORTIVE_INFORMANT | Affective filter high ("I can't", crying, whining) → drop the game, comfort first, difficulty down, celebrate effort | word-teaching upset scaffold; common rules sad/scared rule |
| SELECTIVE NOTICING | Don't correct every error; only ones that block meaning | common rules |
| MICRO-WINS | Celebrate effort, not just results; vary the celebration | CELEBRATE sections |
| SILENCE ESCALATION | 1st: re-ask shorter/easier. 2nd: yes/no or two options. 3rd: soft transition, move on | common rules silence section |
| OPTIONS/FRAMES | Never expect independent answers from a stuck child — offer choices | silence escalation step 2 |
| CONCEPT QUESTIONS | 2-3 closed questions to verify understanding (not "do you understand?") | future: discourse/story stages |

## Numbers worth keeping (for dev-side timing, not prompts)

- Wait time after a question: 5-10 seconds before the no-speech nudge (see notes/turn_taking_timing.md).
- Prompter trigger in the design doc: silence > 3 s before an expected word.
- Task variety: change activity type every 2-3 minutes for this age.

## Moves that need infrastructure we don't have yet (do NOT put in prompts)

These reference learner data the model never receives today. Adding them now would make the
model hallucinate context (see the "appo" incident).

- Memory-based adaptation (confidence level, learning style, recent errors, motivation type)
- Emotional-state injection (anxious/neutral/confident from past sessions)
- Pace adaptation from tracked accuracy (80% gate to advance, recycle otherwise)

When the memory API starts injecting a learner profile into lesson prompts, revisit the
design doc's decision rules (IF confidence=LOW THEN scaffold up, etc.) and add a
"Learner context" section to the common rules.

## Style principles (apply to every template)

1. Specificity > generality — "say the word 3 times" beats "teach the word well".
2. Observable > interpretive — "silent for 5 seconds" beats "seems confused".
3. Rules > guidance — IF/THEN beats "try to...".
4. Only reference inputs the model actually receives.
