import unittest

from japanese_language_core.translation import (
    GlossaryEntry,
    LanguageRegistry,
    TermGlossary,
    TranslationUnit,
    validate_translation,
)
from japanese_language_core.translation.prompt import (
    build_system_prompt,
    build_user_prompt,
    parse_translation_output,
)


class TranslationContractTests(unittest.TestCase):
    def setUp(self):
        self.source = ["明日は晴れる。", "一緒に歩こう。"]
        self.ok = ["明天会放晴。", "一起走吧。"]

    def test_valid_paired_translation(self):
        errors, warnings = validate_translation(self.source, self.ok, paired=True)
        self.assertEqual(errors, [])

    def test_kana_leak_warns(self):
        leak = ["明天会放晴。", "一緒に歩こう。"]
        errors, warnings = validate_translation(self.source, leak, paired=True)
        self.assertEqual(errors, [])
        self.assertTrue(any("假名" in warning for warning in warnings))

    def test_line_count_mismatch(self):
        errors, warnings = validate_translation(self.source, self.ok[:1], paired=True)
        self.assertTrue(any("行数不匹配" in error for error in errors))

    def test_foreign_html_rejected(self):
        bad = ["<div>明天会放晴。</div>", "一起走吧。"]
        errors, warnings = validate_translation(self.source, bad, paired=True)
        self.assertTrue(any("HTML" in error for error in errors))

    def test_registry_default(self):
        registry = LanguageRegistry.from_package()
        self.assertEqual("zh-CN", registry.default().code)
        self.assertIn("en", registry.codes())

    def test_glossary_consistency(self):
        glossary = TermGlossary()
        glossary.add(GlossaryEntry(source="明日", preferred="明天"))
        errors, warnings = validate_translation(
            ["明日は晴れる。"],
            ["明天会放晴。"],
            paired=True,
            glossary=glossary,
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_prompt_roundtrip(self):
        registry = LanguageRegistry.from_package()
        language = registry.get("zh-CN")
        system = build_system_prompt(language)
        self.assertIn("简体中文", system)
        units = [TranslationUnit(line) for line in self.source]
        user = build_user_prompt(units)
        parsed = parse_translation_output("1. 明天会放晴。\n2. 一起走吧。")
        self.assertEqual(self.ok, parsed)


if __name__ == "__main__":
    unittest.main()
