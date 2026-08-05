import json
import unittest
import zipfile

from japanese_language_core.dictionary import YomitanDictionary


def make_fixture(path):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "index.json",
            json.dumps({"title": "JMnedict Test", "format_version": 3}),
        )
        archive.writestr(
            "term_bank_1.json",
            json.dumps(
                [
                    ["山田", "", ["surname"], [], 0, ["やまだ"], 1, ["surname"]],
                    ["東京", "とうきょう", ["place"], [], 0, ["Tokyo"], 2, ["place"]],
                    ["日本語", "にほんご", [], [], 0, ["Japanese language"], 3, []],
                ]
            ),
        )


class JmnedictTests(unittest.TestCase):
    def setUp(self):
        self.path = "/private/tmp/fixture-jmnedict.zip"
        make_fixture(self.path)
        self.dictionary = YomitanDictionary(self.path)

    def test_lookup_names_surname(self):
        names = self.dictionary.lookup_names("山田")
        self.assertEqual(1, len(names))
        self.assertEqual(("やまだ",), names[0].readings)
        self.assertIn("surname", names[0].categories)

    def test_lookup_names_place(self):
        names = self.dictionary.lookup_names("東京")
        self.assertEqual(1, len(names))
        self.assertEqual(("とうきょう",), names[0].readings)
        self.assertIn("place", names[0].categories)

    def test_regular_term_is_not_name(self):
        self.assertEqual([], self.dictionary.lookup_names("日本語"))


if __name__ == "__main__":
    unittest.main()
