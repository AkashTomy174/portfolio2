import unittest

from app.main import (
    _is_assistant_identity_question,
    _is_availability_question,
    _is_experience_question,
    _is_greeting,
    _is_profile_identity_question,
    _is_small_talk,
)


class ShortcutMatchingTests(unittest.TestCase):
    def test_typo_tolerant_shortcuts(self):
        cases = [
            (_is_greeting, "helo"),
            (_is_greeting, "heyy"),
            (_is_greeting, "hi there"),
            (_is_small_talk, "how are yu"),
            (_is_small_talk, "hello how are you"),
            (_is_assistant_identity_question, "who r you"),
            (_is_assistant_identity_question, "what are ya"),
            (_is_assistant_identity_question, "what is your name"),
            (_is_profile_identity_question, "tell me about akash"),
            (_is_profile_identity_question, "who is akash tomy"),
            (_is_experience_question, "experiance"),
            (_is_experience_question, "expereince"),
            (_is_availability_question, "im open to work"),
            (_is_availability_question, "are you available"),
            (_is_availability_question, "looking for a job"),
            (_is_availability_question, "free for call"),
        ]
        for checker, message in cases:
            with self.subTest(message=message):
                self.assertTrue(checker(message))


if __name__ == "__main__":
    unittest.main()
