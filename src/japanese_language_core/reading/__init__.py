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
from .alignment import align_reading
from .deinflect import Deinflection, deinflect

__all__ = [
    "Deinflection",
    "EngineUnavailableError",
    "PykakasiEngine",
    "ReadingEngine",
    "ReadingEngineError",
    "ReadingToken",
    "SudachiEngine",
    "align_reading",
    "create_engine",
    "deinflect",
    "is_hiragana",
    "is_kanji",
    "is_kana",
    "is_katakana",
    "normalize_width",
    "to_hiragana",
    "to_katakana",
    "to_romaji",
]
