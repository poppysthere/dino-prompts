"""Offline harness/checker regression tests. No model or credentials required."""
import unittest

import checker_l2_v3
import checker_word_l2_v3
import run_l2_v3_forge as runner
from checker_l2_human import check_child_first


class L2V3Tests(unittest.TestCase):
    def test_all_active_templates_and_variables(self):
        cases = runner.load_cases()
        self.assertEqual(len(cases), 11)
        self.assertEqual(sum(map(len, cases.values())), 107)
        for family, group in cases.items():
            system, _, _ = runner.compose(family, group[0])
            self.assertNotIn("{{", system)
            self.assertIn("ASCII", system)
            self.assertIn("#", system)
            text = (runner.PROMPT_DIR / runner.FAMILIES[family]["template"]).read_text()
            self.assertGreater(len(text), 300)

    def test_raw_punctuation_and_laughs(self):
        checker_l2_v3.self_test()

    def test_ignored_question_fails(self):
        messages = [{"role": "user", "text": "What's your name?"},
                    {"role": "assistant", "text": "Moo moo. Does the cow have the cake?"}]
        self.assertTrue(check_child_first(messages, "Max", "word_cow"))

    def test_action_timing(self):
        self.assertIsNotNone(checker_word_l2_v3.action_with_later_speech(
            "Cow.[TEACHER_COW_HORNS] Your turn.[TEACHER_LISTEN][STUDENT_TALK]"))
        self.assertIsNone(checker_word_l2_v3.action_with_later_speech(
            "Cow. Your turn.[TEACHER_COW_HORNS][TEACHER_LISTEN][STUDENT_TALK]"))

    def test_silent_failure_of_sound_help_is_detected(self):
        transcript = {"messages": [{"role": "assistant", "text": "Cat."},
             {"role": "assistant", "text": "Yes, cat. A cat says meow."}],
             "v3_require": {"2": [r"/æ/"]}, "v3_forbid": {"2": [r"^Yes"]}}
        self.assertEqual(len(checker_l2_v3.check_extra(transcript)), 2)

    def test_v2_fixture_not_mutated(self):
        # extend_cases expects real family keys; test using the complete base data.
        import run_l2_forge
        baseline = run_l2_forge.load_cases()
        import copy
        saved = copy.deepcopy(baseline)
        checker_l2_v3.extend_cases(baseline)
        self.assertEqual(baseline, saved)


if __name__ == "__main__":
    unittest.main()
