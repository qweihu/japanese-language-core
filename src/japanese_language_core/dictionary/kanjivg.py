"""Reader for KanjiVG stroke-order data (CC BY-SA).

KanjiVG files are SVG documents with one ``<kanji>`` root per character.
The reader extracts stroke path data, the radical, and the stroke count.
The dataset itself is not bundled; point this reader at a downloaded
KanjiVG directory (``kanji/*.svg``) or a single SVG file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class KanjiVGEntry:
    character: str
    strokes: tuple[str, ...]
    radical: str | None
    total_strokes: int


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_svg(data: str, character: str) -> KanjiVGEntry | None:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return None
    strokes: list[str] = []
    radical: str | None = None
    for element in root.iter():
        name = _local_name(element.tag)
        if name == "path" and element.attrib.get("d"):
            strokes.append(element.attrib["d"])
        elif name == "radical" and radical is None:
            radical = (element.text or "").strip() or element.attrib.get("element")
    if not strokes:
        return None
    return KanjiVGEntry(
        character=character,
        strokes=tuple(strokes),
        radical=radical,
        total_strokes=len(strokes),
    )


class KanjiVGReader:
    def __init__(self, source: str | Path) -> None:
        self.source = Path(source)

    def _path_for(self, character: str) -> Path | None:
        if self.source.is_file():
            return self.source
        codepoint = f"{ord(character):x}"
        candidates = [
            self.source / "kanji" / f"{codepoint}.svg",
            self.source / f"{codepoint}.svg",
            self.source / "kanji" / f"{codepoint.zfill(5)}.svg",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None

    def lookup(self, character: str) -> KanjiVGEntry | None:
        path = self._path_for(character)
        if path is None:
            return None
        return parse_svg(path.read_text(encoding="utf-8"), character)
