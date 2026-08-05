import unittest

from japanese_language_core.reading import ReadingToken, create_engine, to_hiragana
from japanese_reading_core import create_engine as legacy_create_engine


class ReadingPackageTests(unittest.TestCase):
    def test_shim_re_exports(self):
        self.assertIs(create_engine, legacy_create_engine)
        self.assertEqual("にほんご", to_hiragana("ニホンゴ"))

    def test_token_contract(self):
        token = ReadingToken("日本語", "にほんご", "nihongo")
        self.assertEqual("日本語", token.orig)


if __name__ == "__main__":
    unittest.main()
