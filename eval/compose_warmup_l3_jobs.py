#!/usr/bin/env python3
"""Compose the L3 warm-up battery into a jobs.json the browser runner can replay.

The shell cannot reach the Forge ALB (network policy), so the battery is driven
from the Forge page itself via CDP. This script does the composition half:
common_l3 + warmup_l3 with placeholders filled, one job per case run.

Usage: python3 eval/compose_warmup_l3_jobs.py > eval/runs/l3jobs.json
"""
import json
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).parent.parent

ROLE = (
    "You are Max, a bold, energetic jungle captain who turns every lesson into a thrilling mission. "
    "Your voice is loud and bright. You inspire children to be brave and speak up."
)

TOMMY_PROFILE = (
    "基础信息: 称呼：Tommy\n"
    '行为画像: {"summary": "A shy but engaged learner", "personality": "Shy yet engaged; prefers a gentle tone."}'
)


def compose(is_first_meet: bool, name: str, profile: str = "No relevant information.") -> str:
    common = (ROOT / "prompts/l3/common_teaching_simple_rules_l3.md").read_text()
    tmpl = (ROOT / "prompts/l3/warmup_teaching_rules_l3.md").read_text()
    mapping = {
        "roleDescription": ROLE,
        "renderContent": "Warm up stage. No lesson content yet.",
        "studentProfile": profile,
        "name": name,
        "isFirstMeet": "true" if is_first_meet else "false",
    }
    text = common.rstrip() + "\n\n" + tmpl.rstrip()
    for k, v in mapping.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def main():
    battery = yaml.safe_load((ROOT / "eval/cases_warmup_l3.yaml").read_text())
    jobs = []
    groups = [
        ("path_a", True, "heidi", "heidi", None),
        ("path_a_extra", True, "heidi", "heidi", None),
        ("path_b", False, "tom", "tom", None),
        # real name + profile carrying a stale 称呼 (prod 7710190001)
        ("path_b_heidi", False, "heidi", "heidi", TOMMY_PROFILE),
        # junk default: prompt sees test_user, checker sees no default name
        # (the whole point is that the junk value must never be heard).
        ("l3_broken", False, "test_user", "", None),
    ]
    for group, first_meet, prompt_name, checker_name, profile in groups:
        system = compose(first_meet, prompt_name, profile or "No relevant information.")
        for case in battery.get(group, []):
            jobs.append({
                "id": case["id"],
                "group": group,
                "system": system,
                "turns": case.get("turns", []),
                "is_first_meet": first_meet,
                "student_name": checker_name,
                "spoken_name": case.get("spoken_name", ""),
                "spoken_name_l1": case.get("spoken_name_l1", ""),
                "forbid_phrases": case.get("forbid_phrases", []),
                "require_phrases": case.get("require_phrases", []),
                "max_beats": case.get("max_beats"),
            })
    json.dump(jobs, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
