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

    def test_repeated_okurigana_kana_uses_the_later_boundary(self):
        self.assertEqual(
            [("歌", "うた"), ("う", "う")],
            align_reading("歌う", "うたう"),
        )

    def test_ambiguous_okurigana_keeps_a_safe_whole_word_reading(self):
        self.assertEqual([("仮名な", "な")], align_reading("仮名な", "な"))

    def test_ambiguous_compound(self):
        pairs = align_reading("好き嫌い", "すききらい")
        self.assertEqual("好き嫌い", "".join(surface for surface, _ in pairs))
        self.assertEqual("すききらい", "".join(reading for _, reading in pairs))

    def test_ambiguous_compound_documented_greedy(self):
        # Known limitation: greedy gives one valid distribution; community
        # dictionaries (e.g. Jitendex) may distribute kana differently.
        pairs = align_reading("好き嫌い", "すききらい")
        self.assertEqual(
            [("好", "す"), ("き", "き"), ("嫌", "きら"), ("い", "い")], pairs
        )

    def test_all_kana_passthrough(self):
        pairs = align_reading("おねがいいたします", "おねがいいたします")
        self.assertEqual("おねがいいたします", "".join(s for s, _ in pairs))
        self.assertEqual("おねがいいたします", "".join(r for _, r in pairs))

    def test_align_with_furigana(self):
        from japanese_language_core.reading import align_with_furigana

        pairs = align_with_furigana(
            "日本語", "にほんご", {"日": "に", "本": "ほん", "語": "ご"}
        )
        self.assertEqual([("日", "に"), ("本", "ほん"), ("語", "ご")], pairs)

    def test_align_with_furigana_falls_back(self):
        from japanese_language_core.reading import align_with_furigana

        pairs = align_with_furigana("日本語", "にほんご", {"日": "にち"})
        self.assertEqual(align_reading("日本語", "にほんご"), pairs)


if __name__ == "__main__":
    unittest.main()
