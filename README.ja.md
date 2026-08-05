# Nihongo Core（japanese-language-core）

Bunomi と Utayomi が共有する日本語処理コア：文脈付き読み、かな/ローマ字、
読み-漢字アライメント、活用形復元、行単位翻訳コントラクト、辞書メタデータ、
文法パターン検出、エクスポート契約。

デフォルトは依存ゼロ。Sudachi/Fugashi/PyKakasi は `[reading]` エクストラで
インストールします。

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
```

翻訳検証：

```bash
python3 -m japanese_language_core.translation validate \
  --source source.txt --translation translation.txt --paired
```

BYO-LLM 翻訳（OpenAI 互換エンドポイントを指定）：

```bash
python3 -m japanese_language_core.translation translate \
  --source source.txt --base-url http://localhost:11434/v1 --model llama3.1
```

## 設計

- 能力はサブモジュール単位でオプトイン。トップレベルは重い import をしない。
- 翻訳自体は LLM 能力：コアは契約・検証・言語レジストリを提供し、
  実行は Agent（スキルモード）かユーザー指定のエンドポイント（BYO-LLM）。
- `japanese_reading_core` は移行期間の互換シム。

## ライセンス

MIT。依存 OSS（Sudachi、Fugashi、PyKakasi、UniDic、Yomitan 辞書形式）の
ライセンスは各プロジェクトに帰属します。
