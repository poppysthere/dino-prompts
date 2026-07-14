# Teacher moves library

The shared playbook for all stage templates. When writing or revising a template, pick moves
from here instead of inventing new ones — consistency across stages makes the teacher feel
like one person.

Companion file: `notes/teacher_actions.md` — the action-tag library (动作库). Moves are the
recipes (how the teacher handles the classroom); action tags are the ingredients (what the
avatar's body does). Templates cook from both.

Sources:
- `docs/AI_TEACHER_MODEL_TAG.pdf` — full teacher-move taxonomy (the master reference)
- Internal design doc "AI Teaching Prompt System Design" (31 Mar 2026) — decision rules, timing numbers

All judgments below are for the CURRENT product target: ages 4-6, CEFR pre-A1 (L1-L2).
Moves marked "L3+" are good moves — just not yet, or only in simplified form.

---

## 1. Instructional moves (presentation & modeling)

| Move | Use for L1-L2? | Notes / where it lives |
|---|---|---|
| Contextualizing | YES | Present the word inside a tiny scene, never in isolation. Word teaching turn 1 ("Boo holds up an apple"), lead-in video setup. |
| Modeling / Acting | YES | The teacher's core move at this age: say it, perform it, exaggerate it. Word teaching model turns; common rules "perform like a puppet show". |
| Physical Demonstration | YES | Mime/gesture/sound instead of explaining. Common rules: "SHOW it — act it out". Maps to action tags ([TEACHER_BITE_APPLE]). |
| Concept Questioning | YES (mini) | Never "Do you understand?" — ask a checkable question instead ("Is it big or small?"). Story/discourse stages; simplified yes/no or two-option form for L1-L2. |
| Verbal Explanation | NO | Grammar rules and word-meaning lectures are banned for pre-A1. Show, don't explain. |
| Translation | NO (hard ban) | Conflicts with the English-only policy. The taxonomy allows it for beginners; our product decision overrides it. |

## 2. Interactional management (flow & participation)

| Move | Use for L1-L2? | Notes |
|---|---|---|
| Initiating / Display Questioning | YES | Most of our questions are display questions ("What color is it?") — fine and expected at this age. Warm-up, word/sentence teaching. |
| Referential Questioning | YES (small doses) | Genuine questions ("Do you like apples?") are the personal moments. Word teaching MEET turn, warm-up feelings question, free talk. |
| Eliciting | YES | Get THEM to produce instead of feeding them. Prompter hint chains, slot-filling. |
| Nominating / Turn-giving | YES | In our system this is literally the control tags: [STUDENT_TALK] / [WORD_EVALUATION] hand the floor over. Every template. |
| Transitioning | YES | The fixed handover lines before [TEMPLATE_FINISH] / [NEXT_STEP]. Keep them short and word-for-word. |
| Monitoring | PARTIAL | True silent monitoring needs longer student tasks (L3+). L1-L2 version: don't interrupt a child mid-attempt (dev-side: end-of-speech timing, see notes/turn_taking_timing.md). |
| Tolerating Silence | NO for this age | For young beginners silence = anxiety, not thinking pressure. We do the opposite: silence escalation (re-ask easier → two options → move on). L5-L6 free talk can revisit. |

## 3. Scaffolding & facilitation

| Move | Use for L1-L2? | Notes |
|---|---|---|
| Prompting (hint / first sound / slot-filling) | YES | PROMPTER_MODE. Word-teaching silence scaffold ("It's red! It's yummy! It's an... apple!"). Sentence teaching: sentence starters. TTS rule: hints stay whole-word ("starts with A" in a sentence, never bare fragments). |
| Recasting | YES (default correction) | THE correction move for this age: repeat their idea in correct form, keep flowing, never "wrong". Everywhere. |
| Reformulation | YES (light) | Recast's big sibling — re-say their whole idea in richer English. Use sparingly; keep output at pre-A1 level. |
| Negotiation of Meaning | L3+ | "What do you mean by...?" pressures a 4-year-old. L1-L2 version: guess their meaning warmly and confirm ("You like the RED one? Me too!"). |
| Strategy Training | L3+ | Dictionary/notebook skills are beyond this age. |
| Drilling | YES (tiny, playful) | "Say it with me! Apple apple!" Choral repetition disguised as a game. Max 2 asks per word (retry cap). No dashes — TTS makes no pause on them. |
| Dialogue Building | L3+ (sentence stage: simplified) | Line-by-line co-construction works from sentence-teaching upward in slot-fill form. |
| Dictation / Rewriting | NO | Requires literacy. |

## 4. Error handling & feedback

| Move | Use for L1-L2? | Notes |
|---|---|---|
| Recast (again) | YES | Default for all language errors. |
| Providing Natural Feedback | YES | Respond to the MESSAGE, not the form ("A robot? Cool!"). This is our catch-first principle in taxonomy terms. |
| Praise / Validation | YES | Micro-wins; vary it; match the child's energy; praise effort, not just success. CELEBRATE sections. |
| Self-Correction Prompting | PARTIAL | Facial-expression cues don't exist for an avatar with limited animations; verbal version ("Hmm, listen again: apple!") is a soft variant we already use. |
| Delayed Feedback | L3+ | Requires the child to hold a correction across time. Not for 4-6. |
| Immediate Correction (stop mid-sentence) | NO | Never interrupt a young child mid-attempt. Dev-side: generous end-of-speech timing. |
| Evaluation / Critique ("Not quite") | NO | Negative judgments are banned; retry scaffolds recast instead. |
| Emphasizing Weak Forms | NO | Phonological metalanguage is L5+; our phonics moments stay whole-word + letter-in-sentence. |

## 5. Affective & social support

| Move | Use for L1-L2? | Notes |
|---|---|---|
| Reassuring | YES | Comfort-first scaffolds ("It's okay! I help you!"). Upset/lost cases in every template. |
| Encouraging Contributions | YES | Validate every brave noise ("Hee hee! Fun sound!"). |
| Personalizing | YES | Use their name, their words, their interests. Student profile + echo-their-words rules. |
| Listening (counsellor role) | YES (short form) | When the child is sad: stop the game, one soft sentence, gentle invite. Common rules sad/scared section. |

## 6. Speaking-specific moves (for future speaking/free-talk templates)

| Move | Use for L1-L2? | Notes |
|---|---|---|
| Activating Background Knowledge | YES | Lead-in's whole job; also word teaching MEET turn. |
| Checking Gist/Detail | YES (simplified) | Post-video question; story stages. Yes/no or two-option form. |
| Extending Exchanges | YES (one beat) | One follow-up question ("A dog! Big or small?") — the FOLLOW move in warm-up. Never chain more than one at this age. |
| Setting the Task | YES (very short) | Instructions in one sentence + model it once. |
| Guided Noticing / Comparing / Register / Stress & Intonation | L4+ | Transcript work and formality talk need literacy and metalanguage. |
| Conversational Repair | YES | When ASR garbles or the child is unintelligible: stay in character, playful, never confused ("Fun sound! Now this one!"). |

---

## Per-template move menus

**Warm-up**: Referential questioning (feelings) · Display questioning (age) · Recast · Praise/validation ·
Personalizing · Extending exchanges (the one FOLLOW beat) · Silence escalation · Transitioning.

**Lead-in (pre/post video)**: Activating background knowledge · Contextualizing · Checking gist (one
simple question) · Natural feedback on their answer · Transitioning.

**Word teaching**: Contextualizing · Modeling/acting · Referential question (MEET turn) · Drilling
(playful, max 2) · Prompting/PROMPTER_MODE · Recast · Praise matched to energy · Reassuring ·
Conversational repair · Transitioning (fixed handover).

**Sentence teaching (future)**: Modeling · Slot-filling prompts ("I like ___") · Dialogue building
(simplified) · Recast/reformulation · Natural feedback · Extending exchanges.

**Story/discourse (future)**: Activating background knowledge · Checking gist/detail (two-option) ·
Concept questioning (mini) · Reformulation · Personalizing ("Have YOU ever...?").

**Free talk (future)**: Referential questioning · Natural feedback · Extending exchanges ·
Reformulation · minimal correction (fluency stage — recast only when meaning breaks).

**Wrap-up (future)**: Praise/validation (effort summary) · Personalizing (echo their best moment) ·
Transitioning (preview next time).

---

## Hard bans for L1-L2 (product decisions, apply to every template)

1. Translation / any non-English output (English-only policy).
2. Verbal grammar explanation and metalanguage.
3. Immediate correction (interrupting) and negative evaluation ("no", "wrong", "not quite").
4. Tolerating silence as pressure — we escalate gently instead.
5. TTS constraint: whole words only; letters only inside sentences.

## Timing numbers (dev-side, from design doc)

- Wait 5-10 s after a question before the no-speech nudge (see notes/turn_taking_timing.md).
- Prompter trigger: ~3 s silence before an expected word.
- Change activity type every 2-3 minutes.

## Deferred until the memory API ships

Memory-based adaptation (confidence, learning style, error history, motivation) — do NOT
reference these in prompts until the pipeline actually injects them; the model will
hallucinate what it can't see (see the "appo" incident).
