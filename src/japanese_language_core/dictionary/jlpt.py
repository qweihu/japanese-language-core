"""JLPT-style difficulty analysis over dictionary metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from .model import DictionaryLookup
from ..reading.kana import is_kana


JLPT_LEVELS = ("n5", "n4", "n3", "n2", "n1")
_LEVEL_SCORE = {"n5": 5.0, "n4": 4.0, "n3": 3.0, "n2": 2.0, "n1": 1.0}
_LEVEL_RE = re.compile(r"(?<![a-z])n[1-5](?![a-z])")


def level_from_tags(
    tags: list[str], tag_defs: dict[str, object] | None = None
) -> str | None:
    """Infer a JLPT level from dictionary tags (e.g. ``jlptN3``, ``n3``)."""

    lowered = [tag.lower() for tag in tags]
    for tag in lowered:
        match = _LEVEL_RE.search(tag)
        if match:
            return match.group(0)
        if "jlpt" in tag:
            for level in JLPT_LEVELS:
                if level in tag:
                    return level
    return None


@dataclass
class DifficultyProfile:
    """Difficulty summary for a text."""

    levels: dict[str, int] = field(default_factory=dict)
    terms: list[tuple[str, str]] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    score: float = 0.0

    def level_counts(self) -> dict[str, int]:
        return dict(self.levels)


def _greedy_terms(text: str, dictionary: DictionaryLookup) -> list[str]:
    """Segment without an engine: longest-match against dictionary terms."""

    expressions = sorted(dictionary.all_expressions(), key=len, reverse=True)
    terms: list[str] = []
    index = 0
    while index < len(text):
        for expression in expressions:
            if text.startswith(expression, index):
                terms.append(expression)
                index += len(expression)
                break
        else:
            char = text[index]
            terms.append(char)
            index += 1
    return terms


def analyze_difficulty(
    text: str,
    dictionary: DictionaryLookup,
    *,
    engine: object | None = None,
) -> DifficultyProfile:
    """Analyze a text's JLPT difficulty using dictionary metadata.

    ``engine`` is any reading engine with ``tokens(text)`` (the reading
    capability's engines qualify). Without one, a deterministic longest-match
    segmentation over dictionary expressions is used.
    """

    if engine is not None:
        surfaces = [
            token.orig
            for token in engine.tokens(text)
            if token.orig.strip() and not token.orig.isspace()
        ]
    else:
        surfaces = [
            term for term in _greedy_terms(text, dictionary) if term.strip()
        ]

    profile = DifficultyProfile()
    tag_defs = dictionary.tags()
    for surface in surfaces:
        entries = dictionary.lookup_terms(surface)
        level = None
        for entry in entries:
            level = level_from_tags(entry.tags, tag_defs)
            if level:
                break
        if level is None:
            level = "unknown"
        profile.terms.append((surface, level))
        profile.levels[level] = profile.levels.get(level, 0) + 1
        if level == "unknown":
            profile.unknown.append(surface)

    known = sum(profile.levels.get(level, 0) for level in JLPT_LEVELS)
    weighted = sum(
        _LEVEL_SCORE[level] * count
        for level, count in profile.levels.items()
        if level in _LEVEL_SCORE
    )
    total = max(known, 1)
    profile.score = round(weighted / total, 2)
    return profile
