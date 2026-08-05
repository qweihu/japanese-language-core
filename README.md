# Nihongo Core（japanese-language-core）

Nihongo Core is the shared Japanese language capability layer for
[**Bunomi**](https://github.com/qweihu/Bunomi) and
[**Utayomi**](https://github.com/qweihu/Utayomi): contextual reading, kana
and romaji, furigana alignment, deinflection, line-preserving translation
contracts, dictionary metadata, grammar patterns, and export contracts.

The design principle is **deterministic contracts, optional heavy
dependencies**. Installing the base package costs zero runtime dependencies;
capabilities opt into libraries only when they need them.

---

## Why a unified core?

Previously, reading lived in `japanese-reading-core` while translation was an
ad-hoc Agent capability inside each application. Both Bunomi and Utayomi need
the same reading *and* translation building blocks, so the two capabilities
now live side by side under one versioned package:

- **Reading** is a deterministic engine problem: segmentation, contextual
  readings, kana normalization.
- **Translation** is an LLM capability: the core defines the contract,
  per-language conventions, and validation, while the actual translation is
  performed by an Agent or by a model endpoint you bring.

Both capabilities share a stable interchange format: line structure plus
`<ruby>…<rt>…</rt></ruby>` markup. The core guarantees that structure is
preserved; applications own their layout.

## Capability overview

| Module | What it provides |
| --- | --- |
| [`reading`](#reading) | Source-preserving tokenization + contextual readings (Sudachi preferred, PyKakasi fallback), `ReadingToken` contract |
| [`reading.kana`](#kana-and-romaji) | Hiragana/katakana conversion, width normalization, Hepburn romaji (pure Python) |
| [`reading.alignment`](#furigana-alignment) | Distribute a reading across kanji for ruby rendering |
| [`reading.deinflect`](#deinflection) | Best-effort conjugated form → dictionary form candidates |
| [`translation`](#translation) | Line-preserving contract, validation, language registry, glossary consistency |
| [`translation.provider`](#byo-llm-translation) | Agent mode (no API) or BYO-LLM mode (any OpenAI-compatible endpoint) |
| [`dictionary`](#dictionary) | Yomitan-format dictionary reader (term/kanji/tag/meta banks) + JLPT difficulty analysis |
| [`grammar`](#grammar) | Deterministic particle and common grammar-pattern detection |
| [`export`](#export) | Anki note contract and paired Markdown layout contract |
| `structure` | Shared ruby/line/placeholder validation helpers used by translation |

## Install

Python 3.10+.

```bash
# reading only (Sudachi / Fugashi / PyKakasi)
python3 -m pip install "japanese-language-core[reading] @ git+https://github.com/qweihu/japanese-language-core.git@v0.2.0"

# translation only (standard library, no dependencies)
python3 -m pip install "japanese-language-core[translation] @ git+https://github.com/qweihu/japanese-language-core.git@v0.2.0"

# everything
python3 -m pip install "japanese-language-core[all] @ git+https://github.com/qweihu/japanese-language-core.git@v0.2.0"
```

Local development:

```bash
git clone https://github.com/qweihu/japanese-language-core.git
cd japanese-language-core
python3 -m pip install -e ".[reading]"
```

The top-level package imports nothing heavy, so a translation-only install
stays lightweight. Heavy adapters are imported lazily inside the `reading`
submodule.

## Reading

The reading engine tokenizes Japanese text while preserving every input
character, whitespace, and line ending, then attaches normalized readings.

```python
from japanese_language_core.reading import create_engine, ReadingToken

engine = create_engine("auto")  # "auto" | "sudachi" | "pykakasi"
tokens = tuple(engine.tokens("雨が降り止むまでは帰れない"))

assert "".join(token.orig for token in tokens) == "雨が降り止むまでは帰れない"
for token in tokens:
    print(token.orig, token.hira, token.hepburn)
```

`ReadingToken` is intentionally small:

| Field | Meaning |
| --- | --- |
| `orig` | Exact source surface fragment; all fragments reconstruct the input |
| `hira` | Normalized hiragana reading (empty when no reading is available) |
| `hepburn` | Optional Hepburn romanization |

### Engine modes

| Mode | Behavior | Best for |
| --- | --- | --- |
| `auto` | Prefer Sudachi; fall back to PyKakasi if unavailable | Normal application use |
| `sudachi` | Require Sudachi and its dictionary | Strict production and CI |
| `pykakasi` | Use the Fugashi/PyKakasi fallback path | Compatibility and comparison |

A strict mode raises `EngineUnavailableError` instead of silently changing
engines. The `ReadingEngine` protocol is the only public boundary; consumers
never touch Sudachi `Morpheme`, Fugashi tag objects, or dictionary internals.

## Kana and romaji

Pure standard library utilities, useful in renderers and tests:

```python
from japanese_language_core.reading import (
    is_kana, is_kanji, is_hiragana, is_katakana,
    to_hiragana, to_katakana, normalize_width, to_romaji,
)

to_hiragana("ニホンゴ")      # "にほんご"
to_katakana("にほんご")      # "ニホンゴ"
to_hiragana("ﾆﾎﾝｺﾞ")        # "にほんご" (halfwidth + dakuten handled)
to_romaji("しんぶん")        # "shimbun" (Hepburn: n → m before b/m/p)
```

The romaji converter is a pragmatic Hepburn reader (including small-tsu
gemination and ん assimilation). For production-grade romanization, install
the `[reading]` extra and use the engine's `hepburn` field.

## Furigana alignment

Distribute a kana reading across kanji — the distribution problem behind ruby
rendering:

```python
from japanese_language_core.reading import align_reading

pairs = align_reading("食べる", "たべる")
# [("食", "た"), ("べ", "べ"), ("る", "る")]

pairs = align_reading("日本語", "にほんご")
# [("日本語", "にほんご")]
```

Kana in the term is matched verbatim; each kanji run greedily consumes kana
until the next kana of the term. Ambiguous compounds (e.g. 好き嫌い) may need
dictionary-level alignment, which `dictionary` metadata can supply; this is
the deterministic fallback.

## Deinflection

Best-effort conjugation → dictionary-form candidates:

```python
from japanese_language_core.reading import deinflect

for candidate in deinflect("食べていました"):
    print(candidate.word, candidate.reason)
# 食べる, "te-form + progressive + polite past"
```

The rule engine strips common suffixes (ます/ない/た/て/ている/すぎる/やすい/…
), reapplies dictionary-form endings, and emits several candidates when the
ending is ambiguous (行った → 行く/行つ/行る/行う). Callers with dictionary
data should filter candidates with `dictionary.lookup_terms`.

## Translation

Translation is an LLM capability. The core provides the **contract**,
**validation**, **language registry**, and **providers**; it never bundles a
model or an API key.

### Data model

```python
from japanese_language_core.translation import TranslationUnit, TranslationResult

unit = TranslationUnit("明日は晴れる。", "明天会放晴。")
result = TranslationResult(
    source_lang="ja", target_lang="zh-CN",
    units=[unit], provider="agent",
    warnings=[], errors=[],
)
result.ok  # True
```

### Validation

```python
from japanese_language_core.translation import validate_translation

errors, warnings = validate_translation(
    source_lines=["明日は晴れる。", "一緒に歩こう。"],
    translation_lines=["明天会放晴。", "一起走吧。"],
    paired=True,
)
```

Checks:

- line pairing (same number of non-empty lines, blank groups preserved);
- ruby/HTML hygiene (balanced tags, only `ruby`/`rt` allowed);
- source fidelity (stripping ruby reconstructs the original);
- placeholder preservation (`♪`, `[Chorus]`, `（…）`, `【…】`);
- kana leakage warnings (hiragana/katakana left in a translation line);
- glossary consistency (optional `TermGlossary`).

CLI:

```bash
python3 -m japanese_language_core.translation validate \
  --source source.txt --translation translation.txt --paired
```

Exit codes: `0` OK, `1` structural errors, `3` warnings only with
`--strict-warnings`.

### Language registry

```python
from japanese_language_core.translation import LanguageRegistry

registry = LanguageRegistry.from_package()
registry.default()       # LanguageInfo(code="zh-CN", ...)
registry.codes()         # ["en", "zh-CN"]
```

The machine-readable registry (`translation/data/languages.json`) drives
BYO-LLM prompts; the human-facing Markdown conventions for Agents live in the
`japanese-translation` skill's `references/`.

### Glossary consistency

```python
from japanese_language_core.translation import TermGlossary, GlossaryEntry

glossary = TermGlossary()
glossary.add(GlossaryEntry(source="明日", preferred="明天"))

errors, warnings = validate_translation(
    ["明日は晴れる。"], ["明天会放晴。"], paired=True, glossary=glossary,
)
```

Warns when a source term is left untranslated, when a non-preferred variant is
used, or when the same term is translated inconsistently across lines.

### Providers

Two execution modes, one validation contract:

| Provider | Mode | Description |
| --- | --- | --- |
| `AgentTranslator` | Agent | Marker contract: the calling Agent translates using the skill's conventions; no network call |
| `OpenAICompatibleTranslator` | BYO-LLM | Calls any OpenAI Chat Completions-compatible endpoint you configure |

```python
from japanese_language_core.translation import AgentTranslator, Translator

translator: Translator = AgentTranslator()
```

## BYO-LLM translation

Bring your own endpoint — Ollama, vLLM, LM Studio, OpenAI-compatible gateways:

```python
from japanese_language_core.translation import (
    OpenAICompatibleTranslator, TranslationUnit,
)

translator = OpenAICompatibleTranslator(
    base_url="http://localhost:11434/v1",  # /chat/completions is appended
    model="llama3.1",
    api_key=None,          # or JAPANESE_LANGUAGE_CORE_API_KEY env var
    temperature=0.2,
    max_tokens=2048,
)

result = translator.translate(
    [TranslationUnit("明日は晴れる。"), TranslationUnit("一緒に歩こう。")],
    target_lang="zh-CN",
)
for unit in result.units:
    print(unit.source, "→", unit.translation)
```

CLI:

```bash
export JAPANESE_LANGUAGE_CORE_API_KEY=sk-...
python3 -m japanese_language_core.translation translate \
  --source source.txt --target-lang zh-CN \
  --base-url https://api.example.com/v1 --model my-model
```

Behavior:

- the system prompt is built from the registered language's conventions;
- the output is parsed back into one translation per source line;
- a missing line raises `TranslateError` (no silent truncation);
- the result is validated with the same `validate_translation` contract.

For tests, inject a `transport` callable (default is a stdlib `urllib`
implementation):

```python
def fake_transport(url, headers, payload):
    return '{"choices": [{"message": {"content": "1. 明天会放晴。"}}]}'

translator = OpenAICompatibleTranslator(
    base_url="https://example.test/v1", model="test",
    transport=fake_transport,
)
```

## Dictionary

Reads dictionaries in the open **Yomitan format** (zip bundles), which gives
access to the community's existing dictionary ecosystem (JMdict-based,
JPDB/KANJIDIC frequency, pitch accent, etc.):

```python
from japanese_language_core.dictionary import YomitanDictionary

dictionary = YomitanDictionary("JMdict.zip")
terms = dictionary.lookup_terms("日本語")
for term in terms:
    print(term.reading, term.definitions, term.tags)
    print(term.frequency, term.pitch_accents)

kanji = dictionary.lookup_kanji("日")
print(kanji[0].onyomi, kanji[0].kunyomi, kanji[0].frequency)
```

Supported banks:

| Bank | Contents |
| --- | --- |
| `term_bank_*.json` | Expressions, readings, definitions, tags, rules, score, sequence |
| `term_meta_bank_*.json` | Frequency (`freq`) and pitch accent (`pitch`) |
| `kanji_bank_*.json` | On/kun readings, meanings, tags, stats (grade/strokes/…) |
| `kanji_meta_bank_*.json` | Kanji frequency |
| `tag_bank_*.json` | Tag definitions (part of speech, levels, categories) |
| `index.json` | Dictionary metadata (`title`, `format_version`, attribution) |

### JLPT difficulty analysis

```python
from japanese_language_core.dictionary import analyze_difficulty

profile = analyze_difficulty("日本語を勉強する。", dictionary)
print(profile.level_counts())  # e.g. {"n5": 2, "unknown": 1}
print(profile.score)           # 0..1, higher = easier
```

Pass a reading engine to use morphological segmentation instead of the
longest-match fallback:

```python
from japanese_language_core.reading import create_engine

profile = analyze_difficulty("日本語を勉強する。", dictionary, engine=create_engine("auto"))
```

## Grammar

Deterministic, surface-level helpers — not a replacement for morphological
analysis, but fast and testable:

```python
from japanese_language_core.grammar import find_particles, find_grammar

particles = find_particles("私は東京へ行きます。")
print([m.particle for m in particles])   # ["は", "へ"]

matches = find_grammar("食べているところです。")
print([m.name for m in matches])         # ["te-iru", "seeming"]
```

Particle detection treats kana runs as particles when they are a known
particle or end with one. Grammar patterns include te-form constructions
(ている/ておく/てしまう/てもいい/てはいけない/てほしい), obligations
(なければならない/ないといけない), potential (ことができる), conditionals
(たら/れば), and more.

## Export

### Anki

```python
from japanese_language_core.export import AnkiNote, to_tsv, build_note
from japanese_language_core.translation import TranslationUnit

note = build_note(
    TranslationUnit("日本語を勉強する。", "学习日语。"),
    expression="日本語", reading="にほんご",
    glossary="Japanese language", tags=["jlptN5"],
)
tsv = to_tsv([note])
```

`anki_connect_payload(...)` builds the `addNote` request shape for AnkiConnect;
the actual API call stays an application-layer concern.

### Paired Markdown

```python
from japanese_language_core.export import build_paired_markdown

markdown = build_paired_markdown(result.units)
```

Output: one source line, one translation line, one blank line per unit —
the layout contract Bunomi and simple exports share. Utayomi owns its final
lyric layout.

## CLI reference

```text
python -m japanese_language_core.translation validate
    --source FILE | -     source Japanese text
    --translation FILE | -  translated text
    --paired              require equal non-empty line counts
    --no-kana-warn        disable kana leakage warnings
    --glossary FILE       JSON glossary ({"entries": [...]})
    --strict-warnings     exit 3 when warnings exist

python -m japanese_language_core.translation translate
    --source FILE | -     source Japanese text
    --target-lang CODE    default zh-CN
    --base-url URL        OpenAI-compatible endpoint
    --model NAME          model identifier
    --api-key KEY         optional; env JAPANESE_LANGUAGE_CORE_API_KEY
    --output FILE         write translations to a file

python -m japanese_language_core.translation languages
    [--registry FILE]     list registered target languages
```

## Compatibility

`japanese_reading_core` is a thin re-export shim during the migration, so
existing imports keep working:

```python
from japanese_reading_core import create_engine  # old, still works
from japanese_language_core.reading import create_engine  # new code
```

New code should use `japanese_language_core.reading`; the shim will be removed
after the transition period.

## Design principles

- **Capabilities are opt-in submodules.** The top-level package imports
  nothing heavy; a translation-only install stays dependency-free.
- **Deterministic contracts.** `ReadingToken`, `TranslationUnit`, and the
  dictionary model are small, testable, versioned interfaces.
- **Translation is an LLM capability.** The core defines the contract,
  conventions, and validation; the actual translation is performed by the
  Agent (skill mode) or a user-supplied endpoint (BYO-LLM).
- **Evidence over replacement.** Dictionary data enriches and audits; it does
  not silently override the primary engine.
- **No product layer.** Lyric cleaning, layouts, UI, and user data stay in
  Bunomi/Utayomi.

## Boundaries (non-goals)

This repository is intentionally not:

- a translation engine itself (translation is an LLM capability);
- a lyric acquisition/cleaning tool (Utayomi's product layer);
- a furigana/HTML renderer or a language detector;
- a user-data store, cloud service, or provider of API keys;
- a Yomitan/JMdict distribution (consumes the format, does not bundle data).

## Testing

```bash
python3 -m unittest discover -s tests -v
```

The suite covers source preservation, contextual readings, kana/romaji,
furigana alignment, deinflection, translation validation, provider transport,
Yomitan parsing, JLPT analysis, grammar detection, and export round-trips.

## Roadmap

- grow reviewed contextual-reading fixtures;
- integrate community frequency/JLPT/pitch-accent dictionaries through the
  existing Yomitan reader;
- add glossary files as first-class skill assets;
- publish stable releases with compatibility notes;
- measure reading accuracy on independently maintained corpora.

## License

MIT. This project builds on open-source foundations (Sudachi, Fugashi,
PyKakasi, UniDic, and the Yomitan dictionary format); their licenses remain
with the respective projects.
