# Nihongo Core（japanese-language-core）

Shared Japanese language capabilities for **Bunomi** and **Utayomi**:
contextual reading, kana/romaji, furigana alignment, deinflection,
line-preserving translation contracts, dictionary metadata, grammar
patterns, and export contracts.

The package is dependency-light by default: `japanese-language-core` alone has
zero runtime dependencies. Capabilities opt into heavy libraries only when
they need them.

## Capabilities

| Module | What it provides |
| --- | --- |
| `reading` | Source-preserving tokenization + contextual readings (Sudachi preferred, PyKakasi fallback), `ReadingToken` contract |
| `reading.kana` | Hiragana/katakana conversion, width normalization, Hepburn romaji (pure Python) |
| `reading.alignment` | Distribute a reading across kanji (furigana alignment for ruby) |
| `reading.deinflect` | Best-effort conjugated form → dictionary form candidates |
| `translation` | Line-preserving translation contract, validation, language registry, glossary consistency |
| `translation.provider` | Agent mode (no API) or BYO-LLM mode (any OpenAI-compatible endpoint) |
| `dictionary` | Yomitan-format dictionary reader (term/kanji/tag/meta banks) + JLPT difficulty analysis |
| `grammar` | Deterministic particle and common grammar-pattern detection |
| `export` | Anki note contract and paired Markdown layout contract |

## Install

```bash
# reading only (Sudachi / Fugashi / PyKakasi)
python3 -m pip install "japanese-language-core[reading] @ git+https://github.com/qweihu/japanese-language-core.git@v0.2.0"

# translation only (standard library)
python3 -m pip install "japanese-language-core[translation] @ git+https://github.com/qweihu/japanese-language-core.git@v0.2.0"

# everything
python3 -m pip install "japanese-language-core[all] @ git+https://github.com/qweihu/japanese-language-core.git@v0.2.0"
```

For local development:

```bash
git clone https://github.com/qweihu/japanese-language-core.git
cd japanese-language-core
python3 -m pip install -e ".[reading]"
```

## Quickstart

### Reading

```python
from japanese_language_core.reading import create_engine

engine = create_engine("auto")
tokens = tuple(engine.tokens("雨が降り止むまでは帰れない"))
assert "".join(token.orig for token in tokens) == "雨が降り止むまでは帰れない"
for token in tokens:
    print(token.orig, token.hira, token.hepburn)
```

### Translation validation

```bash
python3 -m japanese_language_core.translation validate \
  --source source.txt --translation translation.txt --paired
```

### BYO-LLM translation

Bring your own OpenAI-compatible endpoint (Ollama, vLLM, gateways...):

```bash
python3 -m japanese_language_core.translation translate \
  --source source.txt --base-url http://localhost:11434/v1 \
  --model llama3.1
```

Or in Python:

```python
from japanese_language_core.translation import (
    OpenAICompatibleTranslator, TranslationUnit,
)

translator = OpenAICompatibleTranslator(
    base_url="http://localhost:11434/v1", model="llama3.1",
)
result = translator.translate(
    [TranslationUnit("明日は晴れる。")], target_lang="zh-CN",
)
print(result.units[0].translation)
```

The package never bundles a provider or an API key. `AgentTranslator` marks
the Agent-as-translator mode used by the `japanese-translation` skill: the
Agent translates and the same `validate_translation` contract is applied.

### Deinflection

```python
from japanese_language_core.reading import deinflect

for candidate in deinflect("食べていました"):
    print(candidate.word, candidate.reason)
```

### Dictionary metadata (Yomitan format)

```python
from japanese_language_core.dictionary import YomitanDictionary, analyze_difficulty

dictionary = YomitanDictionary("JMdict.zip")
terms = dictionary.lookup_terms("日本語")
profile = analyze_difficulty("日本語を勉強する。", dictionary)
print(profile.level_counts())
```

### Grammar

```python
from japanese_language_core.grammar import find_grammar, find_particles

print([m.particle for m in find_particles("私は東京へ行く。")])
print([m.name for m in find_grammar("食べているところです。")])
```

## Design principles

- **Capabilities are opt-in submodules.** The top-level package imports
  nothing heavy; a translation-only install stays dependency-free.
- **Deterministic contracts.** `ReadingToken`, `TranslationUnit`, and the
  dictionary model are small, testable, versioned interfaces.
- **Translation is an LLM capability.** The core defines the contract,
  conventions, and validation; the actual translation is performed by the
  Agent (skill mode) or a user-supplied model endpoint (BYO-LLM).
- **Compatibility.** `japanese_reading_core` is a thin re-export shim during
  the migration; new code imports `japanese_language_core.reading`.

## Boundaries (non-goals)

This repository is intentionally not:

- a translation engine itself (translation is an LLM capability);
- a lyric acquisition/cleaning tool (that is Utayomi's product layer);
- a furigana/HTML renderer, a language detector, or a user-data store;
- a cloud service or a provider of API keys.

The `japanese-translation` skill in `skills/` is the Agent-facing workflow
that consumes this core; Bunomi and Utayomi remain the product layers.

## Testing

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT. This repository builds on open-source foundations (Sudachi, Fugashi,
PyKakasi, UniDic, Yomitan dictionary format); their licenses remain with the
respective projects.
