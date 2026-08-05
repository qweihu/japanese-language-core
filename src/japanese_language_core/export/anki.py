"""Anki export contract: card data model and serializers.

The core defines the note model and payload shapes only; the AnkiConnect
call itself remains an application-layer concern.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ..translation.contract import TranslationUnit


@dataclass
class AnkiNote:
    """One Anki note with the fields jp-mining setups usually expect."""

    expression: str
    reading: str = ""
    glossary: str = ""
    sentence: str = ""
    translation: str = ""
    audio: str = ""
    pitch: str = ""
    frequency: str = ""
    tags: list[str] = field(default_factory=list)

    def to_tsv_row(self) -> str:
        values = [
            self.expression,
            self.reading,
            self.glossary,
            self.sentence,
            self.translation,
            self.audio,
            self.pitch,
            self.frequency,
            " ".join(self.tags),
        ]
        return "\t".join(value.replace("\t", " ") for value in values)

    @classmethod
    def from_tsv_row(cls, row: str) -> "AnkiNote":
        values = row.split("\t")
        while len(values) < 9:
            values.append("")
        return cls(
            expression=values[0],
            reading=values[1],
            glossary=values[2],
            sentence=values[3],
            translation=values[4],
            audio=values[5],
            pitch=values[6],
            frequency=values[7],
            tags=values[8].split(),
        )


_HEADER = "Expression\tReading\tGlossary\tSentence\tTranslation\tAudio\tPitch\tFrequency\tTags"


def to_tsv(notes: list[AnkiNote], *, header: bool = True) -> str:
    lines = [_HEADER] if header else []
    lines.extend(note.to_tsv_row() for note in notes)
    return "\n".join(lines) + "\n"


def build_note(
    unit: TranslationUnit,
    *,
    expression: str = "",
    reading: str = "",
    glossary: str = "",
    audio: str = "",
    pitch: str = "",
    frequency: str = "",
    tags: list[str] | None = None,
) -> AnkiNote:
    """Build a note from a translation unit, filling sentence/translation."""

    return AnkiNote(
        expression=expression,
        reading=reading,
        glossary=glossary,
        sentence=unit.source,
        translation=unit.translation,
        audio=audio,
        pitch=pitch,
        frequency=frequency,
        tags=list(tags or []),
    )


def anki_connect_payload(
    notes: list[AnkiNote],
    *,
    deck_name: str,
    model_name: str,
    field_map: dict[str, str] | None = None,
) -> dict[str, object]:
    """Build the ``addNote`` payload for AnkiConnect (per note).

    ``field_map`` maps Anki field names to AnkiNote attribute names; defaults
    to the standard jp-mining-ish field set.
    """

    mapping = field_map or {
        "Expression": "expression",
        "Reading": "reading",
        "Glossary": "glossary",
        "Sentence": "sentence",
        "Translation": "translation",
        "Audio": "audio",
        "Pitch": "pitch",
        "Frequency": "frequency",
    }
    note = notes[0]
    return {
        "action": "addNote",
        "version": 6,
        "params": {
            "note": {
                "deckName": deck_name,
                "modelName": model_name,
                "fields": {
                    name: getattr(note, attribute, "")
                    for name, attribute in mapping.items()
                },
                "tags": list(note.tags),
            }
        },
    }
