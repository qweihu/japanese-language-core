from __future__ import annotations

import unittest

from japanese_language_core.reading import ReadingToken
from scripts.evaluate_readings import _edit_distance, _normalize, evaluate


class FakeEngine:
    name = "fake"

    def tokens(self, text):
        if text == "食べる。":
            return [ReadingToken("食べる", "たべる"), ReadingToken("。", "。")]
        return [ReadingToken(text, text)]


class ReadingEvaluationTests(unittest.TestCase):
    def test_normalizes_katakana_and_whitespace_but_keeps_punctuation(self):
        self.assertEqual(_normalize("ﾆﾎﾝ  ゴ。"), "にほんご。")

    def test_edit_distance_handles_insertions_deletions_and_substitutions(self):
        self.assertEqual(_edit_distance("にほん", "にほん"), 0)
        self.assertEqual(_edit_distance("にほん", "にっぽん"), 2)

    def test_evaluation_uses_reviewed_cases_and_scores_ruby_spans(self):
        report = evaluate(
            [
                {
                    "id": "reviewed",
                    "domain": "ordinary",
                    "text": "食べる。",
                    "reference_reading": "たべる。",
                    "reference_ruby_spans": [
                        {"start": 0, "end": 1, "reading": "た"}
                    ],
                    "review_status": "reviewed",
                    "reviewer": "Test Reviewer",
                    "review_basis": "fixed unit-test fixture",
                    "reviewed_at": "2026-01-01",
                },
                {
                    "id": "draft",
                    "domain": "lyrics",
                    "text": "夢",
                    "reference_reading": "ゆめ",
                    "review_status": "pending_review",
                },
            ],
            FakeEngine(),
        )

        self.assertEqual(report["cases"], 1)
        self.assertEqual(report["cer"], 0)
        self.assertEqual(report["ruby_spans"]["f1"], 1)
        self.assertEqual(set(report["by_domain"]), {"ordinary"})

    def test_reviewed_case_requires_traceable_human_review_metadata(self):
        case = {
            "id": "reviewed",
            "text": "食べる。",
            "reference_reading": "たべる。",
            "review_status": "reviewed",
        }
        with self.assertRaisesRegex(ValueError, "needs a reviewer"):
            evaluate([case], FakeEngine())

        case.update(
            reviewer="Test Reviewer",
            review_basis="reviewed Japanese reading",
            reviewed_at="2026-01-01",
        )
        report = evaluate([case], FakeEngine())
        self.assertEqual(report["cases"], 1)

    def test_reviewed_case_requires_iso_review_date(self):
        case = {
            "id": "reviewed",
            "text": "食べる。",
            "reference_reading": "たべる。",
            "review_status": "reviewed",
            "reviewer": "Test Reviewer",
            "review_basis": "reviewed Japanese reading",
            "reviewed_at": "2026/01/01",
        }
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            evaluate([case], FakeEngine())

    def test_unreviewed_cases_are_excluded_unless_explicitly_requested(self):
        draft = [{
            "id": "draft",
            "text": "夢",
            "reference_reading": "ゆめ",
            "review_status": "pending_review",
        }]
        with self.assertRaisesRegex(ValueError, "no reviewed cases"):
            evaluate(draft, FakeEngine())

        report = evaluate(draft, FakeEngine(), include_unreviewed=True)
        self.assertEqual(report["review_scope"], "all cases (exploratory)")


if __name__ == "__main__":
    unittest.main()
