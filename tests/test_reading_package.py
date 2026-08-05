import unittest

from japanese_language_core.reading import ReadingToken, create_engine, to_hiragana


class ReadingPackageTests(unittest.TestCase):
    def test_token_contract(self):
        token = ReadingToken("日本語", "にほんご", "nihongo")
        self.assertEqual("日本語", token.orig)

    def test_hiragana_normalization(self):
        self.assertEqual("にほんご", to_hiragana("ニホンゴ"))

    def test_engine_factory_importable(self):
        self.assertTrue(callable(create_engine))


if __name__ == "__main__":
    unittest.main()
