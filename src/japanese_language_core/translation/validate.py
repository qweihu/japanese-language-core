"""Deterministic validation for line-preserving Japanese translations."""

from __future__ import annotations

import argparse
import sys

from ..structure import (
    balanced_tags,
    check_placeholders,
    content_lines,
    foreign_html_tags,
    kana_matches,
    ruby_fidelity_errors,
)
from .glossary import TermGlossary


def validate_translation(
    source_lines: list[str],
    translation_lines: list[str],
    *,
    paired: bool = False,
    kana_warning: bool = True,
    glossary: TermGlossary | None = None,
) -> tuple[list[str], list[str]]:
    """Return ``(errors, warnings)`` for a translation.

    Checks line pairing, ruby/HTML hygiene, source fidelity, placeholder
    preservation, kana leakage, and optional glossary consistency.
    """

    errors: list[str] = []
    warnings: list[str] = []

    for idx, line in enumerate(translation_lines, start=1):
        label = f"翻译行 {idx}"
        for tag in ("ruby", "rt"):
            if not balanced_tags(line, tag):
                errors.append(f"{label}: <{tag}> 标签不平衡")
        for tag in foreign_html_tags(line):
            errors.append(f"{label}: 出现非 ruby/rt 的 HTML 标签 {tag}")
        if kana_warning and kana_matches(line):
            count = len(kana_matches(line))
            warnings.append(f"{label}: 出现假名 {count} 处，可能是漏译（专名/引用除外）")

    errors.extend(ruby_fidelity_errors(source_lines))
    if paired:
        src_count = len(content_lines(source_lines))
        tgt_count = len(content_lines(translation_lines))
        if src_count != tgt_count:
            errors.append(f"行数不匹配：源 {src_count} 行，翻译 {tgt_count} 行")
    warnings.extend(check_placeholders(source_lines, translation_lines))
    if glossary is not None:
        warnings.extend(glossary.check_units(source_lines, translation_lines))
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="校验逐句日语翻译结构")
    parser.add_argument("--source", required=True, help="源日语文本文件（- 表示 stdin）")
    parser.add_argument("--translation", required=True, help="翻译文本文件（- 表示 stdin）")
    parser.add_argument("--paired", action="store_true", help="要求翻译行数与源行数一致")
    parser.add_argument("--no-kana-warn", action="store_true", help="关闭假名漏译警告")
    parser.add_argument("--glossary", help="术语表 JSON 文件")
    parser.add_argument("--strict-warnings", action="store_true", help="存在警告时退出码为 3")
    args = parser.parse_args(argv)

    def read(path: str) -> list[str]:
        if path == "-":
            return sys.stdin.read().splitlines()
        with open(path, encoding="utf-8") as handle:
            return handle.read().splitlines()

    source = read(args.source)
    translation = read(args.translation)
    glossary = TermGlossary.from_file(args.glossary) if args.glossary else None
    errors, warnings = validate_translation(
        source,
        translation,
        paired=args.paired,
        kana_warning=not args.no_kana_warn,
        glossary=glossary,
    )
    for error in errors:
        print(f"[错误] {error}", file=sys.stderr)
    for warning in warnings:
        print(f"[警告] {warning}")
    if errors:
        print(f"校验失败：{len(errors)} 个错误，{len(warnings)} 个警告", file=sys.stderr)
        return 1
    if warnings and args.strict_warnings:
        print(f"校验通过（含警告）：{len(warnings)} 个警告")
        return 3
    print(f"校验通过：{len(translation)} 行翻译，{len(warnings)} 个警告")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
