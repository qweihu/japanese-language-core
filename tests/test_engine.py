import unittest

from japanese_reading_core import (
    EngineUnavailableError,
    ReadingToken,
    SudachiEngine,
    create_engine,
    to_hiragana,
)


class ReadingEngineTests(unittest.TestCase):
    def test_source_preservation_with_context_engine(self):
        tokens = tuple(create_engine("sudachi").tokens("雨が降り止む\n帰る"))
        self.assertTrue(all(isinstance(token, ReadingToken) for token in tokens))
        self.assertEqual("雨が降り止む\n帰る", "".join(token.orig for token in tokens))

    def test_contextual_compound_reading(self):
        tokens = tuple(SudachiEngine().tokens("雨が降り止むまでは帰れない"))
        readings = [(token.orig, token.hira) for token in tokens if token.hira]
        self.assertIn(("降り止む", "ふりやむ"), readings)

    def test_whitespace_and_newlines_are_tokens(self):
        text = "  日本語\r\n\tを読む"
        tokens = tuple(create_engine("sudachi").tokens(text))
        self.assertEqual(text, "".join(token.orig for token in tokens))
        self.assertIn("\r\n", [token.orig for token in tokens])

    def test_pykakasi_engine_is_selectable(self):
        tokens = tuple(create_engine("pykakasi").tokens("日本語"))
        self.assertEqual("日本語", "".join(token.orig for token in tokens))
        self.assertTrue(any(token.hira for token in tokens))

    def test_invalid_engine_name_is_rejected(self):
        with self.assertRaises(ValueError):
            create_engine("unknown")

    def test_katakana_normalization(self):
        self.assertEqual("にほんご", to_hiragana("ニホンゴ"))


if __name__ == "__main__":
    unittest.main()
