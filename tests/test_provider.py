import unittest

from japanese_language_core.translation import (
    OpenAICompatibleTranslator,
    TranslateError,
    TranslationUnit,
)


def fake_transport(url, headers, payload):
    self = fake_transport
    self.last_url = url
    self.last_headers = headers
    self.last_payload = payload
    return '{"choices": [{"message": {"content": "1. 明天会放晴。\\n2. 一起走吧。"}}]}'


class ProviderTests(unittest.TestCase):
    def test_openai_compatible_translate(self):
        fake_transport.last_url = None
        translator = OpenAICompatibleTranslator(
            base_url="https://example.test/v1",
            model="test-model",
            api_key="secret",
            transport=fake_transport,
        )
        result = translator.translate(
            [TranslationUnit("明日は晴れる。"), TranslationUnit("一緒に歩こう。")]
        )
        self.assertTrue(result.ok)
        self.assertEqual("https://example.test/v1/chat/completions", fake_transport.last_url)
        self.assertEqual("Bearer secret", fake_transport.last_headers["Authorization"])
        self.assertEqual("test-model", fake_transport.last_payload["model"])

    def test_short_output_raises(self):
        def short_transport(url, headers, payload):
            return '{"choices": [{"message": {"content": "只有一行"}}]}'

        translator = OpenAICompatibleTranslator(
            base_url="https://example.test/v1",
            model="test-model",
            transport=short_transport,
        )
        with self.assertRaises(TranslateError):
            translator.translate([TranslationUnit("一行"), TranslationUnit("两行")])

    def test_unregistered_language_raises(self):
        translator = OpenAICompatibleTranslator(
            base_url="https://example.test/v1",
            model="test-model",
            transport=fake_transport,
        )
        with self.assertRaises(TranslateError):
            translator.translate([TranslationUnit("あ")], target_lang="xx")


if __name__ == "__main__":
    unittest.main()
