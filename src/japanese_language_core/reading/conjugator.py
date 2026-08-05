"""Best-effort conjugation generator: dictionary form -> common forms.

Complements ``deinflect`` (conjugated -> dictionary form) with the forward
direction. Ichidan/godan is inferred from the ending; ambiguous verbs such as
帰る/切る (godan despite え/い + る) can be forced with ``kind``.
"""

from __future__ import annotations


_IRREGULAR = {
    "する": {
        "polite": "します",
        "polite_negative": "しません",
        "polite_past": "しました",
        "negative": "しない",
        "negative_past": "しなかった",
        "te": "して",
        "past": "した",
        "conditional": "すれば",
        "volitional": "しよう",
        "potential": "できる",
        "imperative": "しろ",
        "desiderative": "したい",
    },
    "来る": {
        "polite": "来ます",
        "polite_negative": "来ません",
        "polite_past": "来ました",
        "negative": "来ない",
        "negative_past": "来なかった",
        "te": "来て",
        "past": "来た",
        "conditional": "来れば",
        "volitional": "来よう",
        "potential": "来られる",
        "desiderative": "来たい",
    },
}
_IRREGULAR["くる"] = {
    key: value.replace("来", "く")
    if key
    in {
        "polite",
        "polite_negative",
        "polite_past",
        "negative",
        "negative_past",
        "te",
        "past",
        "conditional",
        "volitional",
        "desiderative",
    }
    else value
    for key, value in _IRREGULAR["来る"].items()
}


_GODAN = {
    "う": ("います", "わない", "って", "った", "えば", "おう", "える"),
    "く": ("きます", "かない", "いて", "いた", "けば", "こう", "ける"),
    "ぐ": ("ぎます", "がない", "いで", "いだ", "げば", "ごう", "げる"),
    "す": ("します", "さない", "して", "した", "せば", "そう", "せる"),
    "つ": ("ちます", "たない", "って", "った", "てば", "とう", "てる"),
    "ぬ": ("にます", "なない", "んで", "んだ", "ねば", "のう", "ねる"),
    "ぶ": ("びます", "ばない", "んで", "んだ", "べば", "ぼう", "べる"),
    "む": ("みます", "まない", "んで", "んだ", "めば", "もう", "める"),
    "る": ("ります", "らない", "って", "った", "れば", "ろう", "れる"),
}


def _build_godan(word: str, last: str) -> dict[str, str]:
    stem = word[:-1]
    polite, negative, te, past, conditional, volitional, potential = _GODAN[last]
    return {
        "polite": stem + polite,
        "polite_negative": stem + negative + "ません",
        "polite_past": stem + polite.replace("ます", "ました"),
        "negative": stem + negative,
        "negative_past": stem + negative + "なかった",
        "te": stem + te,
        "past": stem + past,
        "conditional": stem + conditional,
        "volitional": stem + volitional,
        "potential": stem + potential,
        "desiderative": stem + "たい",
    }


def _build_ichidan(word: str) -> dict[str, str]:
    stem = word[:-1]
    return {
        "polite": stem + "ます",
        "polite_negative": stem + "ません",
        "polite_past": stem + "ました",
        "negative": stem + "ない",
        "negative_past": stem + "なかった",
        "te": stem + "て",
        "past": stem + "た",
        "conditional": stem + "れば",
        "volitional": stem + "よう",
        "potential": stem + "られる",
        "imperative": stem + "ろ",
        "desiderative": stem + "たい",
    }


def _build_adjective(word: str) -> dict[str, str]:
    stem = word[:-1]
    return {
        "polite": word + "です",
        "negative": stem + "くない",
        "negative_past": stem + "くなかった",
        "adverbial": stem + "く",
        "te": stem + "くて",
        "past": stem + "かった",
        "conditional": stem + "ければ",
        "apparent": stem + "そう",
    }


_ICHIDAN_HINT = "いきしちにひみりぎじびぴえけせてねへめれげぜべぺ"


def conjugate(word: str, kind: str = "auto") -> dict[str, str]:
    """Return common conjugation forms for a dictionary-form word."""

    if word in _IRREGULAR:
        return dict(_IRREGULAR[word])
    if word.endswith("い") and len(word) >= 2 and not word.endswith("る"):
        return _build_adjective(word)
    if word.endswith("る") and len(word) > 2:
        if kind == "godan":
            return _build_godan(word, "る")
        if kind == "ichidan":
            return _build_ichidan(word)
        if word[-2] in _ICHIDAN_HINT:
            return _build_ichidan(word)
        return _build_godan(word, "る")
    if word and word[-1] in _GODAN:
        return _build_godan(word, word[-1])
    return {}
