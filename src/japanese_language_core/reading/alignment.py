"""Distribute a kana reading across kanji (furigana alignment)."""

from __future__ import annotations

from .kana import is_kana, to_hiragana


def align_reading(term: str, reading: str) -> list[tuple[str, str]]:
    """Align ``reading`` with ``term`` and return ``(surface, reading)`` pairs.

    Kana in the term are matched verbatim; each run of kanji greedily consumes
    kana until the next kana of the term (or the end of the reading). This is
    the same distribution problem Yomitan handles with dictionary hints, so
    ambiguous compounds (e.g. 好き嫌い) may need dictionary-level alignment;
    this function is the deterministic fallback.
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
            if next_kana is not None:
                boundary = reading_hira.find(next_kana, reading_index)
                if boundary == reading_index:
                    # A word's reading may begin with the same kana as its
                    # okurigana boundary, e.g. 歌う -> うたう. Prefer the
                    # later boundary; if there is none, keep the whole word
                    # together instead of assigning an empty kanji reading.
                    later_boundary = reading_hira.find(next_kana, boundary + 1)
                    if later_boundary < 0:
                        return [(term, reading_hira)]
                    boundary = later_boundary
                if boundary >= 0:
                    reading_index = boundary
                    break
            reading_index += 1
        pairs.append(("".join(surface), reading_hira[start:reading_index]))
    return pairs


def align_with_furigana(
    term: str, reading: str, furigana: dict[str, str] | None
) -> list[tuple[str, str]]:
    """Dictionary-first alignment when per-kanji readings are available.

    ``furigana`` maps each kanji to its reading in this term (the extension
    field some dictionaries provide; most Yomitan v3 term banks do not).
    Falls back to ``align_reading`` when the map cannot cover the reading.
    """

    if not furigana:
        return align_reading(term, reading)
    pairs: list[tuple[str, str]] = []
    index = 0
    for char in term:
        if is_kana(char):
            if index < len(reading) and reading[index] == char:
                pairs.append((char, char))
                index += 1
            else:
                return align_reading(term, reading)
            continue
        expected = furigana.get(char, "")
        if expected and reading.startswith(expected, index):
            pairs.append((char, expected))
            index += len(expected)
        else:
            return align_reading(term, reading)
    if index != len(reading):
        return align_reading(term, reading)
    return pairs
