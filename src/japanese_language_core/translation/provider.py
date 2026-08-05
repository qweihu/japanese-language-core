"""Translation providers: the Agent itself, or a user-supplied LLM endpoint."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import time
from typing import Callable, Protocol
import urllib.error
import urllib.request

from .contract import (
    LanguageRegistry,
    TranslateError,
    TranslationResult,
    TranslationUnit,
)
from .prompt import build_system_prompt, build_user_prompt, parse_translation_output
from .validate import validate_translation


class Translator(Protocol):
    """Whoever performs the translation must honor this contract."""

    name: str

    def translate(
        self,
        units: list[TranslationUnit],
        *,
        source_lang: str = "ja",
        target_lang: str = "zh-CN",
    ) -> TranslationResult:
        ...


class AgentTranslator:
    """Marker for the Agent-as-translator mode.

    The calling Agent performs the translation itself using the
    ``japanese-translation`` skill's conventions. This class documents the
    contract and refuses to issue network calls; applications that call it
    directly should run ``validate_translation`` on the Agent's output.
    """

    name = "agent"

    def translate(
        self,
        units: list[TranslationUnit],
        *,
        source_lang: str = "ja",
        target_lang: str = "zh-CN",
    ) -> TranslationResult:
        raise TranslateError(
            "AgentTranslator 不发起网络调用：请由 Agent 按技能约定完成翻译，"
            "再对结果运行 validate_translation。"
        )


Transport = Callable[[str, dict[str, str], dict[str, object]], str]


def _default_transport(url: str, headers: dict[str, str], payload: dict[str, object]) -> str:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise TranslateError(f"翻译端点返回 HTTP {exc.code}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise TranslateError(f"无法连接翻译端点 {url}: {exc.reason}") from exc


@dataclass
class OpenAICompatibleTranslator:
    """Translate through any OpenAI Chat Completions-compatible endpoint.

    Users bring their own ``base_url`` and ``model`` (Ollama, vLLM, LM Studio,
    OpenAI-compatible gateways...). No default provider, no bundled key:
    ``api_key`` may come from the caller or the ``JAPANESE_LANGUAGE_CORE_API_KEY``
    environment variable.
    """

    base_url: str
    model: str
    api_key: str | None = None
    timeout: float = 60.0
    temperature: float = 0.2
    max_tokens: int = 2048
    max_retries: int = 2
    retry_backoff: float = 1.0
    max_chars_per_request: int = 4000
    transport: Transport = _default_transport
    name: str = field(default="openai-compatible", init=False)

    def _headers(self) -> dict[str, str]:
        key = self.api_key or os.environ.get("JAPANESE_LANGUAGE_CORE_API_KEY")
        return {"Authorization": f"Bearer {key}"} if key else {}

    def translate(
        self,
        units: list[TranslationUnit],
        *,
        source_lang: str = "ja",
        target_lang: str = "zh-CN",
    ) -> TranslationResult:
        registry = LanguageRegistry.from_package()
        language = registry.get(target_lang)
        url = self.base_url.rstrip("/") + "/chat/completions"
        result_units: list[TranslationUnit] = []
        warnings: list[str] = []
        errors: list[str] = []
        for chunk in self._chunk_units(units):
            partial, chunk_warnings, chunk_errors = self._translate_chunk(
                chunk, language, url
            )
            result_units.extend(partial)
            warnings.extend(chunk_warnings)
            errors.extend(chunk_errors)
        return TranslationResult(
            source_lang=source_lang,
            target_lang=target_lang,
            units=result_units,
            provider=self.name,
            warnings=warnings,
            errors=errors,
        )

    def _chunk_units(
        self, units: list[TranslationUnit]
    ) -> list[list[TranslationUnit]]:
        if not units:
            return []
        chunks: list[list[TranslationUnit]] = []
        current: list[TranslationUnit] = []
        size = 0
        for unit in units:
            cost = len(unit.source) + 1
            if current and size + cost > self.max_chars_per_request:
                chunks.append(current)
                current = []
                size = 0
            current.append(unit)
            size += cost
        if current:
            chunks.append(current)
        return chunks

    def _translate_chunk(
        self,
        units: list[TranslationUnit],
        language,
        url: str,
    ) -> tuple[list[TranslationUnit], list[str], list[str]]:
        payload: dict[str, object] = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": build_system_prompt(language)},
                {"role": "user", "content": build_user_prompt(units, language)},
            ],
        }
        last_error: TranslateError | None = None
        for attempt in range(self.max_retries + 1):
            try:
                raw = self.transport(url, self._headers(), payload)
                break
            except TranslateError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff * (attempt + 1))
        else:
            raise last_error  # type: ignore[misc]
        try:
            data = json.loads(raw)
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise TranslateError(f"翻译端点返回格式无法解析: {raw[:500]}") from exc
        lines = parse_translation_output(str(content))
        result_units = [
            TranslationUnit(unit.source, line)
            for unit, line in zip(units, lines)
        ]
        if len(result_units) != len(units):
            missing = len(units) - len(result_units)
            raise TranslateError(f"翻译输出行数不足：缺少 {missing} 行")
        errors, warnings = validate_translation(
            [unit.source for unit in units],
            [unit.translation for unit in result_units],
            paired=True,
            kana_warning=language.kana_warning,
        )
        return result_units, warnings, errors
