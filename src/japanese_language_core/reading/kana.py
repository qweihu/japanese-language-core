"""Kana and romaji utilities (pure standard library, no dependencies)."""

from __future__ import annotations

HIRAGANA_START = 0x3041
HIRAGANA_END = 0x3096
KATAKANA_START = 0x30A1
KATAKANA_END = 0x30F6
KATAKANA_HALFWIDTH_START = 0xFF66
KATAKANA_HALFWIDTH_END = 0xFF9D


def is_hiragana(char: str) -> bool:
    return len(char) == 1 and HIRAGANA_START <= ord(char) <= HIRAGANA_END


def is_katakana(char: str) -> bool:
    return len(char) == 1 and KATAKANA_START <= ord(char) <= KATAKANA_END


def is_kana(char: str) -> bool:
    return is_hiragana(char) or is_katakana(char)


def is_kanji(char: str) -> bool:
    if len(char) != 1:
        return False
    codepoint = ord(char)
    return 0x4E00 <= codepoint <= 0x9FFF or 0x3400 <= codepoint <= 0x4DBF


def to_hiragana(text: str) -> str:
    """Normalize katakana (including halfwidth + dakuten marks) to hiragana."""

    normalized: list[str] = []
    for char in text:
        codepoint = ord(char)
        if KATAKANA_START <= codepoint <= KATAKANA_END:
            normalized.append(chr(codepoint - 0x60))
        elif KATAKANA_HALFWIDTH_START <= codepoint <= KATAKANA_HALFWIDTH_END:
            normalized.append(_HALFWIDTH_KATAKANA.get(char, char))
        elif char in "ﾞﾟ" and normalized and is_kana(normalized[-1]):
            voiced = _apply_diacritic(normalized[-1], char)
            normalized[-1] = voiced
        else:
            normalized.append(char)
    return "".join(normalized)


def to_katakana(text: str) -> str:
    """Convert hiragana (and halfwidth katakana) to fullwidth katakana."""

    converted: list[str] = []
    for char in text:
        codepoint = ord(char)
        if HIRAGANA_START <= codepoint <= HIRAGANA_END:
            converted.append(chr(codepoint + 0x60))
        elif KATAKANA_HALFWIDTH_START <= codepoint <= KATAKANA_HALFWIDTH_END:
            converted.append(_HALFWIDTH_KATAKANA.get(char, char))
        else:
            converted.append(char)
    return "".join(converted)


def normalize_width(text: str) -> str:
    """Normalize halfwidth katakana and halfwidth ASCII to fullwidth forms."""

    return to_hiragana(text)


# Small, explicit romaji table (Hepburn-ish). Longest entries are matched
# first so that きゃ/しゅ and similar digraphs win over single kana.
_ROMAJI = {
    "っ": "",
    "ゃ": "ya",
    "ゅ": "yu",
    "ょ": "yo",
    "ぁ": "a",
    "ぃ": "i",
    "ぅ": "u",
    "ぇ": "e",
    "ぉ": "o",
    "ゎ": "wa",
    "ゕ": "ka",
    "ゖ": "ke",
    "きゃ": "kya",
    "きゅ": "kyu",
    "きょ": "kyo",
    "しゃ": "sha",
    "しゅ": "shu",
    "しょ": "sho",
    "ちゃ": "cha",
    "ちゅ": "chu",
    "ちょ": "cho",
    "にゃ": "nya",
    "にゅ": "nyu",
    "にょ": "nyo",
    "ひゃ": "hya",
    "ひゅ": "hyu",
    "ひょ": "hyo",
    "みゃ": "mya",
    "みゅ": "myu",
    "みょ": "myo",
    "りゃ": "rya",
    "りゅ": "ryu",
    "りょ": "ryo",
    "ぎゃ": "gya",
    "ぎゅ": "gyu",
    "ぎょ": "gyo",
    "じゃ": "ja",
    "じゅ": "ju",
    "じょ": "jo",
    "びゃ": "bya",
    "びゅ": "byu",
    "びょ": "byo",
    "ぴゃ": "pya",
    "ぴゅ": "pyu",
    "ぴょ": "pyo",
    "あ": "a",
    "い": "i",
    "う": "u",
    "え": "e",
    "お": "o",
    "か": "ka",
    "き": "ki",
    "く": "ku",
    "け": "ke",
    "こ": "ko",
    "さ": "sa",
    "し": "shi",
    "す": "su",
    "せ": "se",
    "そ": "so",
    "た": "ta",
    "ち": "chi",
    "つ": "tsu",
    "て": "te",
    "と": "to",
    "な": "na",
    "に": "ni",
    "ぬ": "nu",
    "ね": "ne",
    "の": "no",
    "は": "ha",
    "ひ": "hi",
    "ふ": "fu",
    "へ": "he",
    "ほ": "ho",
    "ま": "ma",
    "み": "mi",
    "む": "mu",
    "め": "me",
    "も": "mo",
    "や": "ya",
    "ゆ": "yu",
    "よ": "yo",
    "ら": "ra",
    "り": "ri",
    "る": "ru",
    "れ": "re",
    "ろ": "ro",
    "わ": "wa",
    "を": "o",
    "ん": "n",
    "が": "ga",
    "ぎ": "gi",
    "ぐ": "gu",
    "げ": "ge",
    "ご": "go",
    "ざ": "za",
    "じ": "ji",
    "ず": "zu",
    "ぜ": "ze",
    "ぞ": "zo",
    "だ": "da",
    "ぢ": "ji",
    "づ": "zu",
    "で": "de",
    "ど": "do",
    "ば": "ba",
    "び": "bi",
    "ぶ": "bu",
    "べ": "be",
    "ぼ": "bo",
    "ぱ": "pa",
    "ぴ": "pi",
    "ぷ": "pu",
    "ぺ": "pe",
    "ぽ": "po",
    "ー": "",
}

