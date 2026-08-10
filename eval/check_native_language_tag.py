#!/usr/bin/env python3
"""Ensure the experimental prompts use Prompt Forge's nativeLanguage variable."""
from pathlib import Path


ROOT = Path(__file__).parent.parent
COMMON = ROOT / "experiments/common_teaching_simple_rules_language_rescue.md"
PROMPTS = [
    COMMON,
    ROOT / "experiments/word_teaching_rules_l2_cow_language_rescue.md",
    ROOT / "experiments/word_teaching_rules_l2_cat_language_rescue.md",
    ROOT / "experiments/word_teaching_rules_l2_horse_language_rescue.md",
]
RUNNERS = [
    ROOT / "eval/run_word_language_rescue.py",
    ROOT / "eval/run_cat_language_rescue.py",
    ROOT / "eval/run_horse_language_rescue.py",
]


def main():
    issues = []
    common = COMMON.read_text()
    exact_block = "<nativeLanguage>\n{{nativeLanguage}}\n</nativeLanguage>"
    if exact_block not in common:
        issues.append("common prompt is missing the exact nativeLanguage block")

    for path in PROMPTS:
        text = path.read_text()
        if "supportLanguage" in text:
            issues.append(f"{path.name}: legacy supportLanguage remains")
        if "{{nativeLanguage}}" not in text:
            issues.append(f"{path.name}: nativeLanguage variable is missing")

    for path in RUNNERS:
        text = path.read_text()
        if '"nativeLanguage": support_language' not in text:
            issues.append(f"{path.name}: eval does not inject nativeLanguage")
        if '"supportLanguage"' in text:
            issues.append(f"{path.name}: eval still injects supportLanguage")

    if issues:
        for issue in issues:
            print(f"FAIL {issue}")
        return 1

    print("PASS nativeLanguage tag contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
