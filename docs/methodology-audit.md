# japanese-language-core 方法论审计报告

更新日期：2026-08-05

## 1. 审计范围与方法

对 japanese-language-core 的读音、对齐、活用形、翻译契约、BYO-LLM、
词典、语法、导出、包工程与 Agent 集成做一轮完整审计。对照基线：

- 论文：Sudachi（Takaoka et al., LREC 2018）；COMET（Rei et al., EMNLP 2020）；
  MeCab/UniDic 形态学分析传统。
- 开源项目：Yomitan/Yomichan（词典格式、MultiLanguageTransformer 活用形还原、
  读音分布）；japanese-furigana-normalize（读音-汉字对齐）；jamdict（JMdict
  词典与活用形，MIT）；pandas/narwhals 等（extras 可选依赖模式）；
  GitHub Actions 矩阵测试；pytest/hypothesis 测试生态。
- 工程实践：PEP 508 extras、pyproject（PEP 621）、语义化版本、虚拟环境隔离、
  覆盖率与静态检查、CI 门禁、发布流程。

审计方法：读代码 + 对照基线 + 用真实语料抽查 + 评估可维护性与可审计性。
所有结论按 P0（必须修）/ P1（应该修）/ P2（建议修）分级。

## 2. 结论摘要

总体判断：**架构方向正确，细节有若干明显瑕疵。** 三个最值得肯定、也是
符合业界做法的设计：

1. **契约驱动**：`ReadingToken` / `TranslationUnit` / 词典模型都是小而稳定的
   接口，这是 Sudachi、Yomitan 等项目的共同哲学；
2. **翻译"契约 + 校验"而非"翻译引擎"**：在 LLM 时代，模型负责生成、代码负责
   约束与验证，这正是当前工业界 LLM 翻译管线（生成 → 校验 → 修正）的分工；
3. **可选重依赖（extras）**：读音与翻译解耦安装，符合 pandas/narwhals 等
   项目的标准做法。

需要修的关键问题：

- P0：缺基准集与 CI，无法证明"读音正确率、校验召回率"在演进中不回退；
- P0：furigana 对齐是贪心算法，对歧义复合词（好き嫌い、おねがいいたします）
  会错分——业界用词典内读音分布或专门的归一化算法解决；
- P1：活用形规则覆盖远小于 Yomitan MultiLanguageTransformer，且不接词典过滤，
  候选噪音大；
- P1：翻译校验只做结构启发式（行数/ruby/假名），没有语义或术语级验证；
- P1：BYO-LLM 无重试、无长文分批，max_tokens 固定，长文本有截断风险；
- P1：Agent 使用方式未统一为 CLI-first；
- P1：Yomitan meta bank 每次查询线性扫描，大词典会退化；
- P2：语法检测用正则而非形态学 PoS，存在同形误报；
- P2：包工程缺 CI/覆盖率/静态检查/发布流程；PyKakasi GPL 声明需保留。

## 3. 逐模块审计

### 3.1 读音引擎（reading/engine.py）

优点：

- 原文保真是硬契约（`orig` 拼接 == 输入），与 Sudachi 的分词一致性要求一致；
- 上下文读音（Sudachi SplitMode.C）优于逐字符猜测，符合 Sudachi 论文与
  Yomitan 的实践；
- `auto` 降级、`sudachi`/`pykakasi` 严格模式的语义清晰，严格模式不静默换引擎
  （符合 EngineUnavailableError 的契约设计）。

瑕疵：

- P1：`auto` 降级到 PyKakasi 时无任何可观测信号（日志/返回元数据），生产环境
  可能静默用低质量引擎输出。Yomitan 的做法是显式 `--engine shared` +
  stderr 警告；建议至少提供 `engine.name` 供调用方记录，并在 CLI/技能层输出
  降级提示；
- P1：Sudachi 词典版本约束过宽（`sudachidict-core>=20230110`），读音行为随
  词典更新漂移。建议锁定到已验证的具体版本区间并在发行说明记录；
- P2：`to_romaji` 是简化 Hepburn（促音、ん 同化已处理，但 ぢ/づ、長音符号、
  外来语表记等边界不全）；文档已声明这是务实实现，可接受，但应在发布说明
  中标注与 PyKakasi 的差异。

### 3.2 读音-汉字对齐（reading/alignment.py）

