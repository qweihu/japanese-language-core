"""Simple Japanese sentence splitting (keep terminators attached)."""

from __future__ import annotations

_TERMINATORS = set("。！？!?…")


def split_sentences(text: str) -> list[str]:
    """Split ``text`` on sentence terminators, keeping them attached."""

    sentences: list[str] = []
    buffer: list[str] = []
    for char in text:
        buffer.append(char)
        if char in _TERMINATORS:
            sentences.append("".join(buffer))
            buffer = []
    if buffer:
        sentences.append("".join(buffer))
    return sentences
