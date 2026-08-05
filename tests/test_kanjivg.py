import tempfile
import unittest
from pathlib import Path

from japanese_language_core.dictionary import KanjiVGReader, parse_svg


SAMPLE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 109 109">
<kanji><g id="kvg:日"><path d="M1,1 L2,2"/><path d="M3,3 L4,4"/></g>
<radical>日</radical></kanji></svg>"""


class KanjiVGTests(unittest.TestCase):
    def test_parse_svg(self):
        entry = parse_svg(SAMPLE, "日")
        self.assertIsNotNone(entry)
        self.assertEqual(2, entry.total_strokes)
        self.assertEqual("日", entry.radical)

    def test_reader_from_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "kanji.svg"
            path.write_text(SAMPLE, encoding="utf-8")
            reader = KanjiVGReader(path)
            entry = reader.lookup("日")
            self.assertEqual(2, entry.total_strokes)


if __name__ == "__main__":
    unittest.main()