瑕疵（本模块是当前正确性风险最高点）：

- P0：贪心"下一个假名即停"无法处理歧义分布，例如 好き嫌い（すき|きらい vs
  す|きき|らい）、おねがいいたします（重复假名）。Yomitan 官方承认该问题
  （issue #505），解决方式是让词典自带读音分布；社区工具
  japanese-furigana-normalize 用"kanji 对齐 + 阅读归一化"算法处理同一问题；
- P1：没有与词典联动的接口。正确做法是三级策略：词典内分布（若词条带
  furigana/reading 对齐）→ 通用对齐算法 → 明确标记无法对齐；
- P1：没有单元级 golden 测试覆盖歧义样例。

建议：P0 增加歧义样例测试并写明已知限制；P1 实现"词典优先 + 算法回退"的
组合策略，算法本身参考 japanese-furigana-normalize 的思路（阅读归一化 +
汉字边界约束）。

### 3.3 活用形还原（reading/deinflect.py）

优点：

- 规则表 + 候选集 + 规则链 reason 的结构是对的，与 Yomitan
  MultiLanguageTransformer（suffixInflection + 抽象变形）思路一致；
- 明确声明"best-effort"，并由词典过滤候选的设计正确。

瑕疵：

- P1：规则覆盖远小于业界：缺 ちゃう/じゃう（てしまう 口语缩约）、とく
  （ておく 缩约）、てる/てた（口语体）、たがる、てください、たほうがいい、
  そうです 等高频形；音便候选（行った → 行く）生成了但噪音候选过多；
- P1：不接词典过滤，单独使用返回大量无效候选；README 有说明，但没有 API
  层封装（如 `deinflect_with_dictionary(word, dict)`）；
- P2：Yomitan 的规则是 AGPL，不能直接移植代码；jamdict 是 MIT，但其
  deinflector 面向 JMdict 查询，可以作为"规则数据思路"的参考。

### 3.4 翻译契约与校验（translation/）

优点：

- 行配对、ruby/HTML 卫生、原文保真、占位符、假名漏译五类结构检查，比"裸
  prompt 翻译"严格得多，是正确方向；
- 校验与执行解耦（validate_translation 独立于 provider），任何执行者产出
  都走同一契约，这符合 LLM 应用"生成不可信、验证要确定"的工程原则。

瑕疵：

- P1：校验是结构启发式，无语义层。业界 MT 评估用 BLEU/sacrebleu、COMET 或
  LLM-as-judge；对歌词/学习文本，低成本替代是"术语表命中检查 + 回译/自一致
  抽查"；当前只有术语表结构检查；
- P1：无 few-shot 示例，system prompt 只有规则文本。GPT-3 以来的实践表明
  few-shot 显著提升风格稳定性；建议把示例放进 languages.json 或语言约定；
- P1：假名漏译警告对 zh-CN 专名会误报（默认开），需要每语言策略更细
  （已提供 kana_warning 开关，但缺"专名白名单"）；
- P2：占位符检查只做"出现与否"，未做"位置/数量"校验。

### 3.5 BYO-LLM 执行器（translation/provider.py）

优点：

- 不内置供应商、api key 走环境变量/注入，transport 可替换便于测试，这是
  当前开源 LLM 客户端（OpenAI SDK、LiteLLM）的共同模式；
- 输出行数不足即抛错，不静默截断。

瑕疵：

- P1：无重试/退避与超时配置暴露（timeout 固定默认 60s，urllib 层无重试）；
- P1：max_tokens 固定 2048，长文本（歌词几十句）会截断；应支持按源行数
  自动分批（chunk），或允许覆盖 max_tokens；
- P1：无流式；对慢端点长文本体验差（Agent 场景可接受，但应文档说明）；
- P2：对"翻译不可信输入"的 prompt injection 没有说明（用户粘贴的网页/歌词
  可能含恶意指令）；应在文档中提示"把输入当数据、约束在 system prompt"。

### 3.6 词典层与 JLPT（dictionary/）

优点：

- 对齐 Yomitan 开放格式是正确选择——社区词典生态（JMdict 系、JPDB、声调）
  都以此分发，避免自造格式；
- TermEntry/KanjiEntry/FrequencyTag/PitchAccent 模型覆盖了主要使用场景。

瑕疵：

