#!/usr/bin/env python3
"""Template size lint — the mechanical guard against prompt bloat.

Every fix must fit the budget: fold new knowledge into existing rules/lists,
swap examples one-in-one-out, never append case after case. If this lint fails,
the fix goes back for compaction, not the budget up.

L2, L3 and the festival lessons are linted — the legacy L1 _l1l2_ files are
frozen in production and stay unlinted.
Exit 0 = all within budget, 1 = over budget.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent

# (max lines, max words) per template; default covers the fixed-script pages.
DEFAULT_BUDGET = (115, 1800)
BUDGETS = {
    "warmup_teaching_rules_l2_lesson0.md": (230, 3600),  # state machine with two paths
    "common_teaching_simple_rules_l2.md": (95, 1500),
    # Word pages are AT their ceiling (mishear whitelists + worked examples for a
    # flaky small model). Frozen at current size: any new fix must be net-zero,
    # and the next compaction pass should push them back toward the default.
    "word_teaching_rules_l2_cow.md": (100, 1850),
    "word_teaching_rules_l2_cat.md": (102, 1900),
    "word_teaching_rules_l2_horse.md": (105, 2100),
    # L3 (7-9, A1+): started lean on purpose — keep it that way.
    "common_teaching_simple_rules_l3.md": (95, 1500),
    # Warm-up budgets raised twice on 2026-07-17 (devices #365995 and #366244:
    # the production model copies example lines verbatim — a Leo role said
    # "I'm Kim", then a heidii student was greeted "Tom!"): both the teacher
    # name and the Path B student name now carry TWO contrasting examples so
    # blind copying is impossible. Deliberate recalibration, not creep —
    # trim before raising again.
    "warmup_teaching_rules_l3.md": (90, 1300),
    "leadin_teaching_rules_l3_step_pre_video.md": (40, 600),
    "leadin_teaching_rules_l3_step_post_video.md": (65, 1000),
    # L5 (11-12, A2+): same lean shape as L3.
    "common_teaching_simple_rules_l5.md": (100, 1600),
    "warmup_teaching_rules_l5.md": (95, 1400),  # raised twice, see warmup_l3 note
    "leadin_teaching_rules_l5_step_pre_video.md": (40, 650),
    "leadin_teaching_rules_l5_step_post_video.md": (70, 1100),
    # Festival: 足球课 (World Cup soccer, 4-6, pre-A1) — keep lean.
    "common_teaching_simple_rules_l1_soccer.md": (95, 1450),
    "warmup_teaching_rules_l1_soccer.md": (100, 1550),  # raised twice, see warmup_l3 note
    "leadin_teaching_rules_l1_soccer_step_pre_video.md": (40, 600),
    "leadin_teaching_rules_l1_soccer_step_post_video.md": (55, 900),
    # Raised 1700 -> 1950 -> 2100 across two device-bug rounds (#360356 and
    # the 22:00 opt-out run): HUMAN RULE, invite budget, opt-out doctrine.
    # Deliberate recalibration, not creep — trim before raising again.
    "word_teaching_rules_l1_soccer.md": (100, 2100),
    "wrapup_teaching_rules_l1_soccer.md": (75, 1100),
    # Trial: 新手引导体验课 demo (Fox's birthday party, 4-6, pre-A1) — first
    # contact with the product, keep lean. render_content_* is data, not prompt.
    "common_teaching_simple_rules_l1_trial.md": (110, 1600),
    # Raised 850 -> 950: page grew from 2 to 3 beats (hello-only small win,
    # then celebrate/feed, then launch) per product decision. Then -> 1050
    # (device #368067-75): greeting-once law + profile-nickname guard, both
    # real device bugs ported from the warm-up family. Then -> 1060
    # (user doctrine, round #368532): "Repeat after me." feed format + the
    # can-you-say ban (question marks bend the melody kids copy). Not creep.
    "leadin_teaching_rules_trial_step_pre_video.md": (65, 1060),
    # Raised 1000 -> 1100 (device #367710-15: verbatim who-line repeat to a
    # confused child, doubled catches): menu-fed ask, confusion branch, and
    # the say-nothing-twice law. Then -> 1150: missing-catch bad examples
    # (IDK ignored, scared kid closed early) from the live battery. Then
    # -> 1190 (device #368551-56): the agreement row ("Sure." re-triggered
    # the whole B1 line), kid-words ban (mystery/neither), ask-back door
    # question. Not creep.
    "leadin_teaching_rules_trial_step_post_video.md": (70, 1190),
    "render_content_trial_leadin.md": (30, 400),
    # The hedgehog reveal page: inherits the soccer word page's HUMAN RULE +
    # invite budget doctrine, plus the syllable-ladder section. Raised
    # 2000 -> 2050 after device #368306-12: six new doctrines in one round
    # (no door re-opening, "You say" call, piece handling, kid-sized close,
    # clap-only-in-reply-2, no close at reply 1). Then -> 2070 (user doctrine,
    # round #368532): the call became "Repeat after me. Hedgehog!" and the
    # can-you-say ban. Then -> 2140: the close gained the party handoff
    # ("Let's go back to the party!") because the flamingo bridge follows.
    # Deliberate recalibrations, not creep.
    "word_teaching_rules_trial_hedgehog.md": (105, 2140),
    "render_content_trial_word_hedgehog.md": (15, 250),
    # Shadow bridge: the repurposed wrap-up (second shadow -> flamingo reveal).
    # Grew 1000 -> 1450 when the user made pre-video a real guess game
    # (3 replies, two child turns) instead of a one-beat tease — the counter
    # law, catch table and dead-line rules came with it. Deliberate.
    "shadow_bridge_rules_trial_flamingo.md": (90, 1450),
    "render_content_trial_shadow_flamingo.md": (15, 250),
}


def main():
    bad = 0
    files = []
    for level in ("l2", "l3", "l5"):
        files += sorted((ROOT / "prompts" / level).glob("*.md"))
    files += sorted((ROOT / "prompts/festival").glob("*.md"))
    files += sorted((ROOT / "prompts/trial").glob("*.md"))
    for f in files:
        text = f.read_text()
        lines = len(text.splitlines())
        words = len(text.split())
        max_lines, max_words = BUDGETS.get(f.name, DEFAULT_BUDGET)
        over = lines > max_lines or words > max_words
        bad += over
        mark = "OVER" if over else "ok  "
        print(f"[{mark}] {f.name}: {lines} lines (max {max_lines}), {words} words (max {max_words})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
