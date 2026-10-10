import unittest
import json
import re

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
            [TranslationUnit("明日は晴れる。"), TranslationUnit("一緒に歩こう。")],
            target_lang="zh-CN",
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
            translator.translate(
                [TranslationUnit("一行"), TranslationUnit("两行")],
                target_lang="zh-CN",
            )

    def test_unregistered_language_raises(self):
        translator = OpenAICompatibleTranslator(
            base_url="https://example.test/v1",
            model="test-model",
            transport=fake_transport,
        )
        with self.assertRaises(TranslateError):
            translator.translate([TranslationUnit("あ")], target_lang="xx")

    def test_retry_then_success(self):
        calls = {"count": 0}

        def flaky_transport(url, headers, payload):
            calls["count"] += 1
            if calls["count"] < 3:
                raise TranslateError("temporary failure")
            return '{"choices": [{"message": {"content": "1. 明天会放晴。"}}]}'

        translator = OpenAICompatibleTranslator(
            base_url="https://example.test/v1",
            model="test-model",
            max_retries=2,
            retry_backoff=0,
            transport=flaky_transport,
        )
        result = translator.translate(
            [TranslationUnit("明日は晴れる。")],
            target_lang="zh-CN",
        )
        self.assertTrue(result.ok)
        self.assertEqual(3, calls["count"])

    def test_long_input_is_chunked(self):
        calls = {"count": 0}
        source_lines = [
            "これは長い文です。" * 3,
            "これも長い文です。" * 3,
        ]

        def chunk_transport(url, headers, payload):
            calls["count"] += 1
            user = payload["messages"][1]["content"]
            numbered = [
                line for line in user.splitlines() if re.match(r"^\d+\.", line)
            ]
            content = "\n".join(
                f"{i}. 译文{i}" for i in range(1, len(numbered) + 1)
            )
            return json.dumps({"choices": [{"message": {"content": content}}]})

        translator = OpenAICompatibleTranslator(
            base_url="https://example.test/v1",
            model="test-model",
            max_chars_per_request=20,
            transport=chunk_transport,
        )
        result = translator.translate(
            [TranslationUnit(line) for line in source_lines],
            target_lang="en",
        )
        self.assertTrue(result.ok)
        self.assertEqual(2, calls["count"])
        self.assertEqual(len(source_lines), len(result.units))


if __name__ == "__main__":
    unittest.main()
