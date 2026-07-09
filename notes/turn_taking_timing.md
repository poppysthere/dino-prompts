# Turn-taking & silence timing (L1, ages 4-6)

Two different timers — they fail in opposite ways. Both are system config
(VAD / session settings), not prompts. Block A reacts to the "silent for x seconds"
message without hardcoding any number, so timers can be tuned freely.

## Timer 1 — end-of-speech detection (child started talking; when are they done?)
- Problem: adult defaults (0.5-0.8s trailing silence) cut kids off mid-thought
  ("I am... um...... five!" has 1-2s gaps mid-sentence).
- Setting: 1.5-2.0s trailing silence before closing the turn.
- During word elicitation ([WORD_EVALUATION] turns): stretch toward 2.5s —
  kids psych themselves up mid-attempt.

## Timer 2 — no-speech timeout (child never starts; fires the silence prompt)
| Situation | Wait |
|---|---|
| Open question (name, feelings, "do you want...") | 6-8s (current 7s is good) |
| Repeat-after-me ("Say it with me — apple!") | 4-5s (imitation is immediate; silence = lost) |
| After 1st re-prompt (2nd wait, same question) | ~5s |
| After 2nd re-prompt (3rd wait) | 4-5s, then ladder moves on |

Rationale: classroom wait-time research (Rowe) — 3s transforms child responses;
L2 children need roughly double (decode English + gather courage). Waits shrink
as the ladder escalates because each re-prompt is easier. Total dead air on one
question ≤ ~20s worst case; beyond that a 4-year-old's attention is gone.

## Implementation rules
1. Any detected speech onset cancels the pending silence prompt (avoid the race
   where the kid starts at 6.8s and the timeout fires at 7.0s over them).
2. Avatar response latency after child finishes: target ≤ 1-1.5s. If LLM+TTS is
   slower, play an instant client-side backchannel ("Ooh!", "Hmm!") — reads as
   listening, not lag.
3. Tune from logs, not from this table: pull "question asked → child speech onset"
   distributions from conversation records, set Timer 2 near p75-p80 per situation
   type. These numbers are starting points.

## Related (not timers)
- Barge-in: if the child talks over the avatar, prefer letting the child win —
  short avatar turns (already enforced by prompts) reduce collisions.
