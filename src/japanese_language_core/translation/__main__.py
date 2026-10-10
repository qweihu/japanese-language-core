"""CLI: validate / translate / languages for the translation capability."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .contract import LanguageRegistry, TranslationUnit
from .glossary import TermGlossary
from .provider import OpenAICompatibleTranslator
from .validate import validate_translation


def _read(path: str) -> list[str]:
    if path == "-":
        return sys.stdin.read().splitlines()
    return Path(path).read_text(encoding="utf-8").splitlines()


def _translate(args: argparse.Namespace) -> int:
    source = _read(args.source)
    units = [TranslationUnit(line) for line in source]
    translator = OpenAICompatibleTranslator(
        base_url=args.base_url,
        model=args.model,
        api_key=args.api_key,
    )
    result = translator.translate(units, target_lang=args.target_lang)
    for warning in result.warnings:
        print(f"[警告] {warning}", file=sys.stderr)
    for error in result.errors:
        print(f"[错误] {error}", file=sys.stderr)
    output = "\n".join(unit.translation for unit in result.units)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(f"翻译已写入：{args.output}")
    else:
        print(output)
    return 0 if result.ok else 1


def _validate(args: argparse.Namespace) -> int:
    source = _read(args.source)
    translation = _read(args.translation)
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


def _languages(args: argparse.Namespace) -> int:
    registry = (
        LanguageRegistry.from_file(args.registry)
        if args.registry
        else LanguageRegistry.from_package()
    )
    for info in registry.codes():
        language = registry.get(info)
        marker = "（默认）" if language.default else ""
        print(f"{language.code}: {language.name}{marker}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m japanese_language_core.translation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="校验翻译结构")
    validate_parser.add_argument("--source", required=True)
    validate_parser.add_argument("--translation", required=True)
    validate_parser.add_argument("--paired", action="store_true")
    validate_parser.add_argument("--no-kana-warn", action="store_true")
    validate_parser.add_argument("--glossary")
    validate_parser.add_argument("--strict-warnings", action="store_true")
    validate_parser.set_defaults(func=_validate)

    translate_parser = subparsers.add_parser("translate", help="通过 BYO-LLM 端点翻译")
    translate_parser.add_argument("--source", required=True)
    translate_parser.add_argument(
        "--target-lang",
        required=True,
        help="目标语言代码；由调用方根据用户语境明确传入",
    )
    translate_parser.add_argument("--base-url", required=True)
    translate_parser.add_argument("--model", required=True)
    translate_parser.add_argument("--api-key")
    translate_parser.add_argument("--output")
    translate_parser.set_defaults(func=_translate)

    languages_parser = subparsers.add_parser("languages", help="列出已注册语言")
    languages_parser.add_argument("--registry")
    languages_parser.set_defaults(func=_languages)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
