import unittest

from japanese_language_core.structure import (
    check_placeholders,
    extract_placeholders,
    foreign_html_tags,
    strip_ruby,
)


class StructureTests(unittest.TestCase):
    def test_strip_ruby(self):
        self.assertEqual("日本語を読む", strip_ruby("<ruby>日本語<rt>にほんご</rt></ruby>を読む"))

    def test_foreign_html_detected(self):
        self.assertTrue(foreign_html_tags("<div>bad</div>"))
        self.assertFalse(foreign_html_tags("<ruby>日<rt>にち</rt></ruby>"))

    def test_placeholders(self):
        line = "♪ [Chorus] 君を（ずっと）待つ"
        tokens = extract_placeholders(line)
        self.assertIn("♪", tokens)
        self.assertIn("[Chorus]", tokens)
        self.assertIn("（ずっと）", tokens)

    def test_placeholder_loss_warns(self):
        warnings = check_placeholders(["♪ 明日"], ["明天"])
        self.assertEqual(len(warnings), 1)
        self.assertIn("♪", warnings[0])

    def test_placeholder_count_mismatch_warns(self):
        warnings = check_placeholders(["♪ ♪ 明日"], ["♪ 明天"])
        self.assertEqual(len(warnings), 1)
        self.assertIn("缺少 1 处", warnings[0])


if __name__ == "__main__":
    unittest.main()
