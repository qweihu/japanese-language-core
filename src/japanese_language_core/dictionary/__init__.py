"""Dictionary and vocabulary metadata capabilities."""

from .model import (
    DictionaryLookup,
    FrequencyTag,
    KanjiEntry,
    PitchAccent,
    TagEntry,
    TermEntry,
)
from .yomitan import YomitanDictionary
from .jlpt import DifficultyProfile, analyze_difficulty, level_from_tags

__all__ = [
    "DictionaryLookup",
    "DifficultyProfile",
    "FrequencyTag",
    "KanjiEntry",
    "PitchAccent",
    "TagEntry",
    "TermEntry",
    "YomitanDictionary",
    "analyze_difficulty",
    "level_from_tags",
]
