"""Dictionary data model aligned with the Yomitan dictionary format."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class PitchAccent:
    """A term's pitch accent position/category."""

    position: int | None = None
    category: str | None = None


@dataclass(frozen=True)
class FrequencyTag:
    """A frequency value from a dictionary meta bank."""

    value: float | int | None = None
    source: str = ""


@dataclass
class TermEntry:
    """A dictionary term: expression, readings, definitions, metadata."""

    expression: str
    reading: str = ""
    definitions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    score: int = 0
    sequence: int | None = None
    frequency: FrequencyTag | None = None
    pitch_accents: list[PitchAccent] = field(default_factory=list)


@dataclass
class KanjiEntry:
    """A kanji entry: readings, meanings, stats, and frequency."""

    character: str
    onyomi: list[str] = field(default_factory=list)
    kunyomi: list[str] = field(default_factory=list)
    meanings: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    stats: dict[str, object] = field(default_factory=dict)
    frequency: FrequencyTag | None = None


@dataclass(frozen=True)
class TagEntry:
    """A tag definition (part of speech, frequency, kanken level...)."""

    name: str
    category: str = ""
    order: int = 0
    description: str = ""


class DictionaryLookup(Protocol):
    """Minimal lookup contract applications depend on."""

    def lookup_terms(self, expression: str) -> list[TermEntry]:
        ...

    def lookup_kanji(self, character: str) -> list[KanjiEntry]:
        ...

    def tags(self) -> dict[str, TagEntry]:
        ...
