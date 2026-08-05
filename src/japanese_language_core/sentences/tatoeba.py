"""Reader for Tatoeba sentence exports (CC BY 2.0).

Data files are the per-language ``*_sentences.tsv.bz2`` and
``<src>-<tgt>_links.tsv.bz2`` exports from
https://tatoeba.org/en/downloads. This module reads already-decompressed
TSV files; fetching and decompressing is the caller's concern.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Sentence:
    id: str
    text: str
    lang: str = ""


@dataclass
class SentenceBank:
    sentences: dict[str, Sentence] = field(default_factory=dict)
    links: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def from_tatoeba(
        cls,
        sentences_path: str | Path,
        links_path: str | Path,
        *,
        source_lang: str = "jpn",
        target_lang: str = "cmn",
    ) -> "SentenceBank":
        bank = cls()
        with open(sentences_path, encoding="utf-8") as handle:
            for line in handle:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 3:
                    continue
                sentence_id, lang, text = parts[0], parts[1], parts[2]
                if lang in {source_lang, target_lang}:
                    bank.sentences[sentence_id] = Sentence(
                        id=sentence_id, text=text, lang=lang
                    )
        with open(links_path, encoding="utf-8") as handle:
            for line in handle:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 2:
                    continue
                source_id, target_id = parts[0], parts[1]
                if source_id in bank.sentences and target_id in bank.sentences:
                    bank.links.setdefault(source_id, []).append(target_id)
        return bank

    def lookup(self, term: str, *, lang: str = "jpn") -> list[Sentence]:
        return [
            sentence
            for sentence in self.sentences.values()
            if sentence.lang == lang and term in sentence.text
        ]

    def translations(self, sentence_id: str) -> list[Sentence]:
        return [
            self.sentences[target_id]
            for target_id in self.links.get(sentence_id, [])
            if target_id in self.sentences
        ]
