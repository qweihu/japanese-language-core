"""Best-effort Japanese deinflector (conjugated form -> dictionary form).

The rule engine is intentionally small and deterministic. It strips common
inflectional suffixes, reapplies dictionary-form endings, and emits several
candidates when the ending is ambiguous (e.g. 行った -> 行く/行つ/行る/行う).
Callers that own dictionary data should filter candidates with a lookup;
``japanese_language_core.dictionary`` provides exactly that hook.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Deinflection:
    """A candidate dictionary form and the rules used to reach it."""

    word: str
    rules: tuple[str, ...]

    @property
    def reason(self) -> str:
        return " + ".join(self.rules) if self.rules else "dictionary form"


Transform = Callable[[str], list[str]]


def _identity(base: str) -> list[str]:
    return [base]


def _append(kana: str) -> Transform:
    return lambda base: [base + kana]


_ENDING = {
    "い": ["う"],
    "き": ["く", "くる"],
    "ぎ": ["ぐ"],
    "し": ["す", "する"],
    "ち": ["つ"],
    "に": ["ぬ"],
    "び": ["ぶ"],
    "み": ["む"],
    "り": ["る"],
    "か": ["く"],
    "が": ["ぐ"],
    "さ": ["す"],
    "た": ["つ"],
    "な": ["ぬ"],
    "ば": ["ぶ"],
    "ま": ["む"],
    "ら": ["る"],
    "わ": ["う"],
}


def _ending_candidates(base: str) -> list[str]:
    if not base:
        return []
    return [base[:-1] + kana for kana in _ENDING.get(base[-1], [])]


def _te_transform(base: str) -> list[str]:
    """Dictionary forms reachable from a te/ta-form stem."""

    candidates: list[str] = []
    if base.endswith("かっ"):
        candidates.append(base[:-2] + "い")  # 高かっ -> 高い
    if base:
        candidates.append(base + "る")  # 食べ -> 食べる
    if base.endswith("っ"):
        for kana in ("く", "つ", "る", "う"):
            candidates.append(base[:-1] + kana)
    if base.endswith("い"):
        for kana in ("く", "ぐ"):
            candidates.append(base[:-1] + kana)
    if base.endswith("ん"):
        for kana in ("む", "ぬ", "ぶ"):
            candidates.append(base[:-1] + kana)
    if base.endswith("し"):
        candidates.append(base[:-1] + "す")
    return _dedupe(candidates)


def _nai_transform(base: str) -> list[str]:
    return _dedupe([base + "る", *_ending_candidates(base)])


def _masu_transform(base: str) -> list[str]:
    return _dedupe([base + "る", *_ending_candidates(base)])


def _sugiru_transform(base: str) -> list[str]:
    return _dedupe([base + "る", base + "い"])


def _te_bridge(suffix: str, reason: str) -> tuple[str, Transform, str]:
    """Strip a te-form bridge (e.g. てしまう) then apply te transform."""

    def transform(base: str) -> list[str]:
        return _te_transform(base)

    return suffix, transform, reason


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


# Rules are matched longest-first so that なかった/くない/かっ handled before
# shorter suffixes like た/ない.
_RULES: list[tuple[str, Transform, str]] = [
    ("ませんでした", _nai_transform, "polite past negative"),
    ("なければならない", _nai_transform, "obligation"),
    ("ないといけない", _nai_transform, "obligation"),
    _te_bridge("てはいけない", "prohibition"),
    _te_bridge("てしまう", "completive"),
    _te_bridge("ている", "progressive"),
    _te_bridge("ておく", "preparative"),
    _te_bridge("てほしい", "desiderative"),
    _te_bridge("てもいい", "permission"),
    ("なかった", _nai_transform, "past negative"),
    ("ましょう", _masu_transform, "polite volitional"),
    ("ました", _masu_transform, "polite past"),
    ("ません", _nai_transform, "polite negative"),
    ("ました", _masu_transform, "polite past"),
    ("ます", _masu_transform, "polite"),
    ("くない", lambda base: [base + "い"], "negative adjective"),
    ("くて", lambda base: [base + "い"], "te-form adjective"),
    ("かった", lambda base: [base + "い"], "past adjective"),
    ("なかったら", _nai_transform, "past negative conditional"),
    ("なかったり", _nai_transform, "past negative listing"),
    ("なければ", _nai_transform, "negative conditional"),
    ("ない", _nai_transform, "negative"),
    ("すぎる", _sugiru_transform, "excessive"),
    ("やすい", _masu_transform, "easy to"),
    ("にくい", _masu_transform, "hard to"),
    ("ながら", _masu_transform, "while"),
    ("たり", _te_transform, "listing"),
    ("たら", _te_transform, "conditional"),
    ("れば", lambda base: _dedupe([base + "る", base + "い"]), "conditional"),
    ("そうだ", _sugiru_transform, "apparent"),
    ("らしい", _identity, "hearsay"),
    ("ようだ", _identity, "seeming"),
    ("みたいだ", _identity, "seeming"),
    ("はずだ", _identity, "expectation"),
    ("べきだ", _identity, "should"),
    ("つもりだ", _identity, "intention"),
    ("たい", _masu_transform, "desiderative"),
    ("たかった", _masu_transform, "desiderative past"),
    ("させる", _masu_transform, "causative"),
    ("られる", _masu_transform, "potential/passive"),
    ("れる", _masu_transform, "potential/passive"),
    ("て", _te_transform, "te-form"),
    ("た", _te_transform, "past"),
    ("だ", _te_transform, "past (voiced)"),
    ("で", _te_transform, "te-form (voiced)"),
    ("ず", lambda base: _dedupe([base + "る", *_ending_candidates(base)]), "negative"),
    ("でした", lambda base: [base + "です"], "polite copula past"),
    ("だった", lambda base: [base + "だ"], "copula past"),
]

_MAX_DEPTH = 5
_MAX_CANDIDATES = 200


def deinflect(word: str) -> list[Deinflection]:
    """Return dictionary-form candidates for a Japanese word."""

    ordered = sorted(_RULES, key=lambda rule: len(rule[0]), reverse=True)
    results: list[Deinflection] = [Deinflection(word, ())]
    seen: set[tuple[str, tuple[str, ...]]] = {(word, ())}
    queue: list[tuple[str, tuple[str, ...], int]] = [(word, (), 0)]
    while queue:
        current, rules, depth = queue.pop(0)
        if depth >= _MAX_DEPTH or len(results) >= _MAX_CANDIDATES:
            continue
        for suffix, transform, reason in ordered:
            if not current.endswith(suffix):
                continue
            base = current[: -len(suffix)]
            if not base:
                continue
            for candidate in transform(base):
                key = (candidate, rules + (reason,))
                if key in seen:
                    continue
                seen.add(key)
                results.append(Deinflection(candidate, rules + (reason,)))
                queue.append((candidate, rules + (reason,), depth + 1))
    return results
