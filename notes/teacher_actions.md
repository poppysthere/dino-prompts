# Teacher action library (动作库)

The pantry for every template. Teacher moves (`notes/teacher_moves.md`) are the recipes —
HOW the teacher handles the classroom. Action tags are the ingredients — WHAT the avatar's
body actually does. When writing or fixing a prompt, cook from this pantry only:

1. **Templates may only use tags registered here.** Every tag maps to a real client-side
   animation. An invented tag (e.g. `[TEACHER_SALUTE]`) plays NOTHING on the avatar — the
   teacher talks about jumping while standing still, which is exactly the "motionless,
   doesn't feel like a real person" bug we fight. Checkers now flag unregistered tags.
2. **If the avatar can't show it, the words can't claim it.** No "Big smile!" or "watch me
   dance!" in the script unless a matching tag exists. (This is why "Big smile!" was removed
   from the common-layer examples.)
3. New animations added by the client team get registered here FIRST, then become available
   to templates.

## Placement rules (apply to every template)

- The tag goes right after the sentence it belongs to, in the same reply:
  `Moo moo![TEACHER_COW_HORNS]` — never on its own line, never before the sentence.
- 1-2 action tags per reply. A tag on every sentence reads like a twitching puppet.
- Action tags are NOT control tags. Control tags (`[STUDENT_TALK]`, `[NEXT_STEP]`,
  `[TEMPLATE_FINISH]`) end the reply — exactly one, at the very end. Action tags decorate
  sentences inside it.
- Every wait ends `[TEACHER_LISTEN][STUDENT_TALK]` — the listening pose is glued to the
  handover so the child sees the teacher waiting for THEM.
- Energy matching: the action must match the child's mood, not just the script. A quiet
  "no" gets a soft close with no applause; a shout gets the big celebration.

## Registered tags

### Universal (any template)

| Tag | Avatar does | Use when | Energy |
|---|---|---|---|
| `[TEACHER_LISTEN]` | Leans in, listening pose | Before EVERY `[STUDENT_TALK]` wait — mandatory | neutral |
| `[TEACHER_WAVE]` | Waves hand | Hello (warm-up greet), goodbye (wrap-up) | warm |
| `[TEACHER_APPLAUD]` | Claps | Big win: child said the word/sentence, finished the page | high |
| `[TEACHER_THUMBS_UP]` | Thumbs up | Smaller praise: brave try, partial success, good effort | medium |
| `[TEACHER_HIGH_FIVE]` | Raises palm for high five | Shared-win moment, "we did it together" | high |
| `[TEACHER_POINT_TO_SCREEN]` | Points at the screen | Handover to video/song, "look!" moments | medium |
| `[TEACHER_SHOW_MUSCLE]` | Flexes arm | "You're so strong/brave!", confidence boost, cat-page close | medium |
| `[TEACHER_JUMP]` | Jumps once | Blast-off launches, countdown closes (L3+ originals use it) | high |

### Word-specific (signature action of the page — use at model + celebrate beats)

| Tag | Avatar does | Page |
|---|---|---|
| `[TEACHER_COW_HORNS]` | Fingers as horns on head | cow |
| `[TEACHER_CAT_PAWS]` | Paw hands | cat |
| `[TEACHER_RIDE_HORSE]` | Riding gesture | horse |
| `[TEACHER_BITE_APPLE]` | Bites an imaginary apple | apple |
| `[TEACHER_BREAK_BREAD]` | Breaks imaginary bread | bread |
| `[TEACHER_DRINK_JUICE]` | Drinks imaginary juice | juice |
| `[TEACHER_CLIMB]` | Climbing gesture, hands up | climb (L3 Dino & Mia) |
| `[TEACHER_FLY]` | Arms out like wings | fly (L3 Dino & Mia) |

The word page's signature action is its Physical Demonstration move (see teacher_moves.md
section 1): it fires when the teacher MODELS the word and when the child nails it —
so the body teaches the meaning, not a lecture.

### Not action tags (do not register here)

- `[STUDENT_TALK]`, `[NEXT_STEP]`, `[TEMPLATE_FINISH]` — control tags (turn-taking).
- `[WORD_EVALUATION]` — legacy control tag, banned in current L2 templates.
- `[TEACHER_TALK]` — legacy system marker, never emitted by templates.

## To be added (owner: Heidi)

Client team is expanding the animation set. New tags land in this table with the same
four columns before any template may use them.

| Tag | Avatar does | Use when | Energy |
|---|---|---|---|
| _(pending)_ | | | |
