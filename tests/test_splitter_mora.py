import unittest

from japanese_language_core.reading import count_mora, mora_segments, split_sentences


class SplitterTests(unittest.TestCase):
    def test_split_sentences(self):
        text = "こんにちは。元気ですか？"
        self.assertEqual(["こんにちは。", "元気ですか？"], split_sentences(text))

    def test_split_keeps_terminator(self):
        parts = split_sentences("行こう！明日だ。")
        self.assertEqual("行こう！", parts[0])
        self.assertEqual("明日だ。", parts[1])


class MoraTests(unittest.TestCase):
    def test_mora_counts(self):
        self.assertEqual(4, count_mora("がっこう"))
        self.assertEqual(4, count_mora("にほんご"))
        self.assertEqual(2, count_mora("きょう"))
        self.assertEqual(5, count_mora("こんにちは"))

    def test_segments_skip_small_kana(self):
        self.assertEqual(["き", "う"], mora_segments("きょう"))


if __name__ == "__main__":
    unittest.main()
