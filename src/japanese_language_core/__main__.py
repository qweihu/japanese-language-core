"""Top-level CLI for Nihongo Core.

One entry point for Agent and terminal use:

    python -m japanese_language_core reading [--engine auto] [TEXT|-]
    python -m japanese_language_core validate --source S --translation T [--paired] ...
    python -m japanese_language_core translate --source S --base-url URL --model M ...
    python -m japanese_language_core languages [--registry FILE]

Agents should prefer the CLI for deterministic operations; applications can
import the Python API directly.
"""

from __future__ import annotations

import argparse
import json
import sys

from .reading import create_engine
from .translation.__main__ import _languages, _translate, _validate


def _reading(args: argparse.Namespace) -> int:
    engine = create_engine(args.engine)
    if args.verbose:
        print(f"engine={engine.name}", file=sys.stderr)
    text = sys.stdin.read() if args.text in (None, "-") else args.text
    for token in engine.tokens(text):
        print(
            json.dumps(
                {"orig": token.orig, "hira": token.hira, "hepburn": token.hepburn},
                ensure_ascii=False,
            )
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m japanese_language_core",
        description="Nihongo Core CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    reading = subparsers.add_parser("reading", help="输出读音 token（JSON Lines）")
    reading.add_argument(
        "--engine", default="auto", choices=["auto", "sudachi", "pykakasi"]
    )
    reading.add_argument(
        "--verbose", action="store_true", help="把实际使用的引擎名打印到 stderr"
    )
    reading.add_argument("text", nargs="?", default="-", help="文本或 -（stdin）")
    reading.set_defaults(func=_reading)

    validate = subparsers.add_parser("validate", help="校验逐句翻译")
    validate.add_argument("--source", required=True)
    validate.add_argument("--translation", required=True)
    validate.add_argument("--paired", action="store_true")
    validate.add_argument("--no-kana-warn", action="store_true")
    validate.add_argument("--glossary")
    validate.add_argument("--strict-warnings", action="store_true")
    validate.set_defaults(func=_validate)

    translate = subparsers.add_parser("translate", help="通过 BYO-LLM 端点翻译")
    translate.add_argument("--source", required=True)
    translate.add_argument("--target-lang", default="zh-CN")
    translate.add_argument("--base-url", required=True)
    translate.add_argument("--model", required=True)
    translate.add_argument("--api-key")
    translate.add_argument("--output")
    translate.set_defaults(func=_translate)

    languages = subparsers.add_parser("languages", help="列出已注册语言")
    languages.add_argument("--registry")
    languages.set_defaults(func=_languages)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
