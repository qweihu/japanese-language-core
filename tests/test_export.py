import unittest

from japanese_language_core.export import AnkiNote, build_note, to_tsv
from japanese_language_core.translation import TranslationUnit


class ExportTests(unittest.TestCase):
    def test_anki_note_roundtrip(self):
        note = AnkiNote(
            expression="日本語",
            reading="にほんご",
            glossary="Japanese language",
            sentence="日本語を勉強する。",
            translation="学习日语。",
            tags=["jlptN5"],
        )
        row = note.to_tsv_row()
        restored = AnkiNote.from_tsv_row(row)
        self.assertEqual(note.expression, restored.expression)
        self.assertEqual(note.tags, restored.tags)

    def test_build_note_from_unit(self):
        unit = TranslationUnit("日本語を勉強する。", "学习日语。")
        note = build_note(unit, expression="日本語", reading="にほんご")
        self.assertEqual("日本語を勉強する。", note.sentence)
        self.assertEqual("学习日语。", note.translation)
        self.assertTrue(to_tsv([note]).startswith("Expression"))


if __name__ == "__main__":
    unittest.main()
