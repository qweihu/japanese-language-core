# Nihongo Core（japanese-language-core）

Bunomi と Utayomi が共有する日本語処理コア：文脈付き読み、かな/ローマ字、
読み-漢字アライメント、活用形復元、行単位翻訳コントラクト、辞書メタデータ、
文法パターン検出、エクスポート契約。

設計方針は**決定的な契約 + 必要に応じた重い依存**です。ベースパッケージは
依存ゼロで、能力ごとに追加インストールします。

## なぜひとつのコアに？

以前は読みが `japanese-reading-core`、翻訳は各アプリ内のアドホックな
Agent 能力でした。Bunomi と Utayomi は同じ読み・翻訳の部品を必要とするため、
2 つの能力をひとつのバージョン管理されたパッケージに統合しました：

- **読み**は決定的エンジンの問題（分かち書き、文脈付き読み、かな正規化）；
- **翻訳**は LLM 能力（コアは契約・言語別規約・検証を定義し、実際の翻訳は
  Agent またはユーザー指定のモデルエンドポイントが実行）。

両者は行構造と `<ruby>…<rt>…</rt></ruby>` マークアップという安定した交換
フォーマットを共有します。コアは構造の保持を保証し、レイアウトはアプリ層。

## 能力一覧

| モジュール | 内容 |
| --- | --- |
| `reading` | 原文保持の分かち書き + 文脈付き読み（Sudachi 優先、PyKakasi フォールバック） |
| `reading.kana` | かな変換、全半角正規化、ヘボン式ローマ字（純標準ライブラリ） |
| `reading.alignment` | 読みを漢字へ分配（furigana アライメント） |
| `reading.deinflect` | 活用形 → 辞書形 の候補生成 |
| `translation` | 行単位翻訳コントラクト、検証、言語レジストリ、用語一貫性 |
| `translation.provider` | Agent モード（API 不要）または BYO-LLM（OpenAI 互換エンドポイント） |
| `dictionary` | Yomitan 形式辞書リーダー + JLPT 難易度分析 |
| `grammar` | 助詞と定型文法パターンの検出 |
| `export` | Anki ノート契約と対訳 Markdown 契約 |

## インストール

```bash
python3 -m pip install "japanese-language-core[reading] @ git+https://github.com/qweihu/japanese-language-core.git@v0.2.0"
```

`[translation]` は標準ライブラリのみ、`[all]` で全部入りです。

## クイックスタート

```python
from japanese_language_core.reading import create_engine

engine = create_engine("auto")
tokens = tuple(engine.tokens("雨が降り止むまでは帰れない"))
assert "".join(token.orig for token in tokens) == "雨が降り止むまでは帰れない"
```

翻訳検証：

```bash
python3 -m japanese_language_core.translation validate \
  --source source.txt --translation translation.txt --paired
```

BYO-LLM 翻訳：

```bash
python3 -m japanese_language_core.translation translate \
  --source source.txt --base-url http://localhost:11434/v1 --model llama3.1
```

```python
from japanese_language_core.translation import (
    OpenAICompatibleTranslator, TranslationUnit,
)

translator = OpenAICompatibleTranslator(
    base_url="http://localhost:11434/v1", model="llama3.1",
)
result = translator.translate([TranslationUnit("明日は晴れる。")], target_lang="zh-CN")
```

## 読み

`ReadingToken(orig, hira, hepburn)` が最小契約。`create_engine("auto"|"sudachi"|"pykakasi")`
でエンジンを選択し、`tokens(text)` が原文を完全に再構成します。
辞書データは証拠として使いますが、主エンジンを静かに上書きしません。

## かな・ローマ字

```python
from japanese_language_core.reading import to_hiragana, to_katakana, to_romaji

to_hiragana("ニホンゴ")   # "にほんご"
to_katakana("にほんご")   # "ニホンゴ"
to_romaji("しんぶん")     # "shimbun"
```

## アライメントと活用形

```python
from japanese_language_core.reading import align_reading, deinflect

align_reading("食べる", "たべる")  # [("食", "た"), ("べ", "べ"), ("る", "る")]
[c.word for c in deinflect("食べていました")]  # "食べる" などを含む候補
```

## 辞書と JLPT

```python
from japanese_language_core.dictionary import YomitanDictionary, analyze_difficulty

dictionary = YomitanDictionary("JMdict.zip")
profile = analyze_difficulty("日本語を勉強する。", dictionary)
print(profile.level_counts())
```

Yomitan 形式（`term_bank` / `kanji_bank` / `tag_bank` / meta bank）を読み、
頻度・声調・JLPT タグを利用できます。

## 文法

```python
from japanese_language_core.grammar import find_particles, find_grammar

[m.particle for m in find_particles("私は東京へ行きます。")]  # ["は", "へ"]
[m.name for m in find_grammar("食べているところです。")]      # ["te-iru", "seeming"]
```

## エクスポート

```python
from japanese_language_core.export import build_note, to_tsv, build_paired_markdown

note = build_note(TranslationUnit("日本語を勉強する。", "学习日语。"), expression="日本語")
print(to_tsv([note]))
```

## 設計原則

- 能力はサブモジュール単位でオプトイン。トップレベルは重い import をしない。
- 契約は小さく決定的（`ReadingToken`、`TranslationUnit`、辞書モデル）。
- 翻訳自体は LLM 能力：コアは契約・検証・言語レジストリを提供し、
  実行は Agent（スキルモード）かユーザー指定のエンドポイント（BYO-LLM）。
- 歌詞クリーニング、レイアウト、UI、ユーザーデータはコアに含めない。

## 互換性

`japanese_reading_core` は移行期間の互換シムです。新しいコードは
`japanese_language_core.reading` を import してください。

## ライセンス

MIT。依存 OSS（Sudachi、Fugashi、PyKakasi、UniDic、Yomitan 辞書形式）の
ライセンスは各プロジェクトに帰属します。
