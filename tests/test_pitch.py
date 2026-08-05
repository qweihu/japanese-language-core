import unittest

from japanese_language_core.dictionary import classify, pattern


class PitchTests(unittest.TestCase):
    def test_heiban(self):
        self.assertEqual(("H", "H", "H", "H"), pattern(4, 0))
        self.assertEqual("平板 heiban", classify(4, 0))

    def test_atamadaka(self):
        self.assertEqual(("H", "L", "L", "L"), pattern(4, 1))
        self.assertEqual("頭高 atamadaka", classify(4, 1))

    def test_nakadaka(self):
        self.assertEqual(("H", "H", "L", "L"), pattern(4, 2))
        self.assertEqual("中高 nakadaka", classify(4, 2))

    def test_odaka(self):
        self.assertEqual(("H", "H", "H", "H"), pattern(4, 4))
        self.assertEqual("尾高 odaka", classify(4, 4))


if __name__ == "__main__":
    unittest.main()
