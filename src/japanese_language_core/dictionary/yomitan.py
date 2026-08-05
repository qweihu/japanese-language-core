"""Reader for Yomitan-format dictionaries (zip bundles).

Yomitan dictionaries are zip files containing ``index.json`` plus numbered
``term_bank_*.json``, ``kanji_bank_*.json``, ``tag_bank_*.json``, and optional
meta banks. Aligning with this open format gives the core access to the
community's existing dictionary ecosystem (JMdict-based, JPDB frequency,
pitch accent, etc.).
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
import json
from pathlib import Path
import re
import zipfile

from .model import FrequencyTag, KanjiEntry, PitchAccent, TagEntry, TermEntry
from .jmnedict import looks_like_name, to_name_entry


@dataclass(frozen=True)
class DictionaryIndex:
    """Metadata from ``index.json``."""

    title: str = ""
    format_version: int = 3
    description: str = ""
    attribution: str = ""
    author: str = ""
    url: str = ""


class YomitanDictionary:
    """A Yomitan dictionary bundle loaded from a zip file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        with zipfile.ZipFile(self.path) as archive:
            self._entries: dict[str, list[list[object]]] = {}
            self._meta: dict[str, list[list[object]]] = {}
            self._index = self._read_index(archive)
            for name in archive.namelist():
                if name.startswith("term_bank_"):
                    self._entries.setdefault("term", []).extend(
                        self._load_json(archive, name)
                    )
                elif name.startswith("kanji_bank_"):
                    self._entries.setdefault("kanji", []).extend(
                        self._load_json(archive, name)
                    )
                elif name.startswith("tag_bank_"):
                    self._entries.setdefault("tag", []).extend(
                        self._load_json(archive, name)
                    )
                elif name.startswith("term_meta_bank_"):
                    self._meta.setdefault("term", []).extend(
                        self._load_json(archive, name)
                    )
                elif name.startswith("kanji_meta_bank_"):
                    self._meta.setdefault("kanji", []).extend(
                        self._load_json(archive, name)
                    )
        self._tag_defs = self._build_tags()
        self._term_meta_index = self._build_term_meta_index()
        self._kanji_freq = self._build_kanji_freq()
        self._term_index = self._build_term_index()
        self._kanji_index = self._build_kanji_index()
        self._sorted_expressions = sorted(self._term_index)

    @staticmethod
    def _read_index(archive: zipfile.ZipFile) -> DictionaryIndex:
        if "index.json" not in archive.namelist():
            return DictionaryIndex()
        raw = json.loads(archive.read("index.json").decode("utf-8"))
        return DictionaryIndex(
            title=str(raw.get("title", "")),
            format_version=int(raw.get("format_version", 3)),
            description=str(raw.get("description", "")),
            attribution=str(raw.get("attribution", "")),
            author=str(raw.get("author", "")),
            url=str(raw.get("url", "")),
        )

    @staticmethod
    def _load_json(archive: zipfile.ZipFile, name: str) -> list[list[object]]:
        return json.loads(archive.read(name).decode("utf-8"))

    @property
    def index(self) -> DictionaryIndex:
        return self._index

    def _build_tags(self) -> dict[str, TagEntry]:
        result: dict[str, TagEntry] = {}
        for row in self._entries.get("tag", []):
            if not row:
                continue
            name = str(row[0])
            result[name] = TagEntry(
                name=name,
                category=str(row[1]) if len(row) > 1 else "",
                order=int(row[2]) if len(row) > 2 and row[2] is not None else 0,
                description=str(row[3]) if len(row) > 3 else "",
            )
        return result

    @staticmethod
    def _glossary_text(glossary: object) -> list[str]:
        if isinstance(glossary, str):
            return [glossary]
        if isinstance(glossary, list):
            texts: list[str] = []
            for item in glossary:
                if isinstance(item, str):
                    texts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    texts.append(str(item["text"]))
            return texts
        return []

    def _term_meta(self, expression: str) -> tuple[FrequencyTag | None, list[PitchAccent]]:
        frequency: FrequencyTag | None = None
        accents: list[PitchAccent] = []
        for mode, data in self._term_meta_index.get(expression, []):
            if mode == "freq":
                if isinstance(data, (int, float)):
                    frequency = FrequencyTag(value=data, source=self.index.title)
                elif isinstance(data, dict):
                    value = data.get("value", data.get("frequency"))
                    frequency = FrequencyTag(
                        value=value if isinstance(value, (int, float)) else None,
                        source=self.index.title,
                    )
            elif mode == "pitch":
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item is None or item == "n/a":
                        continue
                    if isinstance(item, (int, float)):
                        accents.append(PitchAccent(position=int(item)))
                        continue
                    if isinstance(item, dict):
                        position = item.get("position")
                        accents.append(
                            PitchAccent(
                                position=int(position) if position is not None else None,
                                category=str(item.get("category")) if item.get("category") else None,
                            )
                        )
        return frequency, accents

    def _build_term_meta_index(self) -> dict[str, list[tuple[str, object]]]:
        index: dict[str, list[tuple[str, object]]] = {}
        for row in self._meta.get("term", []):
            if len(row) < 3:
                continue
            index.setdefault(str(row[0]), []).append((str(row[1]), row[2]))
        return index

    def _build_kanji_freq(self) -> dict[str, int | float]:
        result: dict[str, int | float] = {}
        for row in self._meta.get("kanji", []):
            if (
                len(row) >= 3
                and str(row[1]) == "freq"
                and isinstance(row[2], (int, float))
            ):
                result[str(row[0])] = row[2]
        return result

    def _build_term_index(self) -> dict[str, list[TermEntry]]:
        index: dict[str, list[TermEntry]] = {}
        for row in self._entries.get("term", []):
            if not row:
                continue
            expression = str(row[0])
            reading = str(row[1]) if len(row) > 1 else ""
            definition_tags = (
                list(row[2]) if len(row) > 2 and isinstance(row[2], list) else []
            )
            rules = list(row[3]) if len(row) > 3 and isinstance(row[3], list) else []
            score = int(row[4]) if len(row) > 4 and row[4] is not None else 0
            definitions = self._glossary_text(row[5]) if len(row) > 5 else []
            sequence = int(row[6]) if len(row) > 6 and row[6] is not None else None
            term_tags = list(row[7]) if len(row) > 7 and isinstance(row[7], list) else []
            furigana = (
                {str(key): str(value) for key, value in row[8].items()}
                if len(row) > 8 and isinstance(row[8], dict)
                else None
            )
            frequency, accents = self._term_meta(expression)
            entry = TermEntry(
                expression=expression,
                reading=reading,
                definitions=definitions,
                tags=[*definition_tags, *term_tags],
                rules=rules,
                score=score,
                sequence=sequence,
                frequency=frequency,
                pitch_accents=accents,
                furigana=furigana,
            )
            index.setdefault(expression, []).append(entry)
        return index

    def _build_kanji_index(self) -> dict[str, list[KanjiEntry]]:
        index: dict[str, list[KanjiEntry]] = {}
        for row in self._entries.get("kanji", []):
            if not row:
                continue
            character = str(row[0])
            onyomi = list(row[1]) if len(row) > 1 and isinstance(row[1], list) else []
            kunyomi = list(row[2]) if len(row) > 2 and isinstance(row[2], list) else []
            tags = list(row[3]) if len(row) > 3 and isinstance(row[3], list) else []
            meanings = list(row[4]) if len(row) > 4 and isinstance(row[4], list) else []
            stats = dict(row[5]) if len(row) > 5 and isinstance(row[5], dict) else {}
            frequency: FrequencyTag | None = None
            if character in self._kanji_freq:
                frequency = FrequencyTag(
                    value=self._kanji_freq[character], source=self.index.title
                )
            index.setdefault(character, []).append(
                KanjiEntry(
                    character=character,
                    onyomi=onyomi,
                    kunyomi=kunyomi,
                    meanings=meanings,
                    tags=tags,
                    stats=stats,
                    frequency=frequency,
                )
            )
        return index

    def lookup_terms(self, expression: str) -> list[TermEntry]:
        return list(self._term_index.get(expression, []))

    def search(
        self, expression: str, mode: str = "prefix"
    ) -> list[TermEntry]:
        """Search expressions by ``prefix``, ``substring``, or ``wildcard``."""

        if mode == "prefix":
            results: list[TermEntry] = []
            start = bisect_left(self._sorted_expressions, expression)
            for key in self._sorted_expressions[start:]:
                if not key.startswith(expression):
                    break
                results.extend(self._term_index[key])
            return results
        if mode == "substring":
            return [
                entry
                for key in self._sorted_expressions
                if expression in key
                for entry in self._term_index[key]
            ]
        if mode == "wildcard":
            regex = re.compile(
                "^"
                + re.escape(expression).replace(r"\*", ".*").replace(r"\?", ".")
                + "$"
            )
            return [
                entry
                for key in self._sorted_expressions
                if regex.match(key)
                for entry in self._term_index[key]
            ]
        raise ValueError("mode must be 'prefix', 'substring', or 'wildcard'")

    def lookup_kanji(self, character: str) -> list[KanjiEntry]:
        return list(self._kanji_index.get(character, []))

    def lookup_names(self, expression: str):
        """Return proper-noun entries (JMnedict view) for ``expression``."""

        return [
            to_name_entry(entry)
            for entry in self._term_index.get(expression, [])
            if looks_like_name(entry)
        ]

    def tags(self) -> dict[str, TagEntry]:
        return dict(self._tag_defs)

    def all_expressions(self) -> list[str]:
        return list(self._term_index)

    def validate(self) -> list[str]:
        """Return structural validation errors for the bundle."""

        errors: list[str] = []
        if not self._index.title:
            errors.append("index.json 缺少 title")
        if not self._entries.get("term") and not self._entries.get("kanji"):
            errors.append("缺少 term_bank_*.json 或 kanji_bank_*.json")
        for idx, row in enumerate(self._entries.get("term", []), start=1):
            if len(row) < 2 or not isinstance(row[0], str):
                errors.append(f"term_bank 第 {idx} 行字段不足（需要 expression/reading）")
        for idx, row in enumerate(self._entries.get("kanji", []), start=1):
            if len(row) < 6:
                errors.append(f"kanji_bank 第 {idx} 行字段不足（需要 6 列）")
        for idx, row in enumerate(self._entries.get("tag", []), start=1):
            if not row or not isinstance(row[0], str):
                errors.append(f"tag_bank 第 {idx} 行无效")
        return errors
