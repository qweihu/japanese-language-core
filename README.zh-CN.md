# Nihongo Core

**[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md)**

Nihongo Core 是可复用的 Python 日语语言能力库，提供上下文读音、假名与罗马音转换、翻译校验、词典读取、语法检查和导出数据结构。

它是代码库，不是歌词搜索服务、终端应用或 Agent 工作流。具体应用决定如何搜索、如何呈现、使用哪种翻译服务，以及提供哪些具有授权的数据集。


## 能力与成熟度

| 领域 | 能力 | 状态与限制 |
| --- | --- | --- |
| 读音 | 上下文分词、平假名、Hepburn、读音对齐、假名转换、活用还原与生成、句子分割、拍数 | 公开 API，已有应用调用方。测试检查接口契约和原文保留，不代表人工读音准确率。 |
| 翻译 | 逐行数据模型、校验器、语言注册表、术语表检查、可选 OpenAI 兼容客户端 | 公开契约。结构检查不能证明译文语义正确；模型端点和密钥由调用方提供。 |
| 参考数据 | Yomitan 词条与汉字、JMnedict 专名、声调、难度评分、KanjiVG、Tatoeba 例句 | 数据读取器和适配器，多数仍属实验能力。数据由调用方提供，并遵守各自许可。 |
| 组合工具 | 助词和语法型检查、Anki payload、中日对照 Markdown、挖句契约 | 实验性积木；用户流程和网络请求由应用实现。 |

仓库不打包大型词典或例句数据。当前评测限制与读音复核状态见[基准说明](docs/benchmarks.md)和[读音复核表](docs/reading-review-sheet.md)。

## 安装

需要 Python 3.10+。基础包没有运行时依赖。

| 安装项 | 内容 |
| --- | --- |
| <code>japanese-language-core[reading]</code> | SudachiPy 与 SudachiDict Core，上下文读音 |
| <code>japanese-language-core[translation]</code> | 翻译契约与校验器，仅使用标准库 |
| <code>japanese-language-core[all]</code> | 默认读音依赖 |
| <code>japanese-language-core[pykakasi]</code> | 可选对照引擎；Fugashi/PyKakasi 依赖链含 GPL-3.0 |

~~~bash
python3 -m venv .venv
source .venv/bin/activate

# 读音能力
python -m pip install "japanese-language-core[reading] @ git+https://github.com/qweihu/japanese-language-core.git@v0.4.0"

# 或仅安装翻译契约
python -m pip install "japanese-language-core[translation] @ git+https://github.com/qweihu/japanese-language-core.git@v0.4.0"
~~~

本地开发：

~~~bash
git clone https://github.com/qweihu/japanese-language-core.git
cd japanese-language-core
python3 -m pip install -e ".[reading]"
~~~

## 快速上手：读音

~~~python
from japanese_language_core.reading import create_engine

engine = create_engine("auto")
tokens = tuple(engine.tokens("雨が降り止むまでは帰れない"))

for token in tokens:
    print(token.orig, token.hira, token.hepburn)

assert "".join(token.orig for token in tokens) == "雨が降り止むまでは帰れない"
~~~

token 保留原文并补充读音，例如：<code>雨 → あめ</code>、
<code>降り止む → ふりやむ</code>、<code>帰れ → かえれ</code>。空格和换行也会保留。

<p align="center"><img src="screenshot/zh/reading.png" alt="分词表列出原文、平假名和罗马音" width="820"><br><sub>读音示例 · 词语片段按顺序还原原句，并保留各自读音。</sub></p>

## 读音细节

- <code>create_engine("auto")</code> 优先使用 Sudachi。只有安装了可选 PyKakasi 扩展时才会走该回退路径；否则读音引擎不可用时会报错。
- <code>ReadingToken.orig</code> 按顺序拼接后可逐字还原输入；<code>hira</code> 与 <code>hepburn</code> 分别提供平假名和罗马音。Sudachi 路径还可带形态学信息。
- 假名转换与 Hepburn 罗马音转换不依赖读音扩展。

