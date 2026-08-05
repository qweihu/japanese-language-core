# Nihongo Core（japanese-language-core）

Nihongo Core 是 [**Bunomi**](https://github.com/qweihu/Bunomi) 与
[**Utayomi**](https://github.com/qweihu/Utayomi) 共享的日语语言能力核心：
上下文读音、假名/罗马音、读音-汉字对齐、活用形还原、逐句翻译契约、
词典元数据、语法型检测与导出契约。

核心设计原则是**确定性契约 + 可选重依赖**：裸装零依赖，能力按需引入。

---

## 为什么要统一成一个核心？

此前读音在 `japanese-reading-core`，翻译则是每个应用各自临时实现的 Agent
能力。Bunomi 和 Utayomi 需要同一套读音与翻译构件，于是两个能力收进同一个
带版本号的包：

- **读音**是确定性引擎问题：分词、上下文读音、假名归一；
- **翻译**是 LLM 能力：core 定义契约、逐语言约定与校验，实际翻译由
  Agent 或用户自带的模型端点执行。

两个能力共享稳定的交换格式：行结构 + `<ruby>…<rt>…</rt></ruby>` 标记。
core 保证结构不被破坏，应用层负责自己的排版。

## 能力总览

| 模块 | 内容 |
| --- | --- |
| [`reading`](#读音reading) | 保原文分词 + 上下文读音（Sudachi 优先、PyKakasi 回退），`ReadingToken` 契约 |
| [`reading.kana`](#假名与罗马音) | 假名转换、全半角归一、Hepburn 罗马音（纯标准库） |
| [`reading.alignment`](#读音-汉字对齐) | 读音分配到汉字（furigana 对齐） |
| [`reading.deinflect`](#活用形还原) | 变形 → 辞書形 候选（尽力而为） |
| [`translation`](#翻译translation) | 逐句契约、校验、语言注册表、术语一致性 |
| [`translation.provider`](#byo-llm-翻译) | Agent 模式（无 API）或 BYO-LLM（任意 OpenAI 兼容端点） |
| [`dictionary`](#词典dictionary) | Yomitan 词典读取（term/kanji/tag/meta bank）+ JLPT 难度分析 |
| [`grammar`](#语法grammar) | 助词与常见语法型检测 |
| [`export`](#导出export) | Anki 笔记契约与中日对照 Markdown 契约 |
| `structure` | ruby/行/占位符通用校验（translation 复用） |

## 安装

需要 Python 3.10+。

```bash
# 仅读音（Sudachi / Fugashi / PyKakasi）
python3 -m pip install "japanese-language-core[reading] @ git+https://github.com/qweihu/japanese-language-core.git@v0.2.0"

# 仅翻译（纯标准库，零依赖）
python3 -m pip install "japanese-language-core[translation] @ git+https://github.com/qweihu/japanese-language-core.git@v0.2.0"

# 全部
python3 -m pip install "japanese-language-core[all] @ git+https://github.com/qweihu/japanese-language-core.git@v0.2.0"
```

本地开发：

```bash
git clone https://github.com/qweihu/japanese-language-core.git
cd japanese-language-core
python3 -m pip install -e ".[reading]"
```

顶层包不 import 任何重模块；重适配器在 `reading` 子模块内延迟加载，
所以纯翻译安装保持轻量。

## 读音（reading）

引擎在保留每个字符、空白与换行的前提下分词，并附加归一化读音：

```python
from japanese_language_core.reading import create_engine, ReadingToken

engine = create_engine("auto")  # "auto" | "sudachi" | "pykakasi"
tokens = tuple(engine.tokens("雨が降り止むまでは帰れない"))

assert "".join(token.orig for token in tokens) == "雨が降り止むまでは帰れない"
for token in tokens:
    print(token.orig, token.hira, token.hepburn)
```

`ReadingToken` 字段：

| 字段 | 含义 |
| --- | --- |
| `orig` | 原文表面片段；所有片段拼接后等于输入 |
| `hira` | 归一化的平假名读音（无读音时为空串） |
| `hepburn` | 可选 Hepburn 罗马音 |

### 引擎模式

| 模式 | 行为 | 适用 |
| --- | --- | --- |
| `auto` | 优先 Sudachi，不可用时回退 PyKakasi | 常规应用 |
| `sudachi` | 强制 Sudachi + 词典 | 生产与 CI |
| `pykakasi` | Fugashi/PyKakasi 回退路径 | 兼容与对比 |

严格模式在引擎不可用时抛 `EngineUnavailableError`，不会静默换引擎。
`ReadingEngine` 协议是唯一公共边界，消费方不接触 Sudachi `Morpheme`、
Fugashi tag 对象或词典内部结构。

## 假名与罗马音

纯标准库工具，渲染器与测试常用：

```python
from japanese_language_core.reading import (
    is_kana, is_kanji, is_hiragana, is_katakana,
    to_hiragana, to_katakana, normalize_width, to_romaji,
)

to_hiragana("ニホンゴ")      # "にほんご"
to_katakana("にほんご")      # "ニホンゴ"
to_hiragana("ﾆﾎﾝｺﾞ")        # "にほんご"（半角 + 浊音符号）
to_romaji("しんぶん")        # "shimbun"（Hepburn：ん 在 b/m/p 前读 m）
```

罗马音转换器是务实的 Hepburn 实现（含促音双写与 ん 同化）。
生产级罗马音建议安装 `[reading]` 扩展并使用引擎的 `hepburn` 字段。

## 读音-汉字对齐

把假名读音分配到汉字——ruby 渲染背后的分布问题：

```python
from japanese_language_core.reading import align_reading

pairs = align_reading("食べる", "たべる")
# [("食", "た"), ("べ", "べ"), ("る", "る")]

pairs = align_reading("日本語", "にほんご")
# [("日本語", "にほんご")]
```

词中假名逐字匹配；每段汉字贪婪消费假名，直到遇到下一个假名或读完。
歧义复合词（如 好き嫌い）可能需要词典级对齐，`dictionary` 元数据可提供
线索；这是确定性回退方案。

## 活用形还原

尽力而为的变形 → 辞書形 候选：

```python
from japanese_language_core.reading import deinflect

for candidate in deinflect("食べていました"):
    print(candidate.word, candidate.reason)
# 食べる, "te-form + progressive + polite past"
```

规则引擎剥离常见后缀（ます/ない/た/て/ている/すぎる/やすい/…），重新套用
辞書形词尾；结尾有歧义时输出多个候选（行った → 行く/行つ/行る/行う）。
有词典的调用方可以用 `dictionary.lookup_terms` 过滤候选。

## 翻译（translation）

翻译是 LLM 能力。core 提供**契约**、**校验**、**语言注册表**与**执行器**，
不内置模型、不打包密钥。

### 数据模型

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

### 结构校验

```python
from japanese_language_core.translation import validate_translation

errors, warnings = validate_translation(
    source_lines=["明日は晴れる。", "一緒に歩こう。"],
    translation_lines=["明天会放晴。", "一起走吧。"],
    paired=True,
)
```

检查项：

- 行数配对（非空行数一致、空行分组保留）；
- ruby/HTML 卫生（标签闭合、只允许 `ruby`/`rt`）；
- 原文保真（剥离 ruby 后还原原文）；
- 占位符保留（`♪`、`[Chorus]`、`（…）`、`【…】`）；
- 假名漏译警告（翻译行残留平假名/片假名）；
- 术语一致性（可选 `TermGlossary`）。

CLI：

```bash
python3 -m japanese_language_core.translation validate \
  --source source.txt --translation translation.txt --paired
```

退出码：`0` 通过、`1` 结构错误、`3` 仅警告（`--strict-warnings`）。

### 语言注册表

```python
from japanese_language_core.translation import LanguageRegistry

registry = LanguageRegistry.from_package()
registry.default()       # LanguageInfo(code="zh-CN", ...)
registry.codes()         # ["en", "zh-CN"]
```

机器可读注册表（`translation/data/languages.json`）驱动 BYO-LLM prompt；
Agent 使用的人读约定在 `japanese-translation` 技能的 `references/` 中。

### 术语一致性

```python
from japanese_language_core.translation import TermGlossary, GlossaryEntry

glossary = TermGlossary()
glossary.add(GlossaryEntry(source="明日", preferred="明天"))

errors, warnings = validate_translation(
    ["明日は晴れる。"], ["明天会放晴。"], paired=True, glossary=glossary,
)
```

当源词未翻译、未使用首选译文、或同一词在不同行译文不一致时告警。

### 执行器

两种执行模式，同一套校验：

| 执行器 | 模式 | 说明 |
| --- | --- | --- |
| `AgentTranslator` | Agent | 契约标记：由 Agent 按技能约定翻译，不发起网络调用 |
| `OpenAICompatibleTranslator` | BYO-LLM | 调用你配置的任意 OpenAI Chat Completions 兼容端点 |

## BYO-LLM 翻译

自带端点——Ollama、vLLM、LM Studio、OpenAI 兼容网关均可：

```python
from japanese_language_core.translation import (
    OpenAICompatibleTranslator, TranslationUnit,
)

translator = OpenAICompatibleTranslator(
    base_url="http://localhost:11434/v1",  # 自动追加 /chat/completions
    model="llama3.1",
    api_key=None,          # 或环境变量 JAPANESE_LANGUAGE_CORE_API_KEY
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

CLI：

```bash
export JAPANESE_LANGUAGE_CORE_API_KEY=sk-...
python3 -m japanese_language_core.translation translate \
  --source source.txt --target-lang zh-CN \
  --base-url https://api.example.com/v1 --model my-model
```

行为说明：

- system prompt 由注册语言的约定自动构建；
- 输出按源行数解析回逐行翻译；
- 行数不足抛 `TranslateError`（不会静默截断）；
- 结果走同一套 `validate_translation` 校验。

测试时可注入 `transport` 可调用对象（默认是标准库 `urllib` 实现）：

```python
def fake_transport(url, headers, payload):
    return '{"choices": [{"message": {"content": "1. 明天会放晴。"}}]}'

translator = OpenAICompatibleTranslator(
    base_url="https://example.test/v1", model="test",
    transport=fake_transport,
)
```

## 词典（dictionary）

读取开放的 **Yomitan 词典格式**（zip 包），即可接入社区现有词典生态
（JMdict 系、JPDB/KANJIDIC 频率、声调等）：

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

支持的 bank：

| Bank | 内容 |
| --- | --- |
| `term_bank_*.json` | 词条、读音、释义、标签、规则、score、sequence |
| `term_meta_bank_*.json` | 频率（`freq`）与声调（`pitch`） |
| `kanji_bank_*.json` | 音读/训读、释义、标签、统计（grade/strokes/…） |
| `kanji_meta_bank_*.json` | 汉字频率 |
| `tag_bank_*.json` | 标签定义（词性、等级、分类） |
| `index.json` | 词典元数据（title、format_version、attribution） |

### JLPT 难度分析

```python
from japanese_language_core.dictionary import analyze_difficulty

profile = analyze_difficulty("日本語を勉強する。", dictionary)
print(profile.level_counts())  # 例如 {"n5": 2, "unknown": 1}
print(profile.score)           # 0..1，越大越简单
```

传入读音引擎可用形态学分词替代最长匹配回退：

```python
from japanese_language_core.reading import create_engine

profile = analyze_difficulty("日本語を勉強する。", dictionary, engine=create_engine("auto"))
```

## 语法（grammar）

确定性的表层检测——不替代形态学分析，但快速可测：

```python
from japanese_language_core.grammar import find_particles, find_grammar

particles = find_particles("私は東京へ行きます。")
print([m.particle for m in particles])   # ["は", "へ"]

matches = find_grammar("食べているところです。")
print([m.name for m in matches])         # ["te-iru", "seeming"]
```

助词检测把假名串视为已知助词或以助词结尾时识别。语法型包括て形结构
（ている/ておく/てしまう/てもいい/てはいけない/てほしい）、义务
（なければならない/ないといけない）、可能（ことができる）、条件
（たら/れば）等。

## 导出（export）

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

`anki_connect_payload(...)` 生成 AnkiConnect `addNote` 请求结构；
实际 API 调用留在应用层。

### 中日对照 Markdown

```python
from japanese_language_core.export import build_paired_markdown

markdown = build_paired_markdown(result.units)
```

输出：每单元"源行 + 翻译行 + 空行"，是 Bunomi 与简单导出的排版契约；
Utayomi 仍拥有最终歌词排版。

## CLI 参考

```text
python -m japanese_language_core.translation validate
    --source FILE | -       源日语文本
    --translation FILE | -  翻译文本
    --paired                要求非空行数一致
    --no-kana-warn          关闭假名漏译警告
    --glossary FILE         JSON 术语表（{"entries": [...]}）
    --strict-warnings       有警告时退出码 3

python -m japanese_language_core.translation translate
    --source FILE | -       源日语文本
    --target-lang CODE      默认 zh-CN
    --base-url URL          OpenAI 兼容端点
    --model NAME            模型标识
    --api-key KEY           可选；环境变量 JAPANESE_LANGUAGE_CORE_API_KEY
    --output FILE           写入翻译文件

python -m japanese_language_core.translation languages
    [--registry FILE]       列出已注册目标语言
```

## 兼容性

`japanese_reading_core` 是迁移期兼容垫片，旧 import 继续可用：

```python
from japanese_reading_core import create_engine  # 旧写法，仍可用
from japanese_language_core.reading import create_engine  # 新代码
```

新代码请使用 `japanese_language_core.reading`；过渡期结束后移除垫片。

## 设计原则

- **能力按子模块按需引入**，顶层不 import 重模块；
- **契约小而可测**：`ReadingToken`、`TranslationUnit`、词典模型都是
  小接口 + 契约测试；
- **翻译是 LLM 能力**：core 只定义契约/约定/校验，执行者是 Agent
  （技能模式）或用户自带端点（BYO-LLM）；
- **词典是证据不是替代**：丰富与审计结果，不静默覆盖主引擎；
- **不包含产品层**：歌词清洗、排版、UI、用户数据留在 Bunomi/Utayomi。

## 边界（非目标）

本仓库明确不包含：

- 翻译引擎本体（翻译是 LLM 能力）；
- 歌词抓取/清洗（Utayomi 产品层）；
- furigana/HTML 渲染器与语言检测器；
- 用户数据存储、云服务与 API 密钥；
- Yomitan/JMdict 数据分发（消费格式，不打包数据）。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

测试覆盖原文保真、上下文读音、假名/罗马音、读音对齐、活用形还原、
翻译校验、provider 传输、Yomitan 解析、JLPT 分析、语法检测与导出往返。

## Roadmap

- 扩充审核过的上下文读音用例；
- 通过现有 Yomitan 读取器接入社区频率/JLPT/声调词典；
- 术语表文件成为技能的一等资产；
- 发布稳定版本与兼容性说明；
- 在独立维护的日语语料上度量读音准确率。

## 许可

MIT。本项目基于开源组件（Sudachi、Fugashi、PyKakasi、UniDic、Yomitan
词典格式）构建；各自许可证归各自项目所有。
