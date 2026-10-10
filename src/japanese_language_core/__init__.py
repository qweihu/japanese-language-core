"""Nihongo Core: shared Japanese language capabilities.

The package is independent of Bunomi's ruby renderer, lyric workflows, and
export policy. Consumers opt into capabilities through extras and import only
the submodules they use (``reading``, ``translation``, ``dictionary``,
``grammar``, ``export``). The top-level module intentionally imports nothing
heavy so a translation-only install stays dependency-free.
"""

__version__ = "0.4.0"

