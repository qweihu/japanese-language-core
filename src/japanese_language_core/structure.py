"""Shared text-structure contract: ruby hygiene, line pairing, placeholders."""

from __future__ import annotations

from collections import Counter
import re


RUBY_RE = re.compile(r"<ruby>(.*?)<rt>(.*?)</rt></ruby>", re.S)
TAG_RE = re.compile(r"<[^>]+>")
KANA_RE = re.compile(r"[\u3041-\u3096\u30a1-\u30f6\uff66-\uff9d]")

# Tokens that must survive a translation step verbatim.
PLACEHOLDER_RE = re.compile(
    r"[\u266a\u266b\u266c\u2669]|\[[^\]]+\]|（[^）]*）|【[^】]*】|\{[^}]*\}"
)


def strip_ruby(line: str) -> str:
    """Remove ruby/rt markup and return the underlying surface text."""

    return TAG_RE.sub("", RUBY_RE.sub(r"\1", line))


def balanced_tags(line: str, tag: str) -> bool:
    opens = len(re.findall(rf"<{tag}>", line))
    closes = len(re.findall(rf"</{tag}>", line))
    return opens == closes


def foreign_html_tags(line: str) -> list[str]:
    """Return tags in ``line`` other than ruby/rt."""

    foreign: list[str] = []
    for tag in TAG_RE.findall(line):
        name = tag.lstrip("</").rstrip(">").split()[0]
        if name not in {"ruby", "rt"}:
            foreign.append(tag)
    return foreign


def kana_matches(line: str) -> list[str]:
    return KANA_RE.findall(line)


def content_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if line.strip()]


def extract_placeholders(line: str) -> list[str]:
    """Return placeholder tokens found in a line (duplicates preserved)."""

    return [match.group(0) for match in PLACEHOLDER_RE.finditer(line)]


def check_placeholders(
    source_lines: list[str], translation_lines: list[str]
) -> list[str]:
    """Warn when a placeholder is missing or its count differs in the
    matching translation line."""

    warnings: list[str] = []
    src_content = content_lines(source_lines)
    tgt_content = content_lines(translation_lines)
    for index, (source, translation) in enumerate(
        zip(src_content, tgt_content), start=1
    ):
        source_counts = Counter(extract_placeholders(source))
        target_counts = Counter(extract_placeholders(translation))
        for token, count in source_counts.items():
            present = target_counts.get(token, 0)
            if present < count:
                missing = count - present
                warnings.append(
                    f"翻译行 {index}: 占位符 {token!r} 缺少 {missing} 处"
                )
    return warnings


def ruby_fidelity_errors(source_lines: list[str]) -> list[str]:
    """Verify ruby annotations in source lines reconstruct the plain text."""

    errors: list[str] = []
    for idx, line in enumerate(source_lines, start=1):
        if "<ruby>" not in line:
            continue
        if strip_ruby(line) != RUBY_RE.sub(r"\1", line):
            errors.append(f"源行 {idx}: ruby 剥离后与原文不一致")
    return errors