<p align="center"><img src="screenshot/zh/kana.png" alt="片假名转换为平假名和 Hepburn 罗马音" width="820"><br><sub>假名转换 · 同一输入展示两种假名与罗马音结果。</sub></p>

<p align="center"><img src="screenshot/zh/inflection.png" alt="日语动词形态分析与常见活用生成" width="820"><br><sub>活用示例 · 分析输入词形，并生成常见变形。</sub></p>

读音不保证人名、歌词、方言或多音汉字在所有上下文中都正确。当前复核表只是少量流程检查，不是准确率分数，也不是人工审校的基准集。

## 翻译契约

Core 不内置翻译模型。它可以把逐行单元交给调用方配置的 OpenAI 兼容服务，也可以让 Agent 为同一数据契约提供译文。

校验器可以检查：

- <code>paired=True</code> 时非空行是否一一对应；
- Ruby 标记是否合法，以及去除标记后原文是否一致；
- <code>♪</code>、<code>[Chorus]</code>、括号备注等占位符是否保留；
- 译文中是否残留日语假名；
- 可选的术语表一致性。

行数或结构错误会作为错误返回。译文残留假名默认是警告；开启严格警告后会返回非零状态。校验通过只表示结构符合约定，不代表译文准确、自然或忠实于歌曲。

<p align="center"><img src="screenshot/zh/translation.png" alt="一组有效译文和一条假名残留警告" width="820"><br><sub>翻译校验 · 结构通过，同时指出译文残留的日语假名。</sub></p>

要使用可选客户端，请在你的应用中提供服务端点、模型和密钥。Core 不发放凭据，也不替调用方选择目标语言。

## 参考数据与实验模块

这些模块是可复用组件，不是开箱即用的产品。数据获取、授权、缓存、用户界面和产品决策由使用它们的应用负责。

### 词典与例句读取器

Yomitan 词典读取器可读取读音、释义、标签、频率、声调和 JLPT 元数据；JMnedict 支持专名查询；KanjiVG 读取笔顺数据。例句读取器处理 Tatoeba 句对；数据需单独提供，许可证为 CC BY 2.0。

<p align="center"><img src="screenshot/zh/dictionary.png" alt="包含读音与元数据的 Yomitan 词条" width="820"><br><sub>词典读取 · 从调用方提供的数据中读取词条字段。</sub></p>

<p align="center"><img src="screenshot/zh/sentences.png" alt="一条 Tatoeba 日语例句及其对应译文" width="820"><br><sub>例句读取 · 原文与提供的译文保持配对。</sub></p>

### 语法与导出

语法工具执行确定性的助词和模式检查，不是完整语法分析器。导出模型可以生成 Anki TSV、AnkiConnect payload 和逐句对照 Markdown，但不会联网操作 Anki，也不管理学习者的卡片集合。

<p align="center"><img src="screenshot/zh/grammar.png" alt="针对助词和语法型的定向检查" width="820"><br><sub>语法检查 · 报告指定模式，不声称完整解析句子。</sub></p>

<p align="center"><img src="screenshot/zh/export.png" alt="Anki TSV 字段和逐句对照文本示例" width="820"><br><sub>导出数据 · 具体行数据可交给调用方使用。</sub></p>

## 命令行

<code>nihongo</code> 命令和 <code>python -m japanese_language_core</code> 提供确定性操作。翻译校验和翻译工具也有独立模块入口。

~~~bash
nihongo --help
python -m japanese_language_core.translation validate --source source.txt --translation translation.txt --paired
python -m japanese_language_core.translation languages
~~~

<p align="center"><img src="screenshot/zh/cli.png" alt="CLI 校验结果和语言列表" width="820"><br><sub>CLI 输出 · 校验返回通过状态及警告数量。</sub></p>

## 开发与评测

~~~bash
python3 -m pip install -e ".[all]"
python3 -m pytest -q
~~~

测试覆盖 API 契约、序列化、原文保留和确定性行为，不衡量读音准确率或翻译质量。发布基准结论前，应使用人工复核的数据集，并注明引擎与词典版本。

## 许可证

MIT。可选依赖和外部数据集可能采用不同许可证；重新分发前请分别核对。
