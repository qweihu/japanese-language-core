"""Mora (拍) counting for Japanese text."""

from __future__ import annotations

_SMALL_KANA = set("ゃゅょぁぃぅぇぉゎ")


def mora_segments(text: str) -> list[str]:
    """Return per-mora characters. Small kana and whitespace are skipped;
    っ, ん, and ー each count as one mora."""

    return [char for char in text if char not in _SMALL_KANA and not char.isspace()]


def count_mora(text: str) -> int:
    return len(mora_segments(text))
