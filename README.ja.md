# Nihongo Core（japanese-language-core）

Nihongo Core は Python 向けのプロフェッショナルな日本語処理ライブラリです：
文脈付き読み、かな/ローマ字、読み-漢字アライメント、活用形復元、行単位翻訳
コントラクト、辞書メタデータ、文法パターン検出、エクスポート契約。

設計の柱：

- **決定的な契約**：読みトークン、翻訳ユニット、辞書エントリなどは小さく
  テスト可能でバージョン管理されたインターフェース。
- **依存は必要に応じて**：ベースは依存ゼロ。読みは形態素辞書が必要、
  翻訳は LLM 能力（エンドポイントはユーザーが用意）。

## インストール

```bash
python3 -m pip install "japanese-language-core[reading] @ git+https://github.com/qweihu/japanese-language-core.git@v0.2.0"
```

`[translation]` は標準ライブラリのみ、`[all]` で全部入りです。

## クイックスタート

読み：

```python
from japanese_language_core.reading import create_engine

engine = create_engine("auto")
tokens = tuple(engine.tokens("雨が降り止むまでは帰れない"))
for token in tokens:
    print(token.orig, token.hira, token.hepburn)
```

```text
雨 あめ ame
が が ga
降り止む ふりやむ furiyamu
まで まで made
は は ha
帰れ かえれ kaere
ない ない nai
```

翻訳検証：

```bash
python3 -m japanese_language_core.translation validate \
  --source source.txt --translation translation.txt --paired
```

```text
校验通过：2 行翻译，0 个警告
```

BYO-LLM 翻訳：

```python
from japanese_language_core.translation import (
    OpenAICompatibleTranslator, TranslationUnit,
)

translator = OpenAICompatibleTranslator(
    base_url="http://localhost:11434/v1", model="llama3.1",
)
result = translator.translate([TranslationUnit("明日は晴れる。")], target_lang="zh-CN")
print(result.units[0].translation)  # 明天会放晴。
```

## 読み

`create_engine("auto"|"sudachi"|"pykakasi")` がエンジンを返し、`tokens(text)`
が `ReadingToken(orig, hira, hepburn)` を生成。`orig` は常に入力を再構成します。

```python
from japanese_language_core.reading import ReadingToken

token = ReadingToken("降り止む", "ふりやむ", "furiyamu")
```

## かな・ローマ字

```python
from japanese_language_core.reading import to_hiragana, to_katakana, to_romaji

print(to_hiragana("ニホンゴ"))   # にほんご
print(to_katakana("にほんご"))   # ニホンゴ
print(to_romaji("しんぶん"))     # shimbun
print(to_romaji("がっこう"))     # gakkou
```

## アライメントと活用形

```python
from japanese_language_core.reading import align_reading, deinflect

print(align_reading("食べる", "たべる"))
# [('食', 'た'), ('べ', 'べ'), ('る', 'る')]

for candidate in deinflect("食べていました"):
    print(candidate.word, "|", candidate.reason)
# 食べる | past + polite + progressive
```

## 辞書と JLPT

```python
from japanese_language_core.dictionary import YomitanDictionary, analyze_difficulty

dictionary = YomitanDictionary("JMdict.zip")
term = dictionary.lookup_terms("日本語")[0]
print(term.reading, term.definitions, term.tags)

profile = analyze_difficulty("日本語を勉強する。", dictionary)
print(profile.level_counts(), profile.unknown, profile.score)
# {'n5': 3, 'unknown': 2} ['を', '。'] 5.0
```

Yomitan 形式（`term_bank` / `kanji_bank` / `tag_bank` / meta bank）を読み、
頻度・声調・JLPT タグを利用できます。

## 文法

```python
from japanese_language_core.grammar import find_particles, find_grammar

print([m.particle for m in find_particles("私は東京へ行きます。")])
# ['は', 'へ']
print([(m.name, m.matched) for m in find_grammar("食べているところです。")])
# [('te-iru', 'ている')]
```

## エクスポート

```python
from japanese_language_core.export import build_note, to_tsv, build_paired_markdown
from japanese_language_core.translation import TranslationUnit

note = build_note(TranslationUnit("日本語を勉強する。", "学习日语。"), expression="日本語")
print(to_tsv([note]), end="")
```

```text
Expression	Reading	Glossary	Sentence	Translation	Audio	Pitch	Frequency	Tags
日本語	にほんご		日本語を勉強する。	学习日语。				jlptN5
```

```python
print(build_paired_markdown([TranslationUnit("日本語を勉強する。", "学习日语。")]), end="")
```

```text
日本語を勉強する。
学习日语。
```

## CLI リファレンス

```text
python -m japanese_language_core.translation validate
    --source FILE | -       ソース日本語テキスト
    --translation FILE | -  翻訳テキスト
    --paired                空でない行数を一致させる
    --no-kana-warn          仮名漏れ警告を無効化
    --glossary FILE         用語表 JSON
    --strict-warnings       警告があると終了コード 3

python -m japanese_language_core.translation translate
    --source FILE | -       ソース
    --target-lang CODE      デフォルト zh-CN
    --base-url URL          OpenAI 互換エンドポイント
    --model NAME            モデル
    --api-key KEY           任意；環境変数 JAPANESE_LANGUAGE_CORE_API_KEY
    --output FILE           翻訳をファイルに書く

python -m japanese_language_core.translation languages
    [--registry FILE]       登録済み言語を一覧表示
```

## 設計原則

- 能力はサブモジュール単位でオプトイン。トップレベルは重い import をしない。
- 契約は小さく決定的（`ReadingToken`、`TranslationUnit`、辞書モデル）。
- 翻訳自体は LLM 能力：ライブラリは契約・検証・言語レジストリを提供し、
  実行は Agent かユーザー指定のエンドポイント。
- 辞書データは証拠：主エンジンを静かに上書きしない。
- クリーニング、レイアウト、UI、ユーザーデータはライブラリに含めない。

## 境界（非目標）

- 翻訳エンジン本体（翻訳は LLM 能力）；
- 歌詞の取得・クリーニングツール；
- furigana/HTML レンダラー、言語検出器；
- ユーザーデータストア、クラウドサービス、API キー提供；
- 辞書データの配布（Yomitan 形式を読むだけで、辞書アーカイブは同梱しない）。

## テスト

```bash
python3 -m unittest discover -s tests -v
```

## ライセンス

MIT。依存 OSS（Sudachi、Fugashi、PyKakasi、UniDic、Yomitan 辞書形式）の
ライセンスは各プロジェクトに帰属します。
