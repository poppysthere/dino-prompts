#!/usr/bin/env python3
"""Self-tests for the L1 mechanical checker."""

import unittest

import checker_l1


def transcript(family, messages, **extra):
    data = {
        "family": family,
        "case": "unit",
        "teacher_name": "Kim",
        "messages": messages,
    }
    data.update(extra)
    return data


class L1CheckerTests(unittest.TestCase):
    def test_leadin_welcomes_child_before_video(self):
        data = transcript(
            "leadin_pre",
            [
                {
                    "role": "assistant",
                    "text": "Hi, Mia. I'm Kim. Welcome to class. Say hi to me.[TEACHER_LISTEN][STUDENT_TALK]",
                },
                {"role": "user", "text": "Hi!"},
                {
                    "role": "assistant",
                    "text": "Hi. It's nice to meet you. Today, we learn food words. First, watch Chef Boo. Then, say the words. Let's watch.[TEACHER_POINT_TO_SCREEN][NEXT_STEP]",
                },
            ],
            max_replies=2,
        )
        self.assertEqual(checker_l1.check(data), [])

    def test_leadin_cannot_jump_straight_to_video(self):
        data = transcript(
            "leadin_pre",
            [
                {
                    "role": "assistant",
                    "text": "Hi. Today we play with food. Let's watch Chef Boo.[TEACHER_POINT_TO_SCREEN][NEXT_STEP]",
                }
            ],
            max_replies=1,
        )
        issues = checker_l1.check(data)
        self.assertTrue(any("[opening]" in issue for issue in issues))

    def test_good_name_answer_then_apple(self):
        data = transcript(
            "word_apple",
            [
                {
                    "role": "assistant",
                    "text": "Look. Boo has an apple.[TEACHER_BITE_APPLE] Listen first. Apple. Now you try. Apple.[TEACHER_LISTEN][STUDENT_TALK]",
                },
                {"role": "user", "text": "What's your name?"},
                {
                    "role": "assistant",
                    "text": "I'm Kim. Listen first. Apple. Your turn. Apple.[TEACHER_LISTEN][STUDENT_TALK]",
                },
                {"role": "user", "text": "apple"},
                {
                    "role": "assistant",
                    "text": "Nice work.[TEACHER_APPLAUD] Apple starts with A. Let's play with A.[TEMPLATE_FINISH]",
                },
            ],
            max_replies=3,
        )
        self.assertEqual(checker_l1.check(data), [])

    def test_question_cannot_be_ignored(self):
        data = transcript(
            "word_apple",
            [
                {
                    "role": "assistant",
                    "text": "Look. Boo has an apple. Listen first. Apple. Now you try. Apple.[TEACHER_LISTEN][STUDENT_TALK]",
                },
                {"role": "user", "text": "What's your name?"},
                {
                    "role": "assistant",
                    "text": "Listen first. Apple. Your turn. Apple.[TEACHER_LISTEN][STUDENT_TALK]",
                },
                {"role": "user", "text": "apple"},
                {
                    "role": "assistant",
                    "text": "Nice work. Apple starts with A. Let's play with A.[TEMPLATE_FINISH]",
                },
            ],
            max_replies=3,
        )
        issues = checker_l1.check(data)
        self.assertTrue(any("[answer-name]" in issue for issue in issues))
        self.assertTrue(any("[child-first]" in issue for issue in issues))

    def test_clear_instruction_directly_answers_what_to_do(self):
        data = transcript(
            "word_apple",
            [
                {
                    "role": "assistant",
                    "text": "Look. Boo has an apple. Listen first. Apple. Now you try. Apple.[TEACHER_LISTEN][STUDENT_TALK]",
                },
                {"role": "user", "text": "What do I do?"},
                {
                    "role": "assistant",
                    "text": "Listen first. Then you say apple. Apple.[TEACHER_LISTEN][STUDENT_TALK]",
                },
                {"role": "user", "text": "apple"},
                {
                    "role": "assistant",
                    "text": "Nice work. Apple starts with A. Let's play with A.[TEMPLATE_FINISH]",
                },
            ],
            max_replies=3,
        )
        self.assertEqual(checker_l1.check(data), [])

    def test_richer_answer_can_finish(self):
        data = transcript(
            "sentence_like_bread",
            [
                {
                    "role": "assistant",
                    "text": "Look. Boo eats the bread. Munch munch. Listen first. I like bread. Now you try. I like bread.[TEACHER_LISTEN][STUDENT_TALK]",
                },
                {"role": "user", "text": "I really like bread."},
                {
                    "role": "assistant",
                    "text": "You really like bread. Me too. Great sentence.[TEACHER_APPLAUD] I like bread.[NEXT_STEP]",
                },
            ],
            max_replies=2,
            reply_require={"2": ["really like bread", "Great sentence"]},
        )
        self.assertEqual(checker_l1.check(data), [])

    def test_hard_question_is_rejected(self):
        data = transcript(
            "wrapup",
            [
                {
                    "role": "assistant",
                    "text": "Look at Boo's food. Apple, juice, and bread. Was class fun? Say yes or no.[TEACHER_LISTEN][STUDENT_TALK]",
                },
                {"role": "user", "text": "yes"},
                {
                    "role": "assistant",
                    "text": "Do you want Chef Boo's food? Now let's sing.[TEACHER_POINT_TO_SCREEN][NEXT_STEP]",
                },
            ],
            max_replies=2,
        )
        issues = checker_l1.check(data)
        self.assertTrue(any("[hard-output]" in issue for issue in issues))

    def test_long_sentence_is_rejected(self):
        data = transcript(
            "leadin_post",
            [
                {
                    "role": "assistant",
                    "text": "Chef Boo has food. Now we will learn many very lovely new English words together.[TEMPLATE_FINISH]",
                }
            ],
            max_replies=1,
        )
        issues = checker_l1.check(data)
        self.assertTrue(any("[pre-a1-length]" in issue for issue in issues))

    def test_v2_action_cannot_interrupt_tts(self):
        data = transcript(
            "word_apple",
            [
                {
                    "role": "assistant",
                    "text": "Look. Boo has an apple.[TEACHER_BITE_APPLE] Listen first. Apple. Now you try. Apple.[TEACHER_LISTEN][STUDENT_TALK]",
                }
            ],
            prompt_version="v2",
            max_replies=1,
        )
        issues = checker_l1.check(data)
        self.assertTrue(any("[action-timing]" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
