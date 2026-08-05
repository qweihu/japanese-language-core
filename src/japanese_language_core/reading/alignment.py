"""Distribute a kana reading across kanji (furigana alignment)."""

from __future__ import annotations

from .kana import is_kana, to_hiragana


def align_reading(term: str, reading: str) -> list[tuple[str, str]]:
    """Align ``reading`` with ``term`` and return ``(surface, reading)`` pairs.

    Kana in the term are matched verbatim; each run of kanji greedily consumes
    kana until the next kana of the term (or the end of the reading). This is
    the same distribution problem Yomitan handles with dictionary hints, so
    ambiguous compounds (e.g. 好き嫌い) may need dictionary-level alignment;
    this function is the deterministic fallback for ruby rendering.
    """

    term_hira = to_hiragana(term)
    reading_hira = to_hiragana(reading)
    pairs: list[tuple[str, str]] = []
    term_index = 0
    reading_index = 0
    while term_index < len(term_hira):
        char = term_hira[term_index]
        if is_kana(char):
            chunk = char
            if (
                reading_index < len(reading_hira)
                and reading_hira[reading_index] == char
            ):
                reading_index += 1
                pairs.append((term[term_index], char))
            else:
                pairs.append((term[term_index], ""))
            term_index += 1
            continue

        # Kanji run: consume kana until the next kana in the term or EOF.
        surface = [term[term_index]]
        start = reading_index
        term_index += 1
        while term_index < len(term_hira) and not is_kana(term_hira[term_index]):
            surface.append(term[term_index])
            term_index += 1
        next_kana = term_hira[term_index] if term_index < len(term_hira) else None
        while reading_index < len(reading_hira):
            if next_kana is not None and reading_hira[reading_index] == next_kana:
                break
            reading_index += 1
        pairs.append(("".join(surface), reading_hira[start:reading_index]))
    return pairs
