# 基准集方案（benchmarks）

更新日期：2026-08-05

## 原则

优先采用公开材料并保证许可合规；样本尽量小、可随仓库分发；全量扩展由脚本
按需拉取，不把大文件塞进仓库。

## 公开来源评估

| 用途 | 候选来源 | 许可 | 结论 |
| --- | --- | --- | --- |
| 翻译黄金集（日→中） | FLORES-200 devtest（`jpn_Jpan` / `cmn_Hans`） | CC BY-SA 4.0 | 质量最高、句数充足；官方 zip 较大且部分 HF 镜像需登录，作为 CI 全量拉取的首选 |
| 翻译黄金集（日→中） | Tatoeba `jpn-cmn` 句对 | CC BY 2.0 | 轻量、无需登录，已用 20 句样本落地 |
| 读音黄金集 | SudachiDict / JMdict 词级读音 | Apache-2.0 / CC BY-SA | 句级公开读音基准稀缺；用"词典词级读音近似 + 原文保真 + 读音覆盖率"作为可量化的替代指标，并注明限制 |
| 难度分析（JLPT） | tanos.co.uk JLPT 词表（GitHub 转存） | CC BY | 可作 `level_from_tags` 映射验证；JLPT 无官方词表，结果标为近似 |
| 频率 | JPDB 频度表 | 许可不明 | 不宜直接分发，仅作为用户自备词典的格式参考 |
| 活用形 | 本项目规则测试 + jamdict（MIT）对照 | MIT | 用规则测试做回归；不移植 Yomitan 的 AGPL 规则代码 |

## 当前落地

- `benchmarks/tatoeba_sample.json`：Tatoeba 日→中 20 句真实句对
  （来源与 CC BY 2.0 声明在文件内）；
- `scripts/run_benchmarks.py`：读取黄金集，校验读音原文保真与汉字读音覆盖率
  （阈值 0.95），并用 `validate_translation(paired=True)` 校验中文参考句；
- `scripts/benchmarks/prepare_tatoeba_sample.py`：从 Tatoeba 重新下载并重建样本；
- `tests/test_benchmark_sample.py`：黄金集格式、翻译结构、读音保真的单元测试；
- CI 增加 `benchmark` 任务，跑 `run_benchmarks.py`。

## 指标定义

- 读音覆盖率 = 含汉字的 token 中带读音（`hira` 非空）的比例；
- 翻译结构通过率 = 参考译句通过 `validate_translation` 零错误的比例；
- 原文保真 = 所有 token 的 `orig` 拼接等于输入（硬性失败项）。

## 已知限制

- 读音覆盖率是"可读性"而非"人类读音准确率"；句级人工读音基准在公开领域
  稀缺，后续如引入社区标注语料再升级；
- Tatoeba 句对是学习者例句，结构简单，不能完全代表歌词/文学文本；
- FLORES-200 全量接入（约 1000+ 句对）建议在 CI 有网络时按需拉取。
