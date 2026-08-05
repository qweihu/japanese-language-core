"""Difficulty scoring over a ``DifficultyProfile`` (approximate)."""

from __future__ import annotations

from .jlpt import DifficultyProfile


_WEIGHTS = {"n5": 5.0, "n4": 4.0, "n3": 3.0, "n2": 2.0, "n1": 1.0}


def readability(profile: DifficultyProfile, *, unknown_penalty: float = 0.3) -> float:
    """Return a 0..1 score (higher = easier), penalizing unknown terms."""

    total = sum(profile.levels.values())
    if total == 0:
        return 1.0
    known = sum(profile.levels.get(level, 0) for level in _WEIGHTS)
    weighted = sum(
        _WEIGHTS.get(level, 0) * count for level, count in profile.levels.items()
    )
    base = weighted / known if known else 0.0
    unknown_ratio = profile.levels.get("unknown", 0) / total
    return round(base * (1 - unknown_penalty * unknown_ratio), 2)


def difficulty_label(score: float) -> str:
    if score >= 3.5:
        return "easy"
    if score >= 2.5:
        return "medium"
    return "hard"


def mean_frequency_rank(surfaces: list[str], dictionary) -> float | None:
    """Mean frequency rank over dictionary entries (lower = more common)."""

    ranks: list[float] = []
    for surface in surfaces:
        for entry in dictionary.lookup_terms(surface):
            if entry.frequency is not None and entry.frequency.value is not None:
                ranks.append(float(entry.frequency.value))
    if not ranks:
        return None
    return round(sum(ranks) / len(ranks), 2)
