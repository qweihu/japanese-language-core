import io
import json
import unittest
import zipfile

from japanese_language_core.dictionary import YomitanDictionary


def make_fixture(path):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "index.json",
            json.dumps(
                {
                    "title": "Test Dict",
                    "format_version": 3,
                    "author": "tester",
                }
            ),
        )
        archive.writestr(
            "term_bank_1.json",
            json.dumps(
                [
                    ["日本語", "にほんご", ["language"], [], 0, ["Japanese language"], 100, ["jlptN5"]],
                    ["食べる", "たべる", ["v1"], [], 0, ["to eat"], 101, []],
                ]
            ),
        )
        archive.writestr(
            "term_meta_bank_1.json",
            json.dumps([["日本語", "freq", 42], ["食べる", "pitch", [{"position": 2, "category": "heiban"}]]]),
        )
        archive.writestr(
            "kanji_bank_1.json",
            json.dumps([["日", ["ニチ", "ジツ"], ["ひ"], ["n5"], ["day"], {"grade": 1, "stroke_count": 4}]]),
        )
        archive.writestr(
            "tag_bank_1.json",
            json.dumps([["jlptN5", "level", 0, "JLPT N5"]]),
        )


class YomitanDictionaryTests(unittest.TestCase):
    def test_parse_and_lookup(self):
        buffer = io.BytesIO()
        make_fixture(buffer)
        path = "/private/tmp/fixture-yomitan.zip"
        with open(path, "wb") as handle:
            handle.write(buffer.getvalue())
        dictionary = YomitanDictionary(path)
        terms = dictionary.lookup_terms("日本語")
        self.assertEqual(1, len(terms))
        self.assertEqual("にほんご", terms[0].reading)
        self.assertEqual(42, terms[0].frequency.value)
        taberu = dictionary.lookup_terms("食べる")[0]
        self.assertEqual(2, taberu.pitch_accents[0].position)
        kanji = dictionary.lookup_kanji("日")
        self.assertEqual("日", kanji[0].character)
        self.assertIn("jlptN5", dictionary.tags())

    def test_validate_reports_structural_errors(self):
        path = "/private/tmp/fixture-empty-yomitan.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("index.json", json.dumps({"format_version": 3}))
        dictionary = YomitanDictionary(path)
        errors = dictionary.validate()
        self.assertTrue(any("title" in error for error in errors))
        self.assertTrue(any("term_bank" in error for error in errors))

    def test_meta_variants(self):
        path = "/private/tmp/fixture-meta-yomitan.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "index.json",
                json.dumps({"title": "Meta Test", "format_version": 3}),
            )
            archive.writestr(
                "term_bank_1.json",
                json.dumps([["食べる", "たべる", [], [], 0, ["to eat"], 1, []]]),
            )
            archive.writestr(
                "term_meta_bank_1.json",
                json.dumps(
                    [
                        ["食べる", "freq", {"frequency": 7}],
                        [
                            "食べる",
                            "pitch",
                            [{"position": 2, "category": "heiban"}, "n/a", 3],
                        ],
                    ]
                ),
            )
        dictionary = YomitanDictionary(path)
        term = dictionary.lookup_terms("食べる")[0]
        self.assertEqual(7, term.frequency.value)
        self.assertEqual(
            [2, 3], [accent.position for accent in term.pitch_accents]
        )


if __name__ == "__main__":
    unittest.main()
