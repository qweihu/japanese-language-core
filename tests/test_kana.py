import unittest

from japanese_language_core.reading import (
    is_hiragana,
    is_kanji,
    is_katakana,
    normalize_width,
    to_hiragana,
    to_katakana,
    to_romaji,
)


class KanaTests(unittest.TestCase):
    def test_katakana_to_hiragana(self):
        self.assertEqual("にほんご", to_hiragana("ニホンゴ"))

    def test_hiragana_to_katakana(self):
        self.assertEqual("ニホンゴ", to_katakana("にほんご"))

    def test_halfwidth_katakana_normalized(self):
        self.assertEqual("にほんご", to_hiragana("ﾆﾎﾝｺﾞ"))

    def test_classification(self):
        self.assertTrue(is_hiragana("あ"))
        self.assertTrue(is_katakana("ア"))
        self.assertTrue(is_kanji("日"))
        self.assertFalse(is_hiragana("ア"))

    def test_romaji_hepburn(self):
        self.assertEqual("nihongo", to_romaji("にほんご"))
        self.assertEqual("gakkou", to_romaji("がっこう"))
        self.assertEqual("shimbun", to_romaji("しんぶん"))

    def test_width_normalization_keeps_text(self):
        self.assertEqual("にほんご", normalize_width("ﾆﾎﾝｺﾞ"))


if __name__ == "__main__":
    unittest.main()
