# Nihongo Core（japanese-language-core）

Bunomi 与 Utayomi 共享的日语语言能力核心：上下文读音、假名/罗马音、
读音-汉字对齐、活用形还原、逐句翻译契约、词典元数据、语法型检测与导出契约。

默认零依赖；重依赖（Sudachi/Fugashi/PyKakasi）只在安装 `[reading]` 扩展时引入。

## 能力

| 模块 | 内容 |
| --- | --- |
| `reading` | 保原文的分词 + 上下文读音（Sudachi 优先、PyKakasi 回退） |
| `reading.kana` | 假名转换、全半角归一、Hepburn 罗马音（纯标准库） |
| `reading.alignment` | 读音分配到汉字（furigana 对齐） |
| `reading.deinflect` | 变形 → 辞書形 候选（尽力而为） |
| `translation` | 逐句翻译契约、结构校验、语言注册表、术语一致性 |
| `translation.provider` | Agent 模式（无 API）或 BYO-LLM（任意 OpenAI 兼容端点） |
| `dictionary` | Yomitan 词典读取（term/kanji/tag/meta bank）+ JLPT 难度分析 |
| `grammar` | 助词与常见语法型的确定性检测 |
| `export` | Anki 笔记契约与中日对照 Markdown 契约 |

## 安装

```bash
python3 -m pip install "japanese-language-core[reading] @ git+https://github.com/qweihu/japanese-language-core.git@v0.2.0"
```

`[translation]` 只需标准库，`[all]` 安装全部。

## 快速上手

```python
from japanese_language_core.reading import create_engine
from japanese_language_core.translation import OpenAICompatibleTranslator, TranslationUnit

engine = create_engine("auto")
tokens = tuple(engine.tokens("雨が降り止むまでは帰れない"))

translator = OpenAICompatibleTranslator(
    base_url="http://localhost:11434/v1", model="llama3.1",
)
result = translator.translate([TranslationUnit("明日は晴れる。")], target_lang="zh-CN")
```

校验 CLI：

```bash
python3 -m japanese_language_core.translation validate \
  --source source.txt --translation translation.txt --paired
```

## 设计原则

- 能力按子模块按需导入，顶层不 import 重模块；
- 契约小而可测（`ReadingToken`、`TranslationUnit`、词典模型）；
- 翻译是 LLM 能力：core 只定义契约/约定/校验，执行者是 Agent（技能模式）
  或用户自带端点（BYO-LLM）；
- `japanese_reading_core` 是迁移期兼容垫片，新代码请用
  `japanese_language_core.reading`。

## 边界

不包含：翻译引擎本体、歌词抓取/清洗（Utayomi 产品层）、渲染器、用户数据、
云服务与 API 密钥。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

## 许可

MIT。依赖的开源组件（Sudachi、Fugashi、PyKakasi、UniDic、Yomitan 词典格式）
各自保留其许可证。
