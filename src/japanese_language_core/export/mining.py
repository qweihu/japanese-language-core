"""Anki mining pipeline contract: sentence -> note -> AnkiConnect payload.

The core defines the data shape and serializers only; fetching audio, talking
to AnkiConnect, and the card-template UI remain application concerns.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .anki import AnkiNote, anki_connect_payload, to_tsv


@dataclass
class MiningUnit:
    """One mined sentence and the note fields to build from it."""

    sentence: str
    translation: str = ""
    expression: str = ""
    reading: str = ""
    glossary: str = ""
    pitch: str = ""
    frequency: str = ""
    audio: str = ""
    tags: list[str] = field(default_factory=list)

    def to_note(self) -> AnkiNote:
        return AnkiNote(
            expression=self.expression,
            reading=self.reading,
            glossary=self.glossary,
            sentence=self.sentence,
            translation=self.translation,
            audio=self.audio,
            pitch=self.pitch,
            frequency=self.frequency,
            tags=list(self.tags),
        )


def detect_expression(sentence: str, dictionary) -> str:
    """Return the longest dictionary expression contained in ``sentence``."""

    for expression in sorted(dictionary.all_expressions(), key=len, reverse=True):
        if expression in sentence:
            return expression
    return ""


def mining_tsv(units: list[MiningUnit]) -> str:
    return to_tsv([unit.to_note() for unit in units])


def mining_payload(
    units: list[MiningUnit],
    *,
    deck_name: str,
    model_name: str,
    field_map: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    """Return one AnkiConnect ``addNote`` payload per mining unit."""

    return [
        anki_connect_payload(
            [unit.to_note()],
            deck_name=deck_name,
            model_name=model_name,
            field_map=field_map,
        )
        for unit in units
    ]
