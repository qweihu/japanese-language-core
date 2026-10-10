"""Reading capabilities: tokenization, contextual readings, kana/romaji
conversion, furigana alignment, and best-effort deinflection."""

from .engine import (
    EngineUnavailableError,
    PykakasiEngine,
    ReadingEngine,
    ReadingEngineError,
    ReadingToken,
    SudachiEngine,
    create_engine,
    runtime_metadata,
)
from .kana import (
    is_hiragana,
    is_kanji,
    is_katakana,
    is_kana,
    normalize_width,
    to_hiragana,
    to_katakana,
    to_romaji,
)
from .alignment import align_reading, align_with_furigana
from .conjugator import conjugate
from .deinflect import Deinflection, deinflect
from .mora import count_mora, mora_segments
from .splitter import split_sentences

__all__ = [
    "Deinflection",
    "EngineUnavailableError",
    "PykakasiEngine",
    "ReadingEngine",
    "ReadingEngineError",
    "ReadingToken",
    "SudachiEngine",
    "align_reading",
    "align_with_furigana",
    "conjugate",
    "count_mora",
    "create_engine",
    "runtime_metadata",
    "deinflect",
    "is_hiragana",
    "is_kanji",
    "is_kana",
    "is_katakana",
    "mora_segments",
    "normalize_width",
    "split_sentences",
    "to_hiragana",
    "to_katakana",
    "to_romaji",
]
