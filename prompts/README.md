# Prompt templates, organized by level

One folder per level. The filename (minus `.md`) is the template name in Prompt Forge —
folders are for OUR navigation only, so moving files never breaks the Forge mapping.

```
prompts/
  l1/   Level 1 (ages 4-6, CEFR pre-A1) — teacher Kim / Max, Boo the dino, apple-bread-juice lesson;
        plus the 足球课 World Cup festival special (`*_l1_soccer.md`: its own common layer + warm-up)
  l2/   Level 2 (ages 5-7, A1) — Mouse's cake mystery demo, cow-cat-horse lesson
  l3/   Level 3 (ages 7-9, A1+) — big-kid voice (no baby-talk); common layer + warm-up so far
  l4/   (future)
  l5/   (future)
  l6/   (future)
```

## Size discipline (防止 prompt 越修越长)

Cases live in the eval battery (`eval/cases_*.yaml`, unbounded); templates stay within the
budgets enforced by `eval/lint_templates.py`. When fixing a bug, work down this ladder and
stop at the first rung that fixes it:

1. **Data fix** — add a word to an existing list (a mishear whitelist, an agreement-word list).
2. **Generalize** — rewrite ONE existing rule so it covers the whole bug class. Never add a
   sibling rule that overlaps an existing one.
3. **Example swap** — replace the weakest existing example; the example count never grows.
4. **Add text** (last resort) — something else of equal size must be deleted, and only if the
   battery proves rungs 1-3 failed.

Every fix, whichever rung, still gets its regression case in the battery — cases are free,
prompt lines are not. Monthly compaction: try deleting suspect lines; battery stays green =
the line was dead weight.

Notes:
- Files named `_l1l2_` live in `l1/`: they are the current L1 lesson (the name is
  historical — L2 has since gotten its own demo templates in `l2/`).
- Each level has its own common layer (`common_teaching_simple_rules*.md`), prepended
  to every stage template of that level.
- Within a level, files follow `<stage>_teaching_rules_<level>_<step/word>.md`
  (stages: warmup, leadin, word, sentence, wrapup).
- Shared reference material lives in `notes/` (teacher moves, action-tag library,
  turn-taking timing) — templates cook from those libraries regardless of level.
