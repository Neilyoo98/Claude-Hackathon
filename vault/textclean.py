"""Normalize text from feeds: HTML entities, tags, whitespace."""

from __future__ import annotations

import html
import re


def clean_plain_text(text: str, *, max_len: int | None = None) -> str:
    """
    Decode HTML entities (including double-encoded &amp;#8217; style),
    strip HTML tags, collapse whitespace.
    """
    if not text:
        return ""
    t = str(text).strip()
    for _ in range(6):
        n = html.unescape(t)
        if n == t:
            break
        t = n
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    # Prefer straight quotes in plain text (feeds often use &#8217; etc.)
    t = (
        t.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2014", "-")
        .replace("\u2013", "-")
    )
    if max_len is not None and len(t) > max_len:
        t = t[: max_len - 3].rstrip() + "..."
    return t
