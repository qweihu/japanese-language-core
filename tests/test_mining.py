import json
import unittest
import zipfile

from japanese_language_core.dictionary import YomitanDictionary
from japanese_language_core.export import (
    MiningUnit,
    detect_expression,
    mining_payload,
    mining_tsv,
)


def make_dictionary(path):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "index.json",
            json.dumps({"title": "Mining Test", "format_version": 3}),
        )
        archive.writestr(
            "term_bank_1.json",
            json.dumps(
                [
                    ["日本語", "にほんご", [], [], 0, ["Japanese language"], 1, []],
                    ["勉強", "べんきょう", [], [], 0, ["study"], 2, []],
                ]
            ),
        )


class MiningTests(unittest.TestCase):
    def setUp(self):
        self.path = "/private/tmp/fixture-mining.zip"
        make_dictionary(self.path)
        self.dictionary = YomitanDictionary(self.path)

    def test_detect_expression(self):
        self.assertEqual(
            "日本語", detect_expression("日本語を勉強する。", self.dictionary)
        )
        self.assertEqual("", detect_expression("こんにちは。", self.dictionary))

    def test_mining_unit_to_note(self):
        unit = MiningUnit(
            sentence="日本語を勉強する。",
            translation="学习日语。",
            expression="日本語",
            reading="にほんご",
            tags=["jlptN5"],
        )
        note = unit.to_note()
        self.assertEqual("日本語", note.expression)
        self.assertEqual(["jlptN5"], note.tags)
        self.assertTrue(mining_tsv([unit]).startswith("Expression"))

    def test_mining_payload(self):
        unit = MiningUnit(sentence="勉強する。", expression="勉強")
        payloads = mining_payload(
            [unit], deck_name="Mining", model_name="Basic"
        )
        self.assertEqual(1, len(payloads))
        note = payloads[0]["params"]["note"]
        self.assertEqual("Mining", note["deckName"])
        self.assertEqual("勉強", note["fields"]["Expression"])


if __name__ == "__main__":
    unittest.main()
