"""Proper-noun (JMnedict) view over Yomitan term banks.

JMnedict releases commonly mark rows with name categories (surname, given,
place, organization...) and may leave the reading column empty while storing
kana readings as plain strings in the definitions slot. This module provides
the name-specific view; ``YomitanDictionary.lookup_names`` uses it.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..reading.kana import is_kana


NAME_CATEGORIES = {
    "surname",
    "given",
    "female",
    "male",
    "unisex",
    "place",
    "organization",
    "person",
    "work",
    "product",
    "unclass",
    "company",
    "group",
    "character",
    "station",
    "country",
    "prefecture",
    "city",
    "region",
    "mountain",
    "river",
    "event",
    "ship",
    "star",
    "creature",
    "name",
    "title",
    "brand",
    "school",
}


@dataclass(frozen=True)
class NameEntry:
    """A proper noun with its readings and categories."""

    expression: str
    readings: tuple[str, ...]
    categories: tuple[str, ...]
    definition: str = ""


def name_categories(tags: list[str]) -> tuple[str, ...]:
    return tuple(
        sorted({tag for tag in tags if tag.lower() in NAME_CATEGORIES})
    )


def _is_kana_text(text: str) -> bool:
    return bool(text) and all(
        char.isspace() or is_kana(char) for char in text
    )


def looks_like_name(entry) -> bool:
    """True when the term has name categories or the JMnedict pattern
    (empty reading + kana strings in the definitions slot)."""

    if name_categories(entry.tags):
        return True
    if not entry.reading and entry.definitions:
        return all(_is_kana_text(text) for text in entry.definitions)
    return False


def readings_of(entry) -> tuple[str, ...]:
    candidates: list[str] = []
    if entry.reading:
        candidates.append(entry.reading)
    else:
        candidates.extend(
            text for text in entry.definitions if _is_kana_text(text)
        )
    return tuple(dict.fromkeys(candidates))


def to_name_entry(entry) -> NameEntry:
    definition = next(
        (text for text in entry.definitions if not _is_kana_text(text)),
        "",
    )
    return NameEntry(
        expression=entry.expression,
        readings=readings_of(entry),
        categories=name_categories(entry.tags),
        definition=definition,
    )
