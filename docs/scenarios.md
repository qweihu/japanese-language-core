# 场景导航（Scenarios）

更新日期：2026-08-05

这张图把"用户想做什么"映射到 japanese-language-core 的模块与状态，
并对照热门开源项目的做法，标出缺口与规划。状态含义：

- ✅ 生产：有消费方且被测试覆盖；
- 🟡 实验：接口稳定、有测试，但暂无内置消费方；
- ❌ 缺失：尚未实现。

## 场景地图（总表）

| 场景 | 模块 | 状态 | 热门项目怎么做的 | 规划 |
| --- | --- | --- | --- | --- |
| 阅读与注音（furigana/ruby） | `reading` + `reading.alignment` | ✅ 生产 | Yomitan/Jitendex 词典内读音分布；japanese-furigana-normalize | P1 词典内分布接入（需先评估数据可用性） |
| 假名/罗马音转换 | `reading.kana` | ✅ 生产 | pykakasi；kusanaji（Node） | 保持 |
| 词形分析（活用形） | `reading.deinflect` | ✅ 基础 | Yomitan MultiLanguageTransformer；jamdict | P0 补充"辞書形 → 活用形"生成（conjugator） |
| 词典查询（词条/汉字） | `dictionary` | 🟡 实验 | jamdict；Yomitan 词典生态；jisho | P1 通配符/前缀搜索 |
| 专名读音 | `dictionary`（Yomitan/JMnedict bank） | 🟡 部分 | JMnedict；Yomitan | P2 专名模块与上下文消歧 |
| 语法分析 | `grammar` | 🟡 实验 | GiNZA/spaCy（PoS + 依存）；BunPro | P0 在 `ReadingToken` 暴露 PoS/辞書形元数据；依存句法交给 GiNZA，不进 core |
| 翻译 | `translation` | ✅ 生产 | LLM 管线 + COMET/BLEU 评测 | 押后 LLM-as-judge（外部评测工具） |
| 难度评估 | `dictionary.jlpt` | 🟡 实验 | JPDB/BCCWJ 频度；tanos JLPT（CC BY） | P1 频度 + 可读性打分 |
| 声调（pitch accent） | `dictionary`（meta bank） | 🟡 实验 | Kanjium/Wadoku；Yomitan meta；PitchAccent add-on | P1 声调渲染与分析（位置 → 升降模式） |
| 例句/句库 | — | ❌ | Tatoeba API/导出；tatoebatools | P0 Tatoeba 句库读取器（复用基准集数据流） |
| 闪卡挖掘（SRS） | `export.anki` | 🟡 实验 | jp-mining-note；Yomichan + AnkiConnect | P2 mining 流水线契约（句→卡→Anki） |
| 文本统计与归一化 | `reading.kana` + `structure` | ✅ 部分 | NFKC；MeCab 统计 | P0 句子分割 + 拍（mora）计数 |
| 语音/音频 | — | ❌ | Onsei；OpenJTalk；Voicevox；Forvo | P2 音频提供方契约（不合成） |
| 汉字信息（部首/笔顺） | `dictionary.kanji` | 🟡 实验 | KanjiVG；WaniKani；kanjiapi | P2 部首/笔顺读取器 |
| OCR/漫画阅读 | — | ❌（外部） | manga-ocr；mokuro | 外部集成适配，不进 core |

## 与热门项目功能矩阵

| 功能 | japanese-language-core | Yomitan | jamdict | GiNZA/spaCy | pykakasi |
| --- | --- | --- | --- | --- | --- |
| 分词/上下文读音 | ✅（Sudachi/PyKakasi） | ✅ | ✅（MeCab） | ✅ | ✅ |
| furigana 对齐 | 🟡 贪心（限制已文档化） | ✅ 词典内分布 | 🟡 | — | — |
| 词典读取 | ✅ Yomitan 格式 | ✅ 格式即生态 | ✅ JMdict 系 | — | — |
| 活用形还原 | ✅ 规则子集 | ✅ MultiLanguageTransformer | ✅ | — | — |
| 活用形生成 | ❌ 规划中 | 🟡 有限 | ❌ | — | — |
| PoS/依存句法 | ❌（规划 PoS 元数据） | 🟡 词性标签 | 🟡 | ✅ 完整 | — |
| 翻译契约/校验 | ✅ 独特能力 | ❌ | ❌ | — | — |
| 难度/频度 | 🟡 JLPT tag 近似 | ✅ 频度字典 | 🟡 | — | — |
| 声调 | 🟡 meta 解析 | ✅ meta + 渲染 | ❌ | — | — |
| 例句句库 | ❌ 规划中 | 🟡 外部 | 🟡 | — | — |
| Anki 导出 | 🟡 契约层 | ✅ AnkiConnect | ❌ | — | — |
| OCR | ❌ 外部集成 | ❌ | ❌ | — | — |

## 缺口与优先级

### P0（成本低、解锁其他能力，建议先做）

- `ReadingToken` 扩展元数据：`part_of_speech`、`dictionary_form`（辞書形）、
  `normalized_form`（Sudachi 标准形）。Sudachi 已提供这些字段，成本低，
  能直接升级活用形过滤、语法标注与难度分析；
- `reading.conjugator`：从辞書形生成常用活用形（ます/ない/て/た/ば/意向/
  命令），与 deinflect 形成闭环；
- `reading.splitter` + `reading.mora`：句子分割（。」！？）与拍计数，
  服务于歌词、闪卡与声调；
- `sentences`：Tatoeba 句库读取器（复用基准集数据流与 CC BY 2.0 声明）。

### P1（值得做）

- 词典通配符/前缀搜索（Yomitan 同款）；
- 声调渲染：position → 升降模式（平板/头高/中高/尾高）；
- 难度打分：频率 + JLPT + 可读性公式；
- 词典内 furigana 分布接入（先评估公开词典数据可用性）；
- KanjiVG 笔顺/部首读取器。

### P2（有消费方再做）

- JMnedict 专名读音模块；
- Anki mining 流水线契约（句 → 卡 → AnkiConnect payload）；
- 音频提供方契约（Forvo/Onsei/OpenJTalk 适配点，不合成音频）；
- OCR 集成适配（manga-ocr/mokuro 的输出契约）。

### 明确不做（交给专业项目）

- 依存句法/语义分析（GiNZA/spaCy 的地盘，core 只消费其输出）；
- TTS 合成、UI、账号与云服务；
- 歌词/网页抓取（应用层）。

## 参考项目

- [Yomitan](https://github.com/yomidevs/yomitan)：词典生态、活用形、声调、Anki。
- [jamdict](https://github.com/neocl/jamdict)：JMdict/KanjiDic2/JMnedict 查询。
- [GiNZA](https://github.com/megagonlabs/ginza)：spaCy 日语 PoS/依存/NER。
- [pykakasi](https://pypi.org/project/pykakasi/)：假名/罗马音。
- [japanese-furigana-normalize](https://github.com/MarvNC/japanese-furigana-normalize)：读音-汉字对齐。
- [jp-mining-note](https://github.com/Aquafina-water-bottle/jp-mining-note)：Anki 日语卡片模板生态。
- [Tatoeba](https://tatoeba.org/)：句库与句对。
- [Kanjium](https://github.com/mifunetoshiro/kanjium) / [PitchAccent](https://github.com/Ajatt-Tools/PitchAccent)：声调数据与工具。
- [manga-ocr](https://github.com/kha-white/manga-ocr) / [mokuro](https://github.com/kha-white/mokuro)：漫画 OCR。
