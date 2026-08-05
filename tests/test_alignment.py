import unittest

from japanese_language_core.reading import align_reading


class AlignmentTests(unittest.TestCase):
    def test_kanji_compound(self):
        pairs = align_reading("日本語", "にほんご")
        self.assertEqual("日本語", "".join(surface for surface, _ in pairs))
        self.assertEqual("にほんご", "".join(reading for _, reading in pairs))

    def test_mixed_kana_and_kanji(self):
        pairs = align_reading("食べる", "たべる")
        self.assertEqual([("食", "た"), ("べ", "べ"), ("る", "る")], pairs)

    def test_ambiguous_compound(self):
        pairs = align_reading("好き嫌い", "すききらい")
        self.assertEqual("好き嫌い", "".join(surface for surface, _ in pairs))
        self.assertEqual("すききらい", "".join(reading for _, reading in pairs))


if __name__ == "__main__":
    unittest.main()
