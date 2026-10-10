#!/usr/bin/env python3
"""Evaluate Japanese readings against a provenance-tracked JSON reference set.

Only cases marked ``review_status: reviewed`` are included by default. The
script reports character error rate, exact sentence match, reading coverage,
and optional kanji Ruby-span precision/recall. It does not treat token
segmentation as a correctness target.
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Iterable

from japanese_language_core.reading import (
    ReadingEngine,
    align_reading,
    create_engine,
    is_kanji,
    runtime_metadata,
    to_hiragana,
)


def _normalize(value: str) -> str:
    """Normalize kana spelling and width; ignore whitespace, retain punctuation."""

    normalized = to_hiragana(unicodedata.normalize("NFKC", value))
    return "".join(char for char in normalized if not char.isspace())


def _edit_distance(left: str, right: str) -> int:
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for row, left_char in enumerate(left, start=1):
        current = [row]
        for column, right_char in enumerate(right, start=1):
            current.append(
                min(
                    current[column - 1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def _reference_readings(case: dict) -> tuple[str, ...]:
    values = case.get("reference_readings", case.get("reference_reading"))
    if isinstance(values, str):
        values = [values]
    if (
        not isinstance(values, list)
        or not values
        or any(not isinstance(value, str) or not value for value in values)
    ):
        raise ValueError(f"{case.get('id', '?')}: reference_reading(s) must be non-empty")
    return tuple(_normalize(value) for value in values)


def _ruby_spans(engine: ReadingEngine, text: str) -> set[tuple[int, int, str]]:
    spans: set[tuple[int, int, str]] = set()
    offset = 0
    tokens = tuple(engine.tokens(text))
    if "".join(token.orig for token in tokens) != text:
        raise ValueError("reading engine did not preserve source text")
    for token in tokens:
        if token.hira and any(is_kanji(char) for char in token.orig):
            token_offset = offset
            for surface, reading in align_reading(token.orig, token.hira):
                if reading and any(is_kanji(char) for char in surface):
                    spans.add(
                        (token_offset, token_offset + len(surface), _normalize(reading))
                    )
                token_offset += len(surface)
        offset += len(token.orig)
    return spans


def _prediction(engine: ReadingEngine, text: str) -> tuple[str, int, int]:
    tokens = tuple(engine.tokens(text))
    if "".join(token.orig for token in tokens) != text:
        raise ValueError("reading engine did not preserve source text")
    reading = "".join(token.hira or token.orig for token in tokens)
    kanji_tokens = [token for token in tokens if any(is_kanji(char) for char in token.orig)]
    covered = sum(bool(token.hira) for token in kanji_tokens)
    return _normalize(reading), covered, len(kanji_tokens)


def _span_metrics(
    expected: set[tuple[int, int, str]], predicted: set[tuple[int, int, str]]
) -> dict[str, float | int]:
    true_positive = len(expected & predicted)
    precision = true_positive / len(predicted) if predicted else float(not expected)
    recall = true_positive / len(expected) if expected else float(not predicted)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "gold": len(expected),
        "predicted": len(predicted),
        "true_positive": true_positive,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _validate_review_provenance(cases: list[dict]) -> None:
    """Require traceable human review before a case can claim reviewed status."""

    for case in cases:
        if case.get("review_status") != "reviewed":
            continue
        case_id = case.get("id", "?")
        reviewer = case.get("reviewer")
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError(f"{case_id}: reviewed case needs a reviewer")
        basis = case.get("review_basis")
        if not isinstance(basis, str) or not basis.strip():
            raise ValueError(f"{case_id}: reviewed case needs a review_basis")
        reviewed_at = case.get("reviewed_at")
        if not isinstance(reviewed_at, str):
            raise ValueError(f"{case_id}: reviewed case needs reviewed_at (YYYY-MM-DD)")
        try:
            parsed_date = date.fromisoformat(reviewed_at)
        except ValueError as exc:
            raise ValueError(
                f"{case_id}: reviewed_at must use YYYY-MM-DD"
            ) from exc
        if parsed_date.isoformat() != reviewed_at:
            raise ValueError(f"{case_id}: reviewed_at must use YYYY-MM-DD")


def evaluate(
    cases: Iterable[dict], engine: ReadingEngine, *, include_unreviewed: bool = False
) -> dict:
    case_list = list(cases)
    _validate_review_provenance(case_list)
    selected = [
        case
        for case in case_list
        if include_unreviewed or case.get("review_status") == "reviewed"
    ]
    if not selected:
        raise ValueError(
            "no reviewed cases found; add a provenance-checked reference set or "
            "use --include-unreviewed for exploratory checks"
        )

    domain_rows: dict[str, list[dict]] = defaultdict(list)
    expected_spans: set[tuple[int, int, str]] = set()
    predicted_spans: set[tuple[int, int, str]] = set()
    has_span_reference = False
    total_edits = 0
    total_reference_chars = 0
    exact = 0
    covered = 0
    kanji_tokens = 0
    for case in selected:
        case_id = case.get("id")
        text = case.get("text")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("each case needs a non-empty string id")
        if not isinstance(text, str) or not text:
            raise ValueError(f"{case_id}: text must be a non-empty string")
        references = _reference_readings(case)
        predicted, case_covered, case_kanji_tokens = _prediction(engine, text)
        distances = [_edit_distance(reference, predicted) for reference in references]
        best_index = min(range(len(distances)), key=distances.__getitem__)
        distance = distances[best_index]
        reference = references[best_index]
        total_edits += distance
        total_reference_chars += len(reference)
        exact += distance == 0
        covered += case_covered
        kanji_tokens += case_kanji_tokens
        row = {
            "id": case_id,
            "domain": str(case.get("domain") or "unspecified"),
            "cer": distance / len(reference) if reference else float(distance > 0),
            "exact": distance == 0,
            "reference_count": len(references),
            "kanji_token_coverage": (
                case_covered / case_kanji_tokens if case_kanji_tokens else 1.0
            ),
        }
        domain_rows[row["domain"]].append(row)

        expected = case.get("reference_ruby_spans")
        if expected is not None:
            if not isinstance(expected, list):
                raise ValueError(f"{case_id}: reference_ruby_spans must be a list")
            has_span_reference = True
            for span in expected:
                if (
                    not isinstance(span, dict)
                    or not isinstance(span.get("start"), int)
                    or not isinstance(span.get("end"), int)
                    or not isinstance(span.get("reading"), str)
                    or span["start"] < 0
                    or span["end"] <= span["start"]
                    or span["end"] > len(text)
                ):
                    raise ValueError(f"{case_id}: invalid Ruby span")
                expected_spans.add(
                    (span["start"], span["end"], _normalize(span["reading"]))
                )
            predicted_spans.update(_ruby_spans(engine, text))

    report: dict[str, object] = {
        "engine": runtime_metadata(engine),
        "review_scope": "all cases (exploratory)" if include_unreviewed else "reviewed only",
        "cases": len(selected),
        "cer": total_edits / total_reference_chars if total_reference_chars else 0.0,
        "exact_match_rate": exact / len(selected),
        "kanji_token_coverage": covered / kanji_tokens if kanji_tokens else 1.0,
        "ruby_spans": (
            _span_metrics(expected_spans, predicted_spans)
            if has_span_reference
            else None
        ),
        "by_domain": {},
    }
    report["by_domain"] = {
        domain: {
            "cases": len(rows),
            "cer": sum(row["cer"] for row in rows) / len(rows),
            "exact_match_rate": sum(row["exact"] for row in rows) / len(rows),
            "kanji_token_coverage": sum(row["kanji_token_coverage"] for row in rows)
            / len(rows),
        }
        for domain, rows in sorted(domain_rows.items())
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="provenance-tracked JSON reference set")
    parser.add_argument("--engine", default="sudachi")
    parser.add_argument(
        "--include-unreviewed",
        action="store_true",
        help="include draft cases and label the report exploratory",
    )
    parser.add_argument("--json", action="store_true", help="print the full JSON report")
    args = parser.parse_args(argv)
    try:
        dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
        if dataset.get("schema_version") != 1 or not isinstance(dataset.get("cases"), list):
            raise ValueError("dataset must have schema_version 1 and a cases array")
        report = evaluate(
            dataset["cases"], create_engine(args.engine), include_unreviewed=args.include_unreviewed
        )
        report["dataset"] = dataset.get("dataset_id", args.dataset.stem)
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"dataset={report['dataset']} cases={report['cases']} scope={report['review_scope']}")
        print(
            f"engine={report['engine']['engine']} CER={report['cer']:.4f} "
            f"exact={report['exact_match_rate']:.3f} "
            f"kanji_coverage={report['kanji_token_coverage']:.3f}"
        )
        if report["ruby_spans"] is not None:
            spans = report["ruby_spans"]
            print(
                f"ruby_spans P={spans['precision']:.3f} "
                f"R={spans['recall']:.3f} F1={spans['f1']:.3f}"
            )
        for domain, metrics in report["by_domain"].items():
            print(
                f"{domain}: cases={metrics['cases']} CER={metrics['cer']:.4f} "
                f"exact={metrics['exact_match_rate']:.3f} "
                f"coverage={metrics['kanji_token_coverage']:.3f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
