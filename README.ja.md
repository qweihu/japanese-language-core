<div align="center">

# japanese-reading-core

**原文を保持し、文脈を理解する Python 向け日本語読みエンジン。**

日本語は文字を一つずつ読めばよいものではありません。本プロジェクトは形態素解析、
文脈に応じた読み、かなの正規化、安定した token 契約を組み合わせ、振り仮名、学習、
検索、アクセシビリティなどのアプリケーションに再利用可能な読みの基盤を提供します。

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md)

</div>

## 概要

`japanese-reading-core` は日本語テキストを、入力を復元できる `ReadingToken` に変換します。
各 token には元の表層文字列、ひらがなの読み、任意の Hepburn 式ローマ字が含まれます。

このプロジェクトが扱うのは「日本語をどのように読むか」という基盤部分です。

- 文脈を持つ形態素単位へ分割する；
- 文脈対応の形態素エンジンから読みを取得する；
- 優先エンジンが利用できない場合に決定的なフォールバックを提供する；
- 文字、空白、句読点、改行を保持する；
- 小さく安定したインターフェースとして公開する。

大規模言語モデルに読みを推測させるものではなく、特定の HTML や Markdown レンダラーを
利用者に強制するものでもありません。

## 処理の流れ

```text
日本語テキスト
    ↓
行構造と空白の保持
    ↓
文脈形態素解析
    ↓
読みの正規化
    ↓
ReadingToken(orig, hira, hepburn)
    ↓
利用側アプリケーションで描画または分析
```

例えば `降り止む` は文脈を持つ一つの語彙単位として処理され、`ふりやむ` が返されます。
漢字と送り仮名をどのように表示上対応させるかは、利用側アプリケーションが決定します。

## コア契約

```python
from japanese_reading_core import ReadingToken, create_engine

engine = create_engine("auto")
tokens = tuple(engine.tokens("雨が降り止むまでは帰れない"))

assert all(isinstance(token, ReadingToken) for token in tokens)
assert "".join(token.orig for token in tokens) == "雨が降り止むまでは帰れない"
```

| フィールド | 意味 |
| --- | --- |
| `orig` | 元の表層文字列。全 token を連結すると入力を復元できる |
| `hira` | 正規化されたひらがなの読み。読みがない場合は空文字列 |
| `hepburn` | 任意の Hepburn 式ローマ字 |

利用側は `ReadingEngine.tokens(text)` と `ReadingToken` に依存し、Sudachi の `Morpheme`、
Fugashi の tag オブジェクト、外部辞書の内部構造には依存しないことを推奨します。

## エンジンモード

| モード | 動作 | 用途 |
| --- | --- | --- |
| `auto` | Sudachi を優先し、利用できなければ PyKakasi にフォールバック | 通常の利用 |
| `sudachi` | Sudachi と辞書を必須にする | 本番および CI の厳格な検査 |
| `pykakasi` | Fugashi/PyKakasi の経路を使用 | 互換性と比較 |

厳格モードを初期化できない場合は `EngineUnavailableError` が発生し、指定されたモードを
黙って変更することはありません。

## インストール

GitHub のリリースタグからインストールします。

```bash
python3 -m pip install \
  "japanese-reading-core @ git+https://github.com/qweihu/japanese-reading-core.git@v0.1.0"
```

ローカル開発の場合：

```bash
git clone https://github.com/qweihu/japanese-reading-core.git
cd japanese-reading-core
python3 -m pip install -e .
```

Python 3.10 以上をサポートし、SudachiPy、`sudachidict-core`、Fugashi、UniDic-lite、
PyKakasi を読み取りアダプターとして利用します。

## 設計原則

### 文字より先に文脈を理解する

日本語の読みは語境界、活用、文脈に依存します。形態素解析器が文脈上の単位を判断した後、
利用側が送り仮名との表示上の対応を決めます。

### 原文保持を不変条件にする

空白、句読点、ラテン文字、かな、改行、未知の断片を追跡できるようにします。すべての
`orig` を連結すれば、入力が完全に保持されているか検査できます。

### 証拠と描画を分離する

辞書データは上位アプリケーションで候補や監査の証拠として利用できますが、本パッケージが
孤立した辞書検索で主エンジンの結果を黙って上書きすることはありません。

### 小さなインターフェースを保つ

下位 NLP ライブラリの内部オブジェクトではなく、アダプターと正規化された値を公開します。
これにより統合テストがしやすくなり、エンジン更新による挙動の変化も追跡できます。

## 範囲と非目標

本リポジトリは以下を提供しません。

- 日本語言語判定；
- 振り仮名や HTML の描画；
- 翻訳；
- 歌詞の取得やクリーニング；
- Yomitan/JMdict のデータ配布；
- ユーザーデータ保存やリモートサービス。

これらは読み取り契約を変更せず、別のレイヤーとして実装できます。

## テストと再現性

```bash
python3 -m unittest discover -s tests -v
python3 -m build --wheel
```

文脈読み、PyKakasi の選択、原文の再構成、空白と改行の保持、かなの正規化、不正なエンジン
指定を検証します。読みの挙動はバージョンで管理し、利用側は未監査の移動ブランチではなく
リリースタグまたは範囲を限定したバージョンに依存してください。

## ロードマップ

- レビュー済みの文脈読みテストケースを拡充する；
- 曖昧な読みや利用不能なエンジンの診断情報を追加する；
- コア API と結合しない任意の辞書証拠を評価する；
- 安定版リリースと互換性ノートを整備する；
- 独立して管理された日本語コーパスで精度を評価する。

## ライセンス

MIT License。詳しくは [LICENSE](LICENSE) を参照してください。
