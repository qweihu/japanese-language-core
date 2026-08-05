#!/usr/bin/env python3
"""Run the committed benchmark suite.

Reading: for every Japanese sentence in ``benchmarks/tatoeba_sample.json``,
assert source preservation and report kanji-reading coverage.
Translation: validate the paired Chinese reference with
``validate_translation(..., paired=True)`` and require zero errors.

Exit code 1 on failure or below-threshold metrics. Intended for CI.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from japanese_language_core.reading import create_engine, is_kanji
from japanese_language_core.translation import validate_translation


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "benchmarks" / "tatoeba_sample.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-coverage", type=float, default=0.95)
    parser.add_argument("--engine", default="sudachi")
    args = parser.parse_args(argv)

    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    pairs = data["pairs"]
    engine = create_engine(args.engine)
    failures: list[str] = []

    total_kanji = 0
    covered_kanji = 0
    for index, pair in enumerate(pairs, start=1):
        tokens = tuple(engine.tokens(pair["ja"]))
        if "".join(token.orig for token in tokens) != pair["ja"]:
            failures.append(f"reading source mismatch at pair {index}: {pair['ja']!r}")
            continue
        for token in tokens:
            if any(is_kanji(char) for char in token.orig):
                total_kanji += 1
                if token.hira:
                    covered_kanji += 1

    errors, warnings = validate_translation(
        [pair["ja"] for pair in pairs],
        [pair["zh"] for pair in pairs],
        paired=True,
    )
    for error in errors:
        failures.append("translation: " + error)

    coverage = covered_kanji / total_kanji if total_kanji else 1.0
    print(
        f"pairs={len(pairs)} kanji_coverage={coverage:.3f} "
        f"translation_errors={len(errors)} warnings={len(warnings)}"
    )
    if failures:
        for failure in failures[:10]:
            print("FAIL:", failure)
        return 1
    if coverage < args.min_coverage:
        print(f"FAIL: kanji reading coverage {coverage:.3f} < {args.min_coverage}")
        return 1
    print("benchmarks OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