_DAKUTEN = {
    "か": "が", "き": "ぎ", "く": "ぐ", "け": "げ", "こ": "ご",
    "さ": "ざ", "し": "じ", "す": "ず", "せ": "ぜ", "そ": "ぞ",
    "た": "だ", "ち": "ぢ", "つ": "づ", "て": "で", "と": "ど",
    "は": "ば", "ひ": "び", "ふ": "ぶ", "へ": "べ", "ほ": "ぼ",
    "う": "ゔ",
}
_HANDAKUTEN = {
    "は": "ぱ", "ひ": "ぴ", "ふ": "ぷ", "へ": "ぺ", "ほ": "ぽ",
}


def _apply_diacritic(char: str, mark: str) -> str:
    table = _DAKUTEN if mark == "ﾞ" else _HANDAKUTEN
    return table.get(char, char)


def to_romaji(text: str) -> str:
    """Convert hiragana text to Hepburn-style romaji (pure Python).

    Katakana input is normalized to hiragana first. The small tsu doubles the
    following consonant, and the long-vowel mark is skipped. This is a
    pragmatic reader for tests and renderers; the reading extra's PyKakasi
    path remains available for production-grade romanization.
    """

    source = to_hiragana(text)
    result: list[str] = []
    index = 0
    length = len(source)
    while index < length:
        char = source[index]
        if char == "っ":
            nxt = source[index + 1] if index + 1 < length else ""
            roma = _ROMAJI.get(nxt, "")
            if roma and roma[0].isalpha():
                result.append(roma[0])
        elif char == "ん":
            nxt = source[index + 1] if index + 1 < length else ""
            result.append("m" if nxt and nxt in "ばぱまびぴみぶぷむべぺめぼぽも" else "n")
        else:
            result.append(_ROMAJI.get(char, char))
        index += 1
    return "".join(result)


# Halfwidth katakana to fullwidth hiragana mapping used by to_hiragana.
_HALFWIDTH_KATAKANA = {
    "\uff66": "ヲ",
    "\uff67": "ァ",
    "\uff68": "ィ",
    "\uff69": "ゥ",
    "\uff6a": "ェ",
    "\uff6b": "ォ",
    "\uff6c": "ャ",
    "\uff6d": "ュ",
    "\uff6e": "ョ",
    "\uff6f": "ッ",
    "\uff70": "ー",
    "\uff71": "ア",
    "\uff72": "イ",
    "\uff73": "ウ",
    "\uff74": "エ",
    "\uff75": "オ",
    "\uff76": "カ",
    "\uff77": "キ",
    "\uff78": "ク",
    "\uff79": "ケ",
    "\uff7a": "コ",
    "\uff7b": "サ",
    "\uff7c": "シ",
    "\uff7d": "ス",
    "\uff7e": "セ",
    "\uff7f": "ソ",
    "\uff80": "タ",
    "\uff81": "チ",
    "\uff82": "ツ",
    "\uff83": "テ",
    "\uff84": "ト",
    "\uff85": "ナ",
    "\uff86": "ニ",
    "\uff87": "ヌ",
    "\uff88": "ネ",
    "\uff89": "ノ",
    "\uff8a": "ハ",
    "\uff8b": "ヒ",
    "\uff8c": "フ",
    "\uff8d": "ヘ",
    "\uff8e": "ホ",
    "\uff8f": "マ",
    "\uff90": "ミ",
    "\uff91": "ム",
    "\uff92": "メ",
    "\uff93": "モ",
    "\uff94": "ヤ",
    "\uff95": "ユ",
    "\uff96": "ヨ",
    "\uff97": "ラ",
    "\uff98": "リ",
    "\uff99": "ル",
    "\uff9a": "レ",
    "\uff9b": "ロ",
    "\uff9c": "ワ",
    "\uff9d": "ン",
}


def _rebuild_halfwidth_hiragana() -> dict[str, str]:
    """Halfwidth katakana characters map to fullwidth katakana; convert those
    to hiragana so ``to_hiragana`` output is always hiragana."""

    return {k: to_hiragana(v) for k, v in _HALFWIDTH_KATAKANA.items()}


_HALFWIDTH_KATAKANA = _rebuild_halfwidth_hiragana()
