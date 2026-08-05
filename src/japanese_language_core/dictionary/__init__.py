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
from .pitch import classify, pattern
from .scoring import difficulty_label, mean_frequency_rank, readability
from .kanjivg import KanjiVGEntry, KanjiVGReader, parse_svg
from .jmnedict import NameEntry, name_categories

__all__ = [
    "DictionaryLookup",
    "DifficultyProfile",
    "FrequencyTag",
    "NameEntry",
    "KanjiVGEntry",
    "KanjiVGReader",
    "KanjiEntry",
    "PitchAccent",
    "TagEntry",
    "TermEntry",
    "YomitanDictionary",
    "analyze_difficulty",
    "classify",
    "difficulty_label",
    "level_from_tags",
    "mean_frequency_rank",
    "name_categories",
    "parse_svg",
    "pattern",
    "readability",
]
