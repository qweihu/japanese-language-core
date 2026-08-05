import json
import unittest
from pathlib import Path

from japanese_language_core.reading import create_engine
from japanese_language_core.translation import validate_translation


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "benchmarks" / "tatoeba_sample.json"


class BenchmarkSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SAMPLE.read_text(encoding="utf-8"))
        cls.pairs = cls.data["pairs"]

    def test_sample_metadata(self):
        self.assertIn("license", self.data)
        self.assertIn("Tatoeba", self.data["source"])
        self.assertGreaterEqual(len(self.pairs), 20)

    def test_translation_structure(self):
        errors, _ = validate_translation(
            [pair["ja"] for pair in self.pairs],
            [pair["zh"] for pair in self.pairs],
            paired=True,
        )
        self.assertEqual([], errors)

    def test_reading_source_preservation(self):
        engine = create_engine("pykakasi")
        for pair in self.pairs:
            tokens = tuple(engine.tokens(pair["ja"]))
            self.assertEqual(
                pair["ja"], "".join(token.orig for token in tokens)
            )


if __name__ == "__main__":
    unittest.main()
