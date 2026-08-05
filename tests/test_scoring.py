import unittest

from japanese_language_core.dictionary import (
    DifficultyProfile,
    difficulty_label,
    readability,
)


class ScoringTests(unittest.TestCase):
    def test_readability_high_for_easy(self):
        profile = DifficultyProfile(levels={"n5": 4, "unknown": 1})
        score = readability(profile)
        self.assertGreater(score, 3.0)
        self.assertEqual("easy", difficulty_label(score))

    def test_readability_penalizes_unknown(self):
        easy = DifficultyProfile(levels={"n5": 4, "unknown": 1})
        harder = DifficultyProfile(levels={"n5": 4, "unknown": 4})
        self.assertGreater(readability(easy), readability(harder))

    def test_difficulty_label(self):
        self.assertEqual("medium", difficulty_label(3.0))
        self.assertEqual("hard", difficulty_label(1.5))


if __name__ == "__main__":
    unittest.main()
