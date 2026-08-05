"""Surface-level Japanese particle detection (best effort).

Particles are boundary-dependent: the same kana can be part of a longer word
(わたし vs は). This detector treats a kana run as a particle if the run is a
known particle, or ends with one after a longer kana stem. For authoritative
segmentation, feed reading-engine tokens into the caller's own analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from ..reading.kana import is_kana


PARTICLES = (
    "は", "が", "を", "に", "で", "と", "へ", "から", "まで", "より",
    "の", "も", "や", "か", "ね", "よ", "ぞ", "ぜ", "な", "なあ",
    "かな", "かしら", "って", "ってば", "けど", "けれど", "し", "ながら",
    "ので", "のに", "でも", "では", "とは", "には", "へは", "ほど",
    "ぐらい", "くらい", "ばかり", "だけ", "しか", "こそ", "さえ",
    "など", "なんて", "もの", "こと", "ところ", "わけ", "はず", "つもり",
)


@dataclass(frozen=True)
class ParticleMatch:
    """A detected particle and its location."""

    token: str
    particle: str
    start: int
    end: int


_KANA_RUN_RE = re.compile(r"[ぁ-ゖァ-ヺー]+")


def find_particles(text: str) -> list[ParticleMatch]:
    matches: list[ParticleMatch] = []
    for run in _KANA_RUN_RE.finditer(text):
        token = run.group(0)
        for particle in sorted(PARTICLES, key=len, reverse=True):
            if token == particle:
                matches.append(
                    ParticleMatch(token, particle, run.start(), run.end())
                )
                break
            if token.endswith(particle) and len(token) > len(particle):
                end = run.start() + len(token)
                matches.append(
                    ParticleMatch(token, particle, end - len(particle), end)
                )
                break
    matches.sort(key=lambda match: match.start)
    return matches
