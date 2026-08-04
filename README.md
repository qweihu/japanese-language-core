# japanese-reading-core

`japanese-reading-core` 是 Bunomi 与 Utayomi 共用的日语词法分词和上下文读音引擎。
它只负责把原文转换为可追溯的 `ReadingToken`，不负责振假名 HTML、歌词清洗、翻译、
Markdown 排版或文件导出。

## 为什么独立成包

- Bunomi 负责普通日语学习文本的检测、Ruby 渲染、校验和安全导出。
- Utayomi 负责歌词清洗、翻译和歌词专用排版。
- 两个应用共享同一套 Sudachi 上下文读音和 PyKakasi 回退逻辑。
- `orig` 原文保真契约由独立测试验证，避免两个应用各自维护一份引擎代码。

## 安装

从 GitHub 安装当前发布标签：

```bash
python3 -m pip install \
  "japanese-reading-core @ git+https://github.com/qweihu/japanese-reading-core.git@v0.1.0"
```

本地开发安装：

```bash
python3 -m pip install -e .
```

## 最小接口

```python
from japanese_reading_core import ReadingToken, create_engine

engine = create_engine("auto")
tokens = tuple(engine.tokens("雨が降り止むまでは帰れない"))

assert all(isinstance(token, ReadingToken) for token in tokens)
assert "".join(token.orig for token in tokens) == "雨が降り止むまでは帰れない"
```

`ReadingToken` 字段：

| 字段 | 含义 |
| --- | --- |
| `orig` | 原文表面片段；所有 token 拼接后必须等于输入 |
| `hira` | 平假名读音；没有读音时为空字符串 |
| `hepburn` | Hepburn 罗马音；没有读音时为空字符串 |

`create_engine()` 支持：

- `auto`：优先使用 Sudachi，依赖不可用时回退 PyKakasi。
- `sudachi`：严格要求 Sudachi 和其词典。
- `pykakasi`：使用 Fugashi 分词和 PyKakasi 转换。

应用层不应依赖 Sudachi 的 `Morpheme`、Fugashi 的 tag 对象或第三方词典对象；应用之间只
通过 `ReadingEngine.tokens(text)` 和 `ReadingToken` 交换结果。

## 设计边界

这个仓库不包含：

- Bunomi 的日语检测、Ruby 输出和导出策略；
- Utayomi 的歌词来源处理、HTML 清洗、翻译和排版；
- Yomitan/JMdict 的缓存文件、用户文本或 API 密钥。

Yomitan 等词典可以在应用层作为候选和审计证据使用，但不能在这里静默覆盖上下文引擎的结果。

## 测试

```bash
python3 -m unittest discover -s tests -v
python3 -m build --wheel
```

测试重点包括：原文 token 拼接、Sudachi 上下文读音、PyKakasi 回退、换行/空白保留和错误边界。

## 版本策略

应用应依赖明确的版本范围或 Git 标签，而不是默认跟随未审计的 `main`：

```text
japanese-reading-core>=0.1.0,<0.2.0
```

每次读音行为发生变化时，应同时更新版本、测试样本和变更说明。
