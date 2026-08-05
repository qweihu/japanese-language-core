"""Line-preserving translation contracts, validation, and providers."""

from .contract import (
    LanguageInfo,
    LanguageRegistry,
    TranslateError,
    TranslationResult,
    TranslationUnit,
)
from .validate import validate_translation
from .glossary import GlossaryEntry, TermGlossary
from .provider import AgentTranslator, OpenAICompatibleTranslator, Translator

__all__ = [
    "AgentTranslator",
    "GlossaryEntry",
    "LanguageInfo",
    "LanguageRegistry",
    "OpenAICompatibleTranslator",
    "TermGlossary",
    "TranslateError",
    "TranslationResult",
    "TranslationUnit",
    "Translator",
    "validate_translation",
]
