<div align="center">

# japanese-reading-core

**一个保持原文、理解上下文的 Python 日语读音引擎。**

日语不能简单地逐字读取。本项目结合形态素分析、上下文读音、假名规范化和稳定的 token
接口，为振假名、学习工具、搜索和无障碍应用提供可复用的读音基础能力。

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md)

</div>

## 项目概览

`japanese-reading-core` 将日文转换为保持原文的 `ReadingToken`。每个 token 包含原文片段、
平假名读音和可选的 Hepburn 罗马音。

项目只关注“日语应该怎么读”这一层：

- 将日文切分为有上下文意义的词法单元；
- 从上下文形态素引擎获取读音；
- 首选引擎不可用时提供确定性的回退路径；
- 保留输入中的字符、空格、标点和换行；
- 用小而稳定的接口让应用能够测试和版本化。

它不依赖大模型猜读音，也不强迫调用方使用某一种 HTML 或 Markdown 渲染方式。

## 处理流程

```text
日文输入
  ↓
保留行结构与空白
  ↓
上下文词法分析
  ↓
读音规范化
  ↓
ReadingToken(orig, hira, hepburn)
  ↓
由应用决定如何渲染或分析
```

例如，`降り止む` 会被作为一个上下文词法单元处理，得到 `ふりやむ`。调用方再根据自己的
输出格式决定如何将这个读音和汉字、送假名对齐。

## 核心接口

```python
from japanese_reading_core import ReadingToken, create_engine

engine = create_engine("auto")
tokens = tuple(engine.tokens("雨が降り止むまでは帰れない"))

assert all(isinstance(token, ReadingToken) for token in tokens)
assert "".join(token.orig for token in tokens) == "雨が降り止むまでは帰れない"
```

| 字段 | 含义 |
| --- | --- |
| `orig` | 原文表面片段；所有片段拼接后必须还原输入 |
| `hira` | 规范化后的平假名读音；没有读音时为空字符串 |
| `hepburn` | 可选的 Hepburn 罗马音 |

调用方应依赖 `ReadingEngine.tokens(text)` 和 `ReadingToken`，而不应依赖 Sudachi 的
`Morpheme`、Fugashi tag 对象或第三方词典内部结构。

## 引擎模式

| 模式 | 行为 | 适用场景 |
| --- | --- | --- |
| `auto` | 优先 Sudachi，不可用时回退 PyKakasi | 普通应用使用 |
| `sudachi` | 严格要求 Sudachi 和其词典 | 生产与 CI 检查 |
| `pykakasi` | 使用 Fugashi/PyKakasi 路径 | 兼容和对比测试 |

严格模式初始化失败时会抛出 `EngineUnavailableError`，不会静默改变调用方指定的模式。

## 安装

从 GitHub 的当前版本标签安装：

```bash
python3 -m pip install \
  "japanese-reading-core @ git+https://github.com/qweihu/japanese-reading-core.git@v0.1.0"
```

本地开发：

```bash
git clone https://github.com/qweihu/japanese-reading-core.git
cd japanese-reading-core
python3 -m pip install -e .
```

当前支持 Python 3.10 及以上版本，使用 SudachiPy、`sudachidict-core`、Fugashi、UniDic-lite
和 PyKakasi 作为读音适配器。

## 设计原则

### 先理解上下文，再处理字符

日语读音依赖词法边界、活用和上下文。引擎先让形态素分析器判断上下文词，再由应用决定
如何做视觉上的送假名对齐。

### 原文保真是不变量

空格、标点、拉丁字母、假名、换行和未知片段都必须可追溯。调用方可以通过拼接所有
`orig` 字段检查结果是否完整。

### 证据和渲染分离

更高层的应用可以把词典作为候选或审计证据，但本包不会用孤立的词典查找静默覆盖主引擎
结果，也不会携带用户数据、词典缓存或应用策略。

### 小接口更容易审计

本包暴露的是适配器和规范化后的值，而不是底层 NLP 库的内部对象图。这样可以让集成更容易
测试，并让引擎升级通过版本化的行为变化显现出来。

## 范围与非目标

本仓库不是：

- 日语语言检测器；
- 振假名或 HTML 渲染器；
- 翻译系统；
- 歌词抓取或清洗工具；
- Yomitan/JMdict 数据发行包；
- 用户数据存储或远程服务。

这些能力可以由独立层实现，而不改变核心读音接口。

## 测试与复现

```bash
python3 -m unittest discover -s tests -v
python3 -m build --wheel
```

测试覆盖上下文读音、PyKakasi 选择、原文重建、空白与换行保留、假名规范化和非法引擎处理。
读音行为会随版本记录，应用应依赖版本标签或有边界的版本范围，而不是未经审计的移动分支。

## 路线图

- 扩充经过审阅的上下文读音样本；
- 增加歧义读音和不可用引擎的诊断信息；
- 评估可选词典证据，但不耦合核心 API；
- 发布稳定版本和兼容性说明；
- 使用独立维护的日语语料进行准确性评估。

## 许可证

MIT License，详见 [LICENSE](LICENSE)。
