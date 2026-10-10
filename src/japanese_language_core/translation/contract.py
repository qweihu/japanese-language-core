"""Data model and language registry for line-preserving translations."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Mapping


class TranslateError(RuntimeError):
    """Raised when a translation provider cannot produce a result."""


@dataclass
class TranslationUnit:
    """One source line and its translation."""

    source: str
    translation: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class TranslationResult:
    """A validated line-preserving translation."""

    source_lang: str
    target_lang: str
    units: list[TranslationUnit]
    provider: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class LanguageInfo:
    """Per-language translation conventions (machine-readable)."""

    code: str
    name: str
    default: bool = False
    kana_warning: bool = True
    conventions: dict[str, str] = field(default_factory=dict)
    examples: tuple[tuple[str, str], ...] = ()


class LanguageRegistry:
    """Registry of supported target languages.

    The canonical machine-readable source is ``translation/data/languages.json``
    in this package; the human-facing Markdown conventions for agents live in
    the ``japanese-translation`` skill's ``references/`` folder and mirror the
    same codes.
    """

    def __init__(self, data: Mapping[str, Mapping[str, object]]) -> None:
        self._languages: dict[str, LanguageInfo] = {}
        for code, raw in data.items():
            info = LanguageInfo(
                code=code,
                name=str(raw.get("name", code)),
                default=bool(raw.get("default", False)),
                kana_warning=bool(raw.get("kana_warning", True)),
            conventions={
                str(key): str(value)
                for key, value in raw.get("conventions", {}).items()
            },
            examples=tuple(
                (str(item[0]), str(item[1]))
                for item in raw.get("examples", [])
                if isinstance(item, (list, tuple)) and len(item) >= 2
            ),
        )
            self._languages[code] = info

    @classmethod
    def from_package(cls) -> "LanguageRegistry":
        path = Path(__file__).parent / "data" / "languages.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data["registry"])

    @classmethod
    def from_file(cls, path: str | Path) -> "LanguageRegistry":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data.get("registry", data))

    def get(self, code: str) -> LanguageInfo:
        try:
            return self._languages[code]
        except KeyError as exc:
            raise TranslateError(
                f"目标语言 {code!r} 未注册；可用语言：{', '.join(self.codes())}"
            ) from exc

    def codes(self) -> list[str]:
        return sorted(self._languages)

    def default(self) -> LanguageInfo:
        for info in self._languages.values():
            if info.default:
                return info
        raise TranslateError(
            "核心库不设置默认目标语言；请由调用方根据用户语境明确选择语言"
        )
