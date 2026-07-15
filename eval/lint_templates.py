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
    "warmup_teaching_rules_l3.md": (85, 1200),
    "leadin_teaching_rules_l3_step_pre_video.md": (40, 600),
    "leadin_teaching_rules_l3_step_post_video.md": (65, 1000),
    # Festival: 足球课 (World Cup soccer, 4-6, pre-A1) — keep lean.
    "common_teaching_simple_rules_l1_soccer.md": (95, 1450),
    "warmup_teaching_rules_l1_soccer.md": (100, 1450),
    "leadin_teaching_rules_l1_soccer_step_pre_video.md": (40, 600),
    "leadin_teaching_rules_l1_soccer_step_post_video.md": (55, 900),
    "word_teaching_rules_l1_soccer.md": (100, 1700),
    "wrapup_teaching_rules_l1_soccer.md": (75, 1100),
}


def main():
    bad = 0
    files = []
    for level in ("l2", "l3"):
        files += sorted((ROOT / "prompts" / level).glob("*.md"))
    files += sorted((ROOT / "prompts/festival").glob("*.md"))
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
