"""Compatibility shim: re-export the reading capability of
``japanese_language_core`` under the former package name.

New code should import from ``japanese_language_core.reading``. This shim is
kept for the transition period and removed once consumers migrate.
"""

from japanese_language_core.reading import (
    Deinflection,
    EngineUnavailableError,
    PykakasiEngine,
    ReadingEngine,
    ReadingEngineError,
    ReadingToken,
    SudachiEngine,
    align_reading,
    create_engine,
    deinflect,
    to_hiragana,
)

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
    "to_hiragana",
]
