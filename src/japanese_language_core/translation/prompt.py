"""Prompt construction for BYO-LLM translation providers."""

from __future__ import annotations

import re

from .contract import LanguageInfo, TranslationUnit


def build_system_prompt(language: LanguageInfo) -> str:
    lines = [
        "你是日语翻译引擎，输出逐句、逐行对应的目标语言翻译。",
        f"目标语言：{language.name}（{language.code}）",
    ]
    for key, value in language.conventions.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "- 保持源文本的换行与空行分组，一行对应一行，不合并、不拆分句子。",
            "- 保留标题、占位符（♪、[Chorus]、括号内容等）与未翻译的专名。",
            "- 只输出翻译文本，不添加译注、赏析或摘要。",
        ]
    )
    return "\n".join(lines)


def build_user_prompt(
    units: list[TranslationUnit], language: LanguageInfo | None = None
) -> str:
    lines = [
        "请逐行翻译以下文本，每行输出一行译文，不要添加行号以外的内容："
    ]
    if language is not None and language.examples:
        lines.append("示例：")
        for source, translation in language.examples:
            lines.append(f"  {source} → {translation}")
        lines.append("")
    for index, unit in enumerate(units, start=1):
        lines.append(f"{index}. {unit.source}")
    return "\n".join(lines)


_NUMBERED_RE = re.compile(r"^\s*\d+[.:、)\]]?\s*")


def parse_translation_output(text: str) -> list[str]:
    """Split provider output into one translation per source line."""

    lines = [line.rstrip() for line in text.splitlines()]
    return [_NUMBERED_RE.sub("", line) for line in lines if line.strip()]
