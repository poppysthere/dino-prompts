# L1 backlog — fixes waiting for the production freeze to lift

L1 is live in production (2026-07). No L1 template changes until Heidi says go.
Every L2 fix that also applies to L1 gets a row here instead.

| Date | Fix (already live in L2) | L1 files affected when unfrozen |
|---|---|---|
| 07-14 | Echo-translation ban: never speak a translation of the child's words ("知道。" → "Know.") | word/sentence/wrapup close catches |
| 07-14 | Lone "知道" = ASR-truncated "不知道", treat as "I don't know" | word/sentence/wrapup answer rows |
| 07-14 | ASR-mishear whitelists per target word (cow="How?"; L1 words apple/bread/juice need their own observed mishears from logs first — do not guess) | word templates |
| 07-14 | One-way-street script invariant + pinned silent-page sequence (stops retry loops and wonder-question repeats) | word templates (L1 uses the older structure; port the invariant wording, not the L2 rows) |
| 07-14 | Wonder-style checklist question asked exactly once, only after its invite row | word templates |
