"""Common Japanese grammar-pattern detection (deterministic, surface-level)."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class GrammarMatch:
    """A grammar pattern occurrence with its span."""

    name: str
    matched: str
    start: int
    end: int


# Suffix patterns are matched after kana/kanji or at the start of text. The
# alternation is sorted longest-first so てしまう wins over て.
_PATTERNS: list[tuple[str, str]] = [
    ("te-iru", r"てしまう"),
    ("te-oku", r"ておく"),
    ("te-iru", r"ている"),
    ("te-iru", r"てる"),
    ("te-mo-ii", r"てもいい"),
    ("te-wa-ikenai", r"てはいけない"),
    ("te-hoshii", r"てほしい"),
    ("obligation", r"なければならない"),
    ("obligation", r"ないといけない"),
    ("potential", r"ことができる"),
    ("maybe", r"かもしれない"),
    ("suggestion", r"たほうがいい"),
    ("expectation", r"はずだ"),
    ("should", r"べきだ"),
    ("intention", r"つもりだ"),
    ("seeming", r"ようだ"),
    ("seeming", r"みたいだ"),
    ("hearsay", r"らしい"),
    ("apparent", r"そうだ"),
    ("excessive", r"すぎる"),
    ("easy-to", r"やすい"),
    ("hard-to", r"にくい"),
    ("while", r"ながら"),
    ("conditional", r"たら"),
    ("conditional", r"れば"),
    ("decision", r"ことにする"),
    ("become", r"ことになる"),
    ("purpose", r"ために"),
    ("purpose", r"ように"),
    ("desiderative", r"たい"),
]

_COMPILED = [
    (name, re.compile(rf"(?:^|(?<=[ぁ-ゖァ-ヺ\u4e00-\u9fff])){pattern}"))
    for name, pattern in _PATTERNS
]


def find_grammar(text: str) -> list[GrammarMatch]:
    matches: list[GrammarMatch] = []
    for name, regex in _COMPILED:
        for match in regex.finditer(text):
            matches.append(
                GrammarMatch(name, match.group(0), match.start(), match.end())
            )
    matches.sort(key=lambda match: (match.start, match.end))
    return matches
