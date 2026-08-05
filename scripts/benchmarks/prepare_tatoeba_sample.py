#!/usr/bin/env python3
"""Rebuild ``benchmarks/tatoeba_sample.json`` from Tatoeba exports.

Source: https://tatoeba.org/en/downloads (CC BY 2.0). Fetches the Japanese and
Mandarin sentence tables plus their link file, and keeps the first N
non-empty pairs. Run from the repository root with ``python3``.
"""

from __future__ import annotations

import argparse
import bz2
import io
import json
from pathlib import Path
import urllib.request


BASE = "https://downloads.tatoeba.org/exports/per_language"
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "benchmarks" / "tatoeba_sample.json"


def fetch(path: str) -> io.BytesIO:
    with urllib.request.urlopen(f"{BASE}/{path}", timeout=120) as response:
        return io.BytesIO(response.read())


def load_sentences(handle: io.BytesIO) -> dict[str, str]:
    rows: dict[str, str] = {}
    with bz2.open(handle, "rt", encoding="utf-8") as stream:
        for line in stream:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3:
                rows[parts[0]] = parts[2]
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args(argv)

    japanese = load_sentences(fetch("jpn/jpn_sentences.tsv.bz2"))
    mandarin = load_sentences(fetch("cmn/cmn_sentences.tsv.bz2"))
    links = fetch("jpn/jpn-cmn_links.tsv.bz2")

    pairs: list[dict[str, str]] = []
    with bz2.open(links, "rt", encoding="utf-8") as stream:
        for line in stream:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            ja = japanese.get(parts[0], "").strip()
            zh = mandarin.get(parts[1], "").strip()
            if not ja or not zh:
                continue
            pairs.append({"id": f"{parts[0]}-{parts[1]}", "ja": ja, "zh": zh})
            if len(pairs) >= args.count:
                break

    sample = {
        "source": "Tatoeba (https://tatoeba.org), Japanese-Chinese sentence pairs",
        "license": "CC BY 2.0 (https://creativecommons.org/licenses/by/2.0/)",
        "note": "First non-empty pairs from the jpn-cmn export; structural benchmark only.",
        "pairs": pairs,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(sample, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(pairs)} pairs to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
