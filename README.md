# Nihongo Core（japanese-language-core）

Nihongo Core is a professional Japanese language processing library for
Python: contextual reading, kana and romaji, furigana alignment,
deinflection, line-preserving translation contracts, dictionary metadata,
grammar patterns, and export contracts.

It is built around two ideas:

- **Deterministic contracts.** Core behaviors are small, testable, versioned
  interfaces — a reading token, a translation unit, a dictionary entry — so
  you can build reliable tooling on top of them.
- **Optional heavy dependencies.** The base package has zero runtime
  dependencies. Reading needs morphological dictionaries; translation is an
  LLM capability — you bring the endpoint. Everything else is lightweight.

---

## Feature overview

| Module | What it provides |
| --- | --- |
| [`reading`](#reading) | Source-preserving tokenization + contextual readings (`auto` / `sudachi` / `pykakasi`) |
| [`reading.kana`](#kana-and-romaji) | Hiragana/katakana conversion, width normalization, Hepburn romaji |
| [`reading.alignment`](#furigana-alignment) | Distribute readings across kanji for ruby rendering |
| [`reading.deinflect`](#deinflection) | Conjugated form → dictionary-form candidates |
| [`translation`](#translation) | Line-preserving contract, validation, language registry, glossary checks |
| [`translation.provider`](#byo-llm-translation) | Agent mode (no API) or BYO-LLM (any OpenAI-compatible endpoint) |
| [`dictionary`](#dictionary) | Yomitan-format dictionary reader + JLPT difficulty analysis |
| [`grammar`](#grammar) | Particle and common grammar-pattern detection |
| [`export`](#export) | Anki note contract and paired Markdown layout |

## Install

Python 3.10+.

### Virtual environments (recommended)

Always install into a virtual environment so your system Python stays clean.
If you do not have one yet, create it first:

```bash
python3 -m venv .venv          # create the environment
source .venv/bin/activate      # macOS/Linux; Windows: .venv\Scripts\activate
```

Then run the commands below inside the activated environment.

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

The top-level package imports nothing heavy. Heavy adapters load lazily inside
`reading`, so a translation-only installation stays dependency-free.

## Quick start

### 1. Get readings for a sentence

```python
from japanese_language_core.reading import create_engine

engine = create_engine("auto")
tokens = tuple(engine.tokens("雨が降り止むまでは帰れない"))
for token in tokens:
    print(token.orig, token.hira, token.hepburn)
```

The engine preserves the source exactly, so you get a guaranteed contract plus
readings:

```text
雨 あめ ame
が が ga
降り止む ふりやむ furiyamu
まで まで made
は は ha
帰れ かえれ kaere
ない ない nai
```

```python
assert "".join(token.orig for token in tokens) == "雨が降り止むまでは帰れない"
```

### 2. Validate a line-preserving translation

```bash
python3 -m japanese_language_core.translation validate \
  --source source.txt --translation translation.txt --paired
```

With `source.txt`:

```text
明日は晴れる。
一緒に歩こう。
```

and `translation.txt`:

```text
明天会放晴。
一起走吧。
```

you get:

```text
校验通过：2 行翻译，0 个警告
```

### 3. Translate with your own LLM endpoint

```python
from japanese_language_core.translation import (
    OpenAICompatibleTranslator, TranslationUnit,
)

translator = OpenAICompatibleTranslator(
    base_url="http://localhost:11434/v1", model="llama3.1",
)
result = translator.translate(
    [TranslationUnit("明日は晴れる。"), TranslationUnit("一緒に歩こう。")],
    target_lang="zh-CN",
)
for unit in result.units:
    print(unit.source, "→", unit.translation)
```

```text
明日は晴れる。 → 明天会放晴。
一緒に歩こう。 → 一起走吧。
```

## Reading

`create_engine` returns a `ReadingEngine` whose `tokens(text)` yields
`ReadingToken(orig, hira, hepburn)` fragments. The `orig` fields always
reconstruct the input, including whitespace and line endings.

```python
from japanese_language_core.reading import ReadingToken

token = ReadingToken("降り止む", "ふりやむ", "furiyamu")
```

### Engine modes

| Mode | Behavior | Best for |
| --- | --- | --- |
| `auto` | Prefer Sudachi; fall back to PyKakasi if unavailable | Normal use |
| `sudachi` | Require Sudachi and its dictionary | Strict production/CI |
| `pykakasi` | Fugashi/PyKakasi path | Compatibility and comparison |

Strict modes raise `EngineUnavailableError` instead of silently switching
engines. `ReadingEngine` is the only public boundary; you never touch Sudachi
`Morpheme`, Fugashi tag objects, or dictionary internals.

## Kana and romaji

Pure standard-library utilities:

```python
from japanese_language_core.reading import (
    to_hiragana, to_katakana, to_romaji, is_kana, is_kanji,
)

print(to_hiragana("ニホンゴ"))   # → にほんご
print(to_katakana("にほんご"))   # → ニホンゴ
print(to_hiragana("ﾆﾎﾝｺﾞ"))     # → にほんご  (halfwidth + dakuten)
print(to_romaji("しんぶん"))     # → shimbun   (Hepburn: n → m before b/m/p)
print(to_romaji("がっこう"))     # → gakkou    (small tsu doubles consonant)
```

The romaji converter is a pragmatic Hepburn reader. For production-grade
romanization, use the engine's `hepburn` field (requires the `[reading]` extra).

## Furigana alignment

`align_reading(term, reading)` distributes a kana reading across the kanji of
a term — the distribution problem behind ruby rendering:

```python
from japanese_language_core.reading import align_reading

print(align_reading("食べる", "たべる"))
```

```text
[('食', 'た'), ('べ', 'べ'), ('る', 'る')]
```

```python
print(align_reading("日本語", "にほんご"))
```

```text
[('日本語', 'にほんご')]
```

Kana in the term is matched verbatim; each kanji run consumes kana greedily
until the next kana of the term. Ambiguous compounds (好き嫌い) may need
dictionary-level alignment, which the `dictionary` capability can supply;
this function is the deterministic fallback.

## Deinflection

`deinflect(word)` returns dictionary-form candidates with the rule chain that
produced each one:

```python
from japanese_language_core.reading import deinflect

for candidate in deinflect("食べていました"):
    print(candidate.word, "|", candidate.reason)
```

```text
食べる | past + polite + progressive
```

(The full result also includes intermediate forms such as `食べている |
polite past`.) The rule engine strips common suffixes — ます/ない/た/て/ている/
すぎる/やすい and more — and emits multiple candidates when the ending is
ambiguous (行った → 行く/行つ/行る/行う). Filter candidates with
`dictionary.lookup_terms` when you have dictionary data.

## Translation

Translation is an LLM capability. The library provides the contract,
validation, language registry, and providers — never a bundled model or API
key.

### Data model

```python
from japanese_language_core.translation import TranslationUnit, TranslationResult

unit = TranslationUnit("明日は晴れる。", "明天会放晴。")
result = TranslationResult(
    source_lang="ja", target_lang="zh-CN",
    units=[unit], provider="agent",
)
print(result.ok)  # True
```

### Validation

```python
from japanese_language_core.translation import validate_translation

errors, warnings = validate_translation(
    source_lines=["明日は晴れる。", "一緒に歩こう。"],
    translation_lines=["明天会放晴。", "一起走吧。"],
    paired=True,
)
print(errors)    # []
print(warnings)  # []
```

Checks performed:

- line pairing (equal non-empty line counts, blank groups preserved);
- ruby/HTML hygiene (balanced tags, only `ruby`/`rt` allowed);
- source fidelity (stripping ruby reconstructs the original);
- placeholder preservation (`♪`, `[Chorus]`, `（…）`, `【…】`);
- kana leakage (hiragana/katakana left in a translation line);
- glossary consistency (optional).

CLI outcomes:

```bash
python3 -m japanese_language_core.translation validate \
  --source source.txt --translation translation.txt --paired
```

OK:

```text
校验通过：2 行翻译，0 个警告
```

Kana leak (a line left untranslated):

```text
[警告] 翻译行 2: 出现假名 3 处，可能是漏译（专名/引用除外）
校验通过：2 行翻译，1 个警告
```

Line mismatch:

```text
[错误] 行数不匹配：源 2 行，翻译 1 行
校验失败：1 个错误，0 个警告
```

Exit codes: `0` OK, `1` structural errors, `3` warnings only (with
`--strict-warnings`).

### Language registry

```bash
python3 -m japanese_language_core.translation languages
```

```text
en: English
zh-CN: 简体中文（默认）
```

```python
from japanese_language_core.translation import LanguageRegistry

registry = LanguageRegistry.from_package()
print(registry.default().code)  # zh-CN
print(registry.codes())         # ['en', 'zh-CN']
```

The machine-readable registry (`translation/data/languages.json`) drives
BYO-LLM prompts. Adding a language = register it there and (optionally) add
human-readable conventions for Agent use.

### Glossary consistency

```python
from japanese_language_core.translation import TermGlossary, GlossaryEntry

glossary = TermGlossary()
glossary.add(GlossaryEntry(source="明日", preferred="明天"))

errors, warnings = validate_translation(
    ["明日は晴れる。"], ["明天会放晴。"], paired=True, glossary=glossary,
)
print(warnings)  # []
```

It warns when a source term is left untranslated, when a non-preferred
variant is used, or when the same term is translated inconsistently across
lines.

## BYO-LLM translation

Bring your own OpenAI-compatible endpoint — Ollama, vLLM, LM Studio, gateways:

```python
from japanese_language_core.translation import (
    OpenAICompatibleTranslator, TranslationUnit,
)

translator = OpenAICompatibleTranslator(
    base_url="http://localhost:11434/v1",  # /chat/completions is appended
    model="llama3.1",
    api_key=None,          # or the JAPANESE_LANGUAGE_CORE_API_KEY env var
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

```text
明日は晴れる。 → 明天会放晴。
一緒に歩こう。 → 一起走吧。
```

CLI:

```bash
export JAPANESE_LANGUAGE_CORE_API_KEY=sk-...
python3 -m japanese_language_core.translation translate \
  --source source.txt --target-lang zh-CN \
  --base-url https://api.example.com/v1 --model my-model
```

What happens under the hood:

1. the system prompt is built from the registered language's conventions;
2. the model output is parsed back into one translation per source line;
3. a missing line raises `TranslateError` — no silent truncation;
4. the result is validated with the same `validate_translation` contract.

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

The dictionary reader consumes the open **Yomitan format** (zip bundles), the
de-facto standard for community Japanese dictionaries (JMdict-based,
frequency, pitch accent, JLPT tags, ...). A minimal `term_bank_1.json`:

```json
[
  ["日本語", "にほんご", ["language"], [], 0, ["Japanese language"], 100, ["jlptN5"]],
  ["勉強", "べんきょう", ["n", "vs"], [], 0, ["study"], 101, ["jlptN5"]]
]
```

```python
from japanese_language_core.dictionary import YomitanDictionary

dictionary = YomitanDictionary("JMdict.zip")
term = dictionary.lookup_terms("日本語")[0]
print(term.reading, term.definitions, term.tags, term.frequency)
```

```text
にほんご ['Japanese language'] ['language', 'jlptN5'] None
```

Kanji bank lookup:

```python
kanji = dictionary.lookup_kanji("日")[0]
print(kanji.onyomi, kanji.kunyomi, kanji.meanings)
```

```text
['ニチ', 'ジツ'] ['ひ'] ['day', 'sun']
```

Supported banks:

| Bank | Contents |
| --- | --- |
| `term_bank_*.json` | Expressions, readings, definitions, tags, rules, score, sequence |
| `term_meta_bank_*.json` | Frequency (`freq`) and pitch accent (`pitch`) |
| `kanji_bank_*.json` | On/kun readings, meanings, tags, stats |
| `kanji_meta_bank_*.json` | Kanji frequency |
| `tag_bank_*.json` | Tag definitions (part of speech, levels, categories) |
| `index.json` | Dictionary metadata |

### JLPT difficulty analysis

```python
from japanese_language_core.dictionary import analyze_difficulty

profile = analyze_difficulty("日本語を勉強する。", dictionary)
print(profile.level_counts(), profile.unknown, profile.score)
```

```text
{'n5': 3, 'unknown': 2} ['を', '。'] 5.0
```

Pass a reading engine to use morphological segmentation instead of the
longest-match fallback:

```python
from japanese_language_core.reading import create_engine

profile = analyze_difficulty("日本語を勉強する。", dictionary, engine=create_engine("auto"))
```

## Grammar

Deterministic, surface-level helpers — fast and testable, not a replacement
for morphological analysis:

```python
from japanese_language_core.grammar import find_particles, find_grammar

print([m.particle for m in find_particles("私は東京へ行きます。")])
```

```text
['は', 'へ']
```

```python
print([(m.name, m.matched) for m in find_grammar("食べているところです。")])
```

```text
[('te-iru', 'ている')]
```

Particle detection recognizes kana runs that are, or end with, a known
particle. Grammar patterns include te-form constructions (ている/ておく/
てしまう/てもいい/てはいけない/てほしい), obligations (なければならない/
ないといけない), potential (ことができる), conditionals (たら/れば), and more.

## Export

### Anki notes

```python
from japanese_language_core.export import build_note, to_tsv
from japanese_language_core.translation import TranslationUnit

note = build_note(
    TranslationUnit("日本語を勉強する。", "学习日语。"),
    expression="日本語", reading="にほんご",
    glossary="Japanese language", tags=["jlptN5"],
)
print(to_tsv([note]), end="")
```

```text
Expression	Reading	Glossary	Sentence	Translation	Audio	Pitch	Frequency	Tags
日本語	にほんご	Japanese language	日本語を勉強する。	学习日语。				jlptN5
```

`anki_connect_payload(...)` builds the `addNote` request shape for AnkiConnect;
the actual API call stays in your application.

### Paired Markdown

```python
from japanese_language_core.export import build_paired_markdown
from japanese_language_core.translation import TranslationUnit

markdown = build_paired_markdown([
    TranslationUnit("日本語を勉強する。", "学习日语。"),
    TranslationUnit("一緒に歩こう。", "一起走吧。"),
])
print(markdown, end="")
```

```text
日本語を勉強する。
学习日语。

一緒に歩こう。
一起走吧。
```

One source line, one translation line immediately below, one blank line
between groups.

## CLI reference

```text
python -m japanese_language_core.translation validate
    --source FILE | -        source Japanese text
    --translation FILE | -   translated text
    --paired                 require equal non-empty line counts
    --no-kana-warn           disable kana leakage warnings
    --glossary FILE          JSON glossary ({"entries": [...]})
    --strict-warnings        exit 3 when warnings exist

python -m japanese_language_core.translation translate
    --source FILE | -        source Japanese text
    --target-lang CODE       default zh-CN
    --base-url URL           OpenAI-compatible endpoint
    --model NAME             model identifier
    --api-key KEY            optional; env JAPANESE_LANGUAGE_CORE_API_KEY
    --output FILE            write translations to a file

python -m japanese_language_core.translation languages
    [--registry FILE]        list registered target languages
```

## Design principles

- **Capabilities are opt-in submodules.** The top-level package imports
  nothing heavy; a translation-only install stays dependency-free.
- **Deterministic contracts.** `ReadingToken`, `TranslationUnit`, and the
  dictionary model are small, testable, versioned interfaces.
- **Translation is an LLM capability.** The library defines the contract,
  conventions, and validation; you choose the executor (an Agent or a model
  endpoint you bring).
- **Evidence over replacement.** Dictionary data enriches and audits; it never
  silently overrides the primary engine.
- **No product layer.** Cleaning, layouts, UI, and user data stay in your
  application.

## Boundaries (non-goals)

This library is intentionally not:

- a translation engine itself (translation is an LLM capability);
- a lyric acquisition or cleaning tool;
- a furigana/HTML renderer or a language detector;
- a user-data store, cloud service, or provider of API keys;
- a dictionary data distribution (it consumes the Yomitan format, it does not
  bundle dictionary archives).

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
- add glossary files as first-class assets;
- publish stable releases with compatibility notes;
- measure reading accuracy on independently maintained corpora.

## License

MIT. This project builds on open-source foundations (Sudachi, Fugashi,
PyKakasi, UniDic, and the Yomitan dictionary format); their licenses remain
with the respective projects.
