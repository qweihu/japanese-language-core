"""Term-consistency checks for translations (glossary management)."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Iterable

from ..structure import strip_ruby


@dataclass(frozen=True)
class GlossaryEntry:
    """A source term and its preferred translation."""

    source: str
    preferred: str
    allowed_variants: tuple[str, ...] = ()


class TermGlossary:
    """Check that source terms use consistent, preferred translations."""

    def __init__(self, entries: Iterable[GlossaryEntry] | None = None) -> None:
        self.entries: dict[str, GlossaryEntry] = {
            entry.source: entry for entry in (entries or [])
        }

    @classmethod
    def from_file(cls, path: str | Path) -> "TermGlossary":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        items = raw.get("entries", raw)
        return cls(
            GlossaryEntry(
                source=item["source"],
                preferred=item["preferred"],
                allowed_variants=tuple(item.get("allowed_variants", [])),
            )
            for item in items
        )

    def add(self, entry: GlossaryEntry) -> None:
        self.entries[entry.source] = entry

    def check_units(
        self, source_lines: Iterable[str], translation_lines: Iterable[str]
    ) -> list[str]:
        warnings: list[str] = []
        seen: dict[str, str] = {}
        for index, (source_line, translation_line) in enumerate(
            zip(source_lines, translation_lines), start=1
        ):
            plain = strip_ruby(source_line)
            for source_term, entry in self.entries.items():
                if source_term not in plain:
                    continue
                translation = translation_line
                if source_term in translation:
                    warnings.append(
                        f"翻译行 {index}: 术语 {source_term!r} 未翻译，应使用 {entry.preferred!r}"
                    )
                    continue
                allowed = (entry.preferred, *entry.allowed_variants)
                used = next(
                    (variant for variant in allowed if variant in translation), None
                )
                if used is None:
                    warnings.append(
                        f"翻译行 {index}: 术语 {source_term!r} 未使用首选译文 {entry.preferred!r}"
                    )
                    continue
                if source_term in seen and seen[source_term] != used:
                    warnings.append(
                        f"翻译行 {index}: 术语 {source_term!r} 前后译文不一致"
                        f"（{seen[source_term]!r} → {used!r}）"
                    )
                else:
                    seen[source_term] = used
        return warnings
