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
    # can-you-say ban (question marks bend the melody kids copy). Then
    # -> 1210 (device #372667, second-round retest): real-name-always-greeted
    # ("yana" got a no-name hello), the meaning-question row ("什么意思？"
    # must get a SHOWN answer, never "That's okay"), and the feed-is-B2-only
    # law (the feed ran as a FOURTH wait to a child who already said hi).
    # Then -> 1310: babble-is-a-turn row + only-reply-3-launches (live flake:
    # a babble at B2 got the launch, stealing the child's turn). Not creep.
    "leadin_teaching_rules_trial_step_pre_video.md": (70, 1310),
    # Raised 1000 -> 1100 (device #367710-15: verbatim who-line repeat to a
    # confused child, doubled catches): menu-fed ask, confusion branch, and
    # the say-nothing-twice law. Then -> 1150: missing-catch bad examples
    # (IDK ignored, scared kid closed early) from the live battery. Then
    # -> 1190 (device #368551-56): the agreement row ("Sure." re-triggered
    # the whole B1 line), kid-words ban (mystery/neither), ask-back door
    # question. Then -> 1205: no-comfort-on-silence (live flake: "It's okay!"
    # to a child who said nothing). Then -> 1520 (second-round retest, one
    # recalibration for four pinned bugs): opt-out closes the page early
    # (opt-out is sacred), beat-stuffing (B1+B2 in one reply), the hardened
    # never-grows counter law (dead-ask loop returned on device), and the
    # fabricated-guess ban (device #374194: "I don't know" was answered
    # "A dog? Ooh! Maybe!" — a menu word put in the child's mouth). Not creep.
    "leadin_teaching_rules_trial_step_post_video.md": (85, 2150),
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
    # +40: hallucinated-try bad example (silent child celebrated, live flake).
    # +45: opt-out close re-ran "We just look" (live flake, same class as the
    # flamingo page's) — pinned with a bad example.
    # -> 2560: device #375239 (the wonder re-asked at a child who echoed the
    # word again) showed this page missing the sister flamingo page's armor —
    # ported the mechanical one-question check, the dead-words scan and the
    # words-die paragraph. Same round: clap-along retired, the model becomes
    # word -> parts -> word ending on the whole word (user doctrine).
    # -> 2860: the loop reproduced in the battery — the WAIT COUNT spine
    # (flamingo's anchor for the same bug) ported in, plus the catch-list
    # rows declared dead once the wonder is out (a confused question at the
    # close resurrected the retry in a live round), plus two live-flake pins
    # (reply 1's shape re-run at a "刺猬!" reply 2; opt-out words re-run at
    # the close). Parity with the sister page's armor — not creep.
    # -> 3020: three more live-flake pins (handoff dropped from the close;
    # silent page closed a beat early; the guessed-before scan skipped),
    # the ?-scan (any "?" above = the wonder is out = close, simpler than
    # remembering the wonder's words), and the page boundary on the
    # guessed-before variant (a 刺猬 ON this page kept re-running reply 1).
    # -> 3090: the 刺猬 row promoted into REPLY 2 with a full quoted reply
    # (the model copies quoted examples, and reply 1's variant kept winning),
    # then the LAST-REPLY TEST (my last reply ended "?" = this one closes —
    # a one-message check replacing the page-wide scan) + pre-check 1b for
    # the guessed-before opener.
    # -> 3130: the copyable reply-3 quote (the loop's attractor string)
    # replaced with prose + the last-reply condition; the common layer's
    # silence ladder explicitly voided (parity with the sister page).
    # -> 3185: a "?" never shares a reply with [TEMPLATE_FINISH] (live flake:
    # the wonder closed the page mid-question). -> 3320: device #375560 —
    # meaning questions answered for real ("A hedgehog is HIM!") and the
    # CONFUSED CLOSE (meaning + comfort, no praise at a lost child).
    # +40: "hedge hog" back to back is the whole word, never "SO close"
    # (live flake: a second retry ran at reply 3).
    "word_teaching_rules_trial_hedgehog.md": (123, 3980),
    "render_content_trial_word_hedgehog.md": (15, 250),
    # Shadow bridge: the repurposed wrap-up (second shadow -> flamingo reveal).
    # Grew 1000 -> 1450 when the user made pre-video a real guess game
    # (3 replies, two child turns) instead of a one-beat tease — the counter
    # law, catch table and dead-line rules came with it. Then -> 1520: the
    # video gained a THIRD shadow (giraffe, next page's secret), so post-video
    # became a second guess round (cheer + who-ask -> catch + forward close)
    # Shadow bridge, split into Forge's two paste slots (was one file with
    # <currentStep> branching). Pre: the 3-reply tall-or-short guess game.
    # Post: guess-blind flamingo cheer + third-shadow round + forward close.
    "bridge_teaching_rules_trial_step_pre_video.md": (66, 1330),
    # Post needed a page-boundary section once the pre script left the file:
    # without it the model counted the pre-video game as its own replies and
    # skipped the flamingo cheer (caught by the split battery). +~130 words.
    "bridge_teaching_rules_trial_step_post_video.md": (61, 1200),
    "render_content_trial_shadow_flamingo.md": (15, 250),
    # Flamingo word page: hedgehog's sibling. Same doctrine load plus the
    # giraffe-secret rows and the made-up-chunk (never echo "mingo") rule.
    # Then +~110 words: three live battery bugs hardened (uncredited bridge
    # win, "Repeat after me" re-used as the retry call, dead ask resurrected
    # after opt-out) — each got a rule tightening + bad example. Then a big
    # recalibration for device round #369924 and the stabilization sweep it
    # triggered: the mishear row (ASR heard "Good morning"), the real-word
    # ladder (Flam. In. Go. — TTS garbled "Fla"), the game-time close (word
    # practice follows), the wait-count spine with the dead-wonder law (the
    # celebration-plus-question loop took FIVE pins to kill — the verbatim
    # reply-3 example turned out to be the attractor and was removed), and
    # whole-page junk-name discipline. Battery is green 2x in a row at this
    # size; treat it as the ceiling — compact before adding. The clap-along
    # retirement + word->parts->word model (user doctrine) landed within it;
    # +20 for the opt-out fresh-okay-words pin (live flake), +50 for the
    # claims-path wonder re-ask pin (live flake: the "?" written by the claim
    # row was not honored as the wonder), then the ?-scan replacing the
    # dead-words scan (any "?" above = close — simpler and model-checkable),
    # +45: the common layer's silence ladder explicitly voided (it lured a
    # third model out of a silent page, live flake). +40: a "?" never shares
    # a reply with [TEMPLATE_FINISH] (sister-page flake). -> 3630: meaning
    # questions answered for real + the CONFUSED CLOSE (device #375560).
    "word_teaching_rules_trial_flamingo.md": (121, 3990),
    "render_content_trial_word_flamingo.md": (15, 250),
    # Trial wrap-up: pre-video only (the final video ends the class). Recap
    # cheer + one last guess round + the goodbye launch, 2 replies.
    "wrapup_teaching_rules_trial_step_pre_video.md": (63, 1230),
    "render_content_trial_wrap_giraffe.md": (15, 250),
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
