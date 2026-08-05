<div align="center">

# japanese-reading-core

**A source-preserving, context-aware Japanese reading engine for Python.**

Japanese text is not read one character at a time. This project combines
morphological analysis, contextual readings, normalized kana, and a small
stable token contract so applications can build reliable furigana, ruby,
learning, search, and accessibility experiences on top of it.

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md)

</div>

## Overview

`japanese-reading-core` converts Japanese text into source-preserving
`ReadingToken` values. Each token carries the original surface text, a
hiragana reading, and an optional Hepburn romanization.

The package focuses on the reading problem itself:

- segmenting Japanese text into meaningful contextual units;
- obtaining readings from a context-aware morphological engine;
- providing a deterministic fallback when the preferred engine is unavailable;
- preserving every input character, whitespace, and line ending;
- exposing a small interface that application code can test and version.

It does not guess readings in an LLM prompt, and it does not force every
consumer to depend on a particular HTML or Markdown renderer.

## How it works

```text
Japanese text
    ↓
line / whitespace preservation
    ↓
contextual tokenization
    ↓
reading normalization
    ↓
ReadingToken(orig, hira, hepburn)
    ↓
application-specific rendering or analysis
```

For example, the engine treats `降り止む` as a contextual lexical unit and
returns `ふりやむ`. A consumer can then decide how to align that reading with
the kanji and okurigana in its own output format.

## Core contract

```python
from japanese_reading_core import ReadingToken, create_engine

engine = create_engine("auto")
tokens = tuple(engine.tokens("雨が降り止むまでは帰れない"))

assert all(isinstance(token, ReadingToken) for token in tokens)
assert "".join(token.orig for token in tokens) == "雨が降り止むまでは帰れない"
```

`ReadingToken` is intentionally small:

| Field | Meaning |
| --- | --- |
| `orig` | The exact source surface fragment. All fragments reconstruct the input. |
| `hira` | A normalized hiragana reading, or an empty string when no reading is available. |
| `hepburn` | Optional Hepburn romanization of the reading. |

The public engine boundary is:

```python
class ReadingEngine(Protocol):
    def tokens(self, text: str) -> Iterable[ReadingToken]: ...
```

Consumers should depend on this contract, not on Sudachi's `Morpheme`,
Fugashi tag objects, or third-party dictionary internals.

## Engine modes

| Mode | Behavior | Best for |
| --- | --- | --- |
| `auto` | Prefer Sudachi; fall back to PyKakasi if unavailable | Normal application use |
| `sudachi` | Require Sudachi and its dictionary | Strict production and CI checks |
| `pykakasi` | Use the Fugashi/PyKakasi fallback path | Compatibility and comparison |

```python
engine = create_engine("sudachi")
```

If a strict engine cannot be initialized, the package raises
`EngineUnavailableError`. It does not silently change a requested strict mode.

## Installation

Install the current release tag directly from GitHub:

```bash
python3 -m pip install \
  "japanese-reading-core @ git+https://github.com/qweihu/japanese-reading-core.git@v0.1.0"
```

For local development:

```bash
git clone https://github.com/qweihu/japanese-reading-core.git
cd japanese-reading-core
python3 -m pip install -e .
```

The package currently supports Python 3.10+ and uses SudachiPy,
`sudachidict-core`, Fugashi, UniDic-lite, and PyKakasi as its reading
adapters.

## Reading example

```python
from japanese_reading_core import create_engine

text = "雨が降り止むまでは帰れない"
engine = create_engine("auto")

for token in engine.tokens(text):
    print(token.orig, token.hira, token.hepburn)
```

The library returns reading data. Rendering it as HTML ruby, Markdown,
plain-text annotations, or another representation remains the responsibility
of the consuming application.

## Design principles

### Context before characters

Japanese readings depend on lexical boundaries, inflection, and context. The
engine asks a morphological analyzer for a reading of a contextual unit
before an application performs any visual alignment.

### Source preservation is an invariant

Whitespace, punctuation, Latin text, kana, line endings, and unknown fragments
must remain observable. A consumer can reject or report a broken result by
checking the concatenated `orig` fields.

### Evidence and rendering stay separate

Dictionary data can be used by a higher-level application as candidate or
audit evidence. This package does not silently overwrite the primary engine's
result with an unrelated dictionary lookup, and it does not bundle user data,
dictionary caches, or application-specific policy.

### Small interfaces are easier to audit

The package exposes adapters and normalized values, not the internal object
graphs of its underlying NLP libraries. This keeps integrations testable and
makes engine upgrades visible through versioned behavior changes.

## Scope and non-goals

This repository is intentionally not:

- a Japanese language detector;
- a furigana or HTML renderer;
- a translation system;
- a lyric acquisition or cleaning tool;
- a Yomitan/JMdict distribution;
- a user-data store or remote service.

Those concerns can be implemented by separate layers without changing the
reading contract.

## Testing and reproducibility

Run the unit tests with:

```bash
python3 -m unittest discover -s tests -v
```

The test suite checks contextual readings, PyKakasi selection, source
reconstruction, whitespace and newline preservation, kana normalization, and
invalid engine handling. Build a wheel with:

```bash
python3 -m build --wheel
```

Reading behavior is versioned. Applications should depend on a release tag or
a bounded package version rather than an unreviewed moving branch.

## Roadmap

- expand reviewed contextual-reading fixtures;
- add explicit diagnostics for ambiguous or unavailable readings;
- evaluate optional dictionary evidence without coupling it to the core API;
- publish stable package releases and compatibility notes;
- measure accuracy on independently maintained Japanese corpora.

## License

MIT License. See [LICENSE](LICENSE).
