"""Paired Markdown layout contract (reference implementation).

Utayomi owns its final lyric layout; this builder is the reusable contract
for "one source line, one translation line, one blank line" output that
Bunomi and simple exports share.
"""

from __future__ import annotations

from ..translation.contract import TranslationUnit


def build_paired_markdown(
    units: list[TranslationUnit],
    *,
    ruby_lines: dict[int, str] | None = None,
) -> str:
    """Render units as ``ruby line`` + ``translation line`` + blank line."""

    blocks: list[str] = []
    for index, unit in enumerate(units):
        if not unit.source.strip() and not unit.translation.strip():
            continue
        source = (ruby_lines or {}).get(index, unit.source)
        blocks.append(source)
        blocks.append(unit.translation)
    return "\n\n".join(blocks) + "\n"
