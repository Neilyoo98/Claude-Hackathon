"""Title keyword extraction for personalization."""

from __future__ import annotations

import re

_STOP = frozenset(
    """
    a an the and or but if in on at to for of as is was are were be been being
    it its this that these those with from by about into over after before
    than then so not no yes all any each few more most other some such only
    own same so than too very can will just should could would may might must
    has have had do does did doing done get got go going went come came make made
    say said says like up out off down new also back well what when where who how
    why which while during through between under again further once here there
    both each few more most other some such
    """.split()
)


def extract_keywords(title: str, min_len: int = 3) -> list[str]:
    if not title:
        return []
    raw = re.findall(r"[a-z0-9]+", title.lower())
    out: list[str] = []
    for w in raw:
        if len(w) < min_len or w in _STOP:
            continue
        if w not in out:
            out.append(w)
    return out[:24]
