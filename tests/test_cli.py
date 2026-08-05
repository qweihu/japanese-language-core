import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from contextlib import redirect_stderr
from pathlib import Path

from japanese_language_core.__main__ import main


class CliTests(unittest.TestCase):
    def test_reading_json_lines(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            rc = main(["reading", "--engine", "pykakasi", "日本語"])
        self.assertEqual(0, rc)
        payloads = [json.loads(line) for line in buffer.getvalue().strip().splitlines()]
        self.assertEqual("日本語", "".join(item["orig"] for item in payloads))
        self.assertTrue(any(item["hira"] for item in payloads))
        self.assertIn("part_of_speech", payloads[0])

    def test_validate_ok(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "src.txt"
            translation = Path(directory) / "tr.txt"
            source.write_text("明日は晴れる。\n", encoding="utf-8")
            translation.write_text("明天会放晴。\n", encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                rc = main(
                    [
                        "validate",
                        "--source",
                        str(source),
                        "--translation",
                        str(translation),
                        "--paired",
                    ]
                )
            self.assertEqual(0, rc)
            self.assertIn("校验通过", buffer.getvalue())

    def test_languages(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            rc = main(["languages"])
        self.assertEqual(0, rc)
        self.assertIn("zh-CN", buffer.getvalue())

    def test_reading_verbose_reports_engine(self):
        error_buffer = io.StringIO()
        with redirect_stdout(io.StringIO()):
            with redirect_stderr(error_buffer):
                rc = main(
                    ["reading", "--engine", "pykakasi", "--verbose", "日本語"]
                )
        self.assertEqual(0, rc)
        self.assertIn("engine=pykakasi", error_buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
