# 基准集方案（benchmarks）

创建时间：2026-08-05 12:45:37 +08:00
最近更新：2026-10-10 18:03:41 +08:00
状态：进行中
原文档记录的更新日期：2026-08-05

## 原则

优先采用公开材料并保证许可合规；样本尽量小、可随仓库分发；全量扩展由脚本
按需拉取，不把大文件塞进仓库。

## 公开来源评估

| 用途 | 候选来源 | 许可 | 结论 |
| --- | --- | --- | --- |
| 翻译黄金集（日→中） | FLORES-200 devtest（`jpn_Jpan` / `cmn_Hans`） | CC BY-SA 4.0 | 质量最高、句数充足；官方 zip 较大且部分 HF 镜像需登录，作为 CI 全量拉取的首选 |
| 翻译结构样例（日→中） | Tatoeba `jpn-cmn` 句对 | CC BY 2.0 | 轻量、无需登录，已用 20 句样本落地；只用于结构校验，不评估翻译质量 |
| 词级读音参考 | SudachiDict / JMdict 词级读音 | Apache-2.0 / CC BY-SA | 可用于词级对照，不能替代句级人工金集；现有读音覆盖率也不是准确率指标 |
| 难度分析（JLPT） | tanos.co.uk JLPT 词表（GitHub 转存） | CC BY | 可作 `level_from_tags` 映射验证；JLPT 无官方词表，结果标为近似 |
| 频率 | JPDB 频度表 | 许可不明 | 不宜直接分发，仅作为用户自备词典的格式参考 |
| 活用形 | 本项目规则测试 + jamdict（MIT）对照 | MIT | 用规则测试做回归；不移植 Yomitan 的 AGPL 规则代码 |

> 当前提交的 Tatoeba 样本只用于翻译结构检查：它不是翻译质量金集，也不含预期读音，不能作为读音金集。

## 当前落地

- `benchmarks/tatoeba_sample.json`：Tatoeba 日→中 20 句真实句对
  （来源与 CC BY 2.0 声明在文件内）；
- `scripts/run_benchmarks.py`：读取样本，校验读音原文保真与汉字读音覆盖率
  （阈值 0.95），并用 `validate_translation(paired=True)` 校验中文参考句；同时打印所选引擎、Python、可获取的相关包及词典版本；
- `scripts/benchmarks/prepare_tatoeba_sample.py`：从 Tatoeba 重新下载并重建样本；
- `tests/test_benchmark_sample.py`：黄金集格式、翻译结构、读音保真的单元测试；
- CI 增加 `benchmark` 任务，跑 `run_benchmarks.py`。

## 指标定义

- 读音覆盖率 = 含汉字的 token 中带读音（`hira` 非空）的比例；
- 翻译结构通过率 = 参考译句通过 `validate_translation` 零错误的比例；
- 原文保真 = 所有 token 的 `orig` 拼接等于输入（硬性失败项）。

## 下一阶段：读音准确率评估

当前脚本只证明原文保真、读音覆盖和翻译结构可通过；这些指标不能作为读音准确率结论。新增读音金样例前，需要记录数据许可、标注来源、复核状态和领域标签。含版权歌词不得未经许可放入可分发样例。

建议的最小样例字段：`id`、`domain`、`text`、`reference_reading(s)`、可选的 `reference_ruby_spans`、`source`、`license`、`review_status`。已复核案例还必须记录 `reviewer`、`review_basis` 和 ISO `reviewed_at`；评估器会拒绝缺少这些来源信息的 `reviewed` 案例。Ruby span 使用原文上的零起始、左闭右开 Unicode code point 偏移，避免 Python、JavaScript 和 Swift 的字符串索引单位不同造成歧义。读音比较前定义统一规范化：平假名表示、全角形式、长音及标点如何处理；原始结果仍需保留，不能只公布规范化后的分数。只有 `review_status=reviewed` 的例子进入准确率汇总；草案例子只用于开发回归。按歌曲划分歌词样本，避免同一副歌跨越评测集。

评估应分别报告：

- 读音字符准确率与 CER；
- Ruby/汉字跨度的 precision、recall、F1；
- 整行完全匹配率；
- 汉字读音覆盖率与未确认比例；
- 按普通文本、歌词、专名、多读音词、口语和古语拆分的结果。

至少比较 core 的 Sudachi Core、Uta 的 Sudachi Small 和 PyKakasi fallback，并记录引擎及词典版本。由于词典和切分模式不同，不要求 token 边界一致；对照应落在读音及 Ruby 输出行为上。数据和评估器就绪前，不发布“读音准确率”或跨引擎排名结论。

评估器已落在 `scripts/evaluate_readings.py`，支持 CER、整句读音精确匹配、汉字 token 覆盖率和可选 Ruby span P/R/F1。`benchmarks/reading_candidates.json` 是项目原创候选集，内容标为 CC0，但全部 `review_status=pending_review`；它只能通过 `--include-unreviewed` 做流程冒烟，默认不会进入准确率汇总。完成日语母语者复核并登记复核人/日期后，才可将对应案例标成 `reviewed`。

便于人工核对的逐例表见 [`reading-review-sheet.md`](reading-review-sheet.md)，其中展示原文、当前读音、Ruby span 和复核字段。当前 5 条全部待复核；复核表里的机器预测不是人工标签。

```bash
python scripts/evaluate_readings.py benchmarks/reading_candidates.json --include-unreviewed
```

正式基线暂缺已复核案例，所以当前不会给出读音准确率数字。KWDLC 可作为研究参照：其官方分发要求接受研究用途条件，原文也没有逐一取得著作权人许可；本仓库不复制或重分发其语料。可由有权使用语料的研究者在本地转换为上述 JSON 格式后评估，并只发布符合原许可的统计结果。

## 已知限制

- 读音覆盖率是"可读性"而非"人类读音准确率"；句级人工读音基准在公开领域
  稀缺，后续如引入社区标注语料再升级；
- Tatoeba 句对是学习者例句，结构简单，不能完全代表歌词/文学文本；
- FLORES-200 全量接入（约 1000+ 句对）建议在 CI 有网络时按需拉取。
