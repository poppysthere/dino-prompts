# Prompt templates, organized by level

One folder per level. The filename (minus `.md`) is the template name in Prompt Forge —
folders are for OUR navigation only, so moving files never breaks the Forge mapping.

```
prompts/
  l1/   Level 1 (ages 4-6, CEFR pre-A1) — teacher Kim / Max, Boo the dino, apple-bread-juice lesson
  l2/   Level 2 (ages 5-7, A1) — Mouse's cake mystery demo, cow-cat-horse lesson
  l3/   (future)
  l4/   (future)
  l5/   (future)
  l6/   (future)
```

Notes:
- Files named `_l1l2_` live in `l1/`: they are the current L1 lesson (the name is
  historical — L2 has since gotten its own demo templates in `l2/`).
- Each level has its own common layer (`common_teaching_simple_rules*.md`), prepended
  to every stage template of that level.
- Within a level, files follow `<stage>_teaching_rules_<level>_<step/word>.md`
  (stages: warmup, leadin, word, sentence, wrapup).
- Shared reference material lives in `notes/` (teacher moves, action-tag library,
  turn-taking timing) — templates cook from those libraries regardless of level.
