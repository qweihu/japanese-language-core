"""Context-aware Japanese reading engines shared by Bunomi and Utayomi."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Protocol


class ReadingEngineError(RuntimeError):
    """Base error for the shared engine boundary."""


class EngineUnavailableError(ReadingEngineError):
    """Raised when a configured engine or its dictionary is unavailable."""


@dataclass(frozen=True)
class ReadingToken:
    """A source-preserving fragment and its normalized readings."""

    orig: str
    hira: str = ""
    hepburn: str = ""


class ReadingEngine(Protocol):
    """Minimal contract that an application must consume."""

    def tokens(self, text: str) -> Iterable[ReadingToken]:
        """Yield tokens whose ``orig`` fields concatenate to ``text``."""


def to_hiragana(text: str) -> str:
    """Normalize katakana readings so renderer alignment is stable."""

    normalized: list[str] = []
    for char in text:
        codepoint = ord(char)
        if 0x30A1 <= codepoint <= 0x30F6:
            normalized.append(chr(codepoint - 0x60))
        else:
            normalized.append(char)
    return "".join(normalized)


class PykakasiEngine:
    """Fugashi/UniDic fallback tokenization plus PyKakasi readings."""

    name = "pykakasi"

    def __init__(self) -> None:
        try:
            import fugashi  # type: ignore[import-not-found]
            import pykakasi  # type: ignore[import-not-found]
        except ImportError as exc:
            raise EngineUnavailableError(
                "缺少日语注音依赖，请安装 japanese-reading-core"
            ) from exc

        try:
            self._tagger = fugashi.Tagger()
        except Exception as exc:  # pragma: no cover - depends on local dictionary
            raise EngineUnavailableError(
                "无法初始化 UniDic-lite，请重新安装 japanese-reading-core"
            ) from exc
        if hasattr(pykakasi, "kakasi"):
            self._kakasi = pykakasi.kakasi()
        else:  # compatibility with older PyKakasi releases
            self._kakasi = pykakasi.Kakasi()

    def tokens(self, text: str) -> Iterable[ReadingToken]:
        for line in text.splitlines(keepends=True):
            newline = ""
            body = line
            if body.endswith("\r\n"):
                body, newline = body[:-2], "\r\n"
            elif body.endswith("\n"):
                body, newline = body[:-1], "\n"
            if body:
                # MeCab generally omits whitespace from its token stream, so
                # split it out explicitly to guarantee source preservation.
                for chunk in re.split(r"(\s+)", body):
                    if not chunk:
                        continue
                    if chunk.isspace():
                        yield ReadingToken(chunk)
                        continue
                    converted = list(self._kakasi.convert(chunk))
                    # PyKakasi sees the surrounding phrase here, which gives
                    # better compounds such as 日本語 -> にほんご. Fall back
                    # to Fugashi boundaries only if conversion loses text.
                    if "".join(str(item.get("orig", "")) for item in converted) != chunk:
                        converted = []
                        for word in self._tagger(chunk):
                            converted.extend(self._kakasi.convert(word.surface))
                    for item in converted:
                        yield ReadingToken(
                            str(item.get("orig", "")),
                            str(item.get("hira", "")),
                            str(item.get("hepburn", "")),
                        )
            if newline:
                yield ReadingToken(newline)


class SudachiEngine:
    """Context-aware readings from SudachiPy and sudachidict-core."""

    name = "sudachi"

    def __init__(self) -> None:
        try:
            from sudachipy import dictionary, tokenizer  # type: ignore[import-not-found]
            import pykakasi  # type: ignore[import-not-found]
        except ImportError as exc:
            raise EngineUnavailableError(
                "缺少 Sudachi 上下文引擎，请安装 japanese-reading-core"
            ) from exc
        try:
            self._tokenizer = dictionary.Dictionary().create()
            self._split_mode = tokenizer.Tokenizer.SplitMode.C
            self._kakasi = (
                pykakasi.kakasi()
                if hasattr(pykakasi, "kakasi")
                else pykakasi.Kakasi()
            )
        except Exception as exc:  # pragma: no cover - depends on local dictionary
            raise EngineUnavailableError(
                "无法初始化 Sudachi 词典，请重新安装 japanese-reading-core"
            ) from exc

    def _romaji(self, reading: str) -> str:
        return "".join(
            str(item.get("hepburn", ""))
            for item in self._kakasi.convert(to_hiragana(reading))
        )

    def tokens(self, text: str) -> Iterable[ReadingToken]:
        for line in text.splitlines(keepends=True):
            newline = ""
            body = line
            if body.endswith("\r\n"):
                body, newline = body[:-2], "\r\n"
            elif body.endswith("\n"):
                body, newline = body[:-1], "\n"
            if body:
                for chunk in re.split(r"(\s+)", body):
                    if not chunk:
                        continue
                    if chunk.isspace():
                        yield ReadingToken(chunk)
                        continue
                    matches = list(self._tokenizer.tokenize(chunk, self._split_mode))
                    if "".join(match.surface() for match in matches) != chunk:
                        raise ReadingEngineError("Sudachi 分词没有保留原文")
                    for match in matches:
                        surface = match.surface()
                        reading = to_hiragana(match.reading_form() or surface)
                        yield ReadingToken(surface, reading, self._romaji(reading))
            if newline:
                yield ReadingToken(newline)


def create_engine(name: str = "auto") -> ReadingEngine:
    """Create the requested engine, preferring Sudachi for automatic mode."""

    if name not in {"auto", "sudachi", "pykakasi"}:
        raise ValueError("engine must be 'auto', 'sudachi', or 'pykakasi'")
    if name in {"auto", "sudachi"}:
        try:
            return SudachiEngine()
        except EngineUnavailableError:
            if name == "sudachi":
                raise
    return PykakasiEngine()
