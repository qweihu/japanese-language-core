"""Pitch accent helpers: position -> pattern and classification."""

from __future__ import annotations


def pattern(mora_count: int, position: int | None) -> tuple[str, ...]:
    """Return per-mora H/L levels for an accent position.

    ``position == 0`` is heiban (flat); ``position == mora_count`` is odaka
    (accent on the final mora, drop applies to a following particle).
    """

    if mora_count <= 0:
        return ()
    if position is None or position <= 0 or position >= mora_count:
        return ("H",) * mora_count
    return ("H",) * position + ("L",) * (mora_count - position)


def classify(mora_count: int, position: int | None) -> str:
    if position is None:
        return "unknown"
    if position <= 0:
        return "平板 heiban"
    if position == 1:
        return "頭高 atamadaka"
    if position >= mora_count:
        return "尾高 odaka"
    return "中高 nakadaka"