- P1：`validate()` 只检查 term bank 是否存在，远弱于 Yomitan 官方 JSON
  schema（term/kanji/tag/meta 各有 v3 schema）；应至少校验必需文件、行数与
  字段类型；
- P1：meta bank 每次 lookup 都线性扫描（`_term_meta`），大词典（百万词条）
  会退化到不可用；应建 `expression → meta` 索引；
- P1：频率/声调数据格式存在社区变体（freq 可为 int/dict，pitch 可为
  `"n/a"`/list/dict），当前只覆盖一部分，遇未知格式会静默丢数据；
- P2：JLPT 来自 tag 是近似（JLPT 官方并无完整词表，社区用 JPDB/BCCWJ 频度
  或 tag 近似）；README 未声明这个近似，建议明确"难度分析是近似值"；
- P2：无词典 lookup 的分词接口（`analyze_difficulty` 的贪婪最长匹配对
  未登录词会退化为单字），可接受但应文档说明。

### 3.7 语法检测（grammar/）

优点：轻量、确定、零依赖，适合快速标注。

瑕疵：

- P2：表层正则无法处理同形歧义（例えば「やすい」在「安い」「食べやすい」；
  「たい」在「暖たい」）；业界做法是用形态学 PoS（Sudachi/MeCab/Kuromoji）
  后接规则。建议 P2 提供"token + PoS"输入接口，把正则作为无引擎时的回退；
- P2：助词检测把「ください」等误判为助词「し」（假名串后缀匹配），需要
  PoS 才能根治。

### 3.8 导出契约（export/）

优点：Anki 字段模型与 TSV/AnkiConnect payload 分离，符合"core 定义契约、
应用层调 API"的边界。

瑕疵：

- P2：Anki 字段模型默认按 jp-mining 模板假设（Expression/Reading/…）；
  应允许完全自定义 field_map（已支持），README 应给出自定义示例；
- P2：`build_paired_markdown` 与产品层排版有重叠，应明确"参考实现"定位
  （现 README 已说明 Utayomi 拥有最终排版——但 README 已移除应用提及，
  需改为"消费方可自行覆盖"）。

### 3.9 包工程与发布（packaging / CI / 测试）

优点：pyproject（PEP 621）、extras 分离、契约测试、README 详实。

瑕疵：

- P0：无 CI。业界标配是 GitHub Actions 在 Python 3.10–3.13 矩阵上跑测试 +
  覆盖率门禁；没有 CI，改动很容易在"我机器上能跑"与"别人机器上不能跑"
  之间漂移；
- P1：unittest 而非 pytest；pytest 的参数化/插件/覆盖率（pytest-cov）
  生态更适合持续扩大的契约测试；
- P1：无覆盖率与静态检查（ruff/mypy），README 声明"契约可测"但没有数字
  支撑；
- P1：无基准集：读音没有 golden 语料（当前 6 个 fixture 太少），翻译校验
  没有正/负例集；无法度量"错误率"；
- P1：依赖版本范围过宽（`sudachidict-core>=` 等），应至少加
  `~=`/上限约束并在发行说明锁定已验证版本；
- P1：PyKakasi 为 GPL-3.0，作为运行时依赖合法，但发行时必须保留依赖声明
  与许可证提示（README 已列，需在 PyPI 元数据/打包时保持）；
- P2：无 CHANGELOG/语义化发布流程（当前 tag 即发布）；作为库建议 semver +
  CHANGELOG + PyPI 双通道。

### 3.10 技能与 Agent 集成

结论（也回答"Agent 是否应优先用 CLI"）：

**是，Agent 应优先使用 CLI。** 理由：

1. 确定性：CLI 的行为由代码保证，不依赖模型自我想象；
2. 可审计：错误码（0/1/3）与 stderr 输出结构化，Agent 可据此重试；
3. 省上下文：技能只需给命令，不需要贴整段 API 用法；
4. 一致校验：CLI 与库共用同一实现，不会"技能里手写的逻辑"与库漂移。

Python API 面向"应用集成"（Bunomi/Utayomi 等程序化消费方），技能层面向
"Agent 操作"。当前 japanese-translation 技能已有 validate CLI，但缺：

- P1：顶层 CLI（`python -m japanese_language_core` 或 `nihongo` 命令）把
  reading/validate/translate/languages 收拢，Agent 一个入口拿全能力；
- P1：技能明确"CLI-first、API 次之"的操作顺序与 venv 引导。

### 3.11 方法论总体判断

- 边界划分（core 不含产品层、翻译不混入读音 CLI、词典是证据不是替代）
  是正确的，与 Yomitan/Bunomi 的既有边界一致；
- "一个核心包 + 多能力子模块"在项目早期是合理选择；风险是能力面扩张后
  单包维护负担上升。建议以"每能力至少一个消费方 + 契约测试"为扩展门槛
  （已经这么做了，继续保持）；
- 最大方法论风险是**没有 ground truth**：读音、对齐、难度、校验都没有
  可量化的基准集，导致"看起来对"无法转化为"持续正确"。这是 P0。

## 4. 与业界对照表

| 主题 | 我们 | 业界参考 | 差距 |
| --- | --- | --- | --- |
| 分词/读音 | Sudachi C mode + PyKakasi 回退 | Sudachi（LREC 2018）、MeCab/UniDic | 无版本锁定、降级不可观测 |
| 读音对齐 | 贪心算法 | japanese-furigana-normalize、Yomitan 词典分布 | 歧义复合词错分 |
| 活用形 | 自制规则子集 | Yomitan MultiLanguageTransformer、jamdict | 覆盖不足、不接词典过滤 |
| 翻译校验 | 结构启发式 | COMET/BLEU、LLM-as-judge、术语表 | 无语义层 |
| LLM 客户端 | 自研 urllib transport | OpenAI SDK、LiteLLM | 无重试/分批/流式 |
| 词典格式 | Yomitan zip 读取 | Yomitan 官方 schema | 校验弱、meta 线性扫描 |
| 可选依赖 | extras | pandas/narwhals extras | 一致（无差距） |
| 测试 | unittest 契约测试 | pytest + hypothesis + coverage | 工具链与覆盖不足 |
| CI | 无 | GitHub Actions matrix | 缺 |
| 发布 | git tag | PyPI + twine + semver | 未发布 |

## 5. 行动清单

### P0（必须）

- [ ] 建立读音 golden 基准集（覆盖歧义读音/送假名/长音），跑分纳入 CI；
- [ ] 建立翻译校验正/负例集（通过/漏译/行数/ruby/占位符）；
- [ ] 增加歧义 furigana 对齐样例测试并写明已知限制。

### P1（应该）

- [x] Agent CLI-first：新增顶层 CLI（reading/validate/translate/languages），
  技能明确优先使用 CLI；
- [x] 虚拟环境安装引导写入 README（无 venv 时先创建）；
- [x] 活用形补充高频规则（ちゃう/じゃう/とく/てる/てた/たがる/てください/
  たほうがいい/そうです/ことがある 等）；
- [x] Yomitan meta bank 建索引（去掉线性扫描）；
- [ ] auto 降级可观测：调用方记录 `engine.name`，技能/CLI 提示；
- [ ] 对齐算法"词典优先 + 算法回退"组合；
- [ ] 翻译 few-shot 示例进 languages.json；
- [ ] BYO-LLM 重试 + 长文本分批 + max_tokens 可覆盖；
- [ ] 词典 validate 对齐 Yomitan schema 基本校验；
- [ ] CI（GitHub Actions matrix）+ pytest-cov 门禁。

### P2（建议）

- [ ] LLM-as-judge / 自一致校验作为可选验证器；
- [ ] 术语表自动抽取（从 Yomitan 词条）；
- [ ] 语法检测提供 token+PoS 输入接口；
- [ ] 发布到 PyPI（semver + CHANGELOG + 许可证声明）；
- [ ] 频率/声调格式变体兼容与文档说明；
- [ ] 占位符位置/数量校验。

## 6. 参考来源

- Takaoka et al., *Sudachi: a Japanese Tokenizer for Business*, LREC 2018.
- Rei et al., *COMET: A Neural Framework for MT Evaluation*, EMNLP 2020.
- Yomitan / Yomichan：词典格式文档、MultiLanguageTransformer、
  furigana 分布 issue #505。
- japanese-furigana-normalize（MIT，npm）。
- jamdict（MIT，Python JMdict 生态）。
- pandas / narwhals：optional extras 模式。
- PEP 621 / PEP 508：pyproject 与 extras 规范。
