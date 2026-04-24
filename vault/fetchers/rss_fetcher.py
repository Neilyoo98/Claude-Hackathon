from __future__ import annotations

from datetime import datetime, timezone

import feedparser

from vault.ids import item_id_from_url
from vault.models import CivicItem
from vault.textclean import clean_plain_text
from vault.topics import classify_topic


def _entry_date(entry) -> str:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc).date().isoformat()
            except (TypeError, ValueError):
                continue
    return ""


def _summary(entry) -> str:
    s = getattr(entry, "summary", None) or getattr(entry, "description", None) or ""
    return clean_plain_text(str(s), max_len=600)


def fetch_rss_items(feed_label: str, feed_url: str, fetched_at: str) -> list[CivicItem]:
    parsed = feedparser.parse(feed_url)
    out: list[CivicItem] = []
    for entry in getattr(parsed, "entries", []) or []:
        link = (getattr(entry, "link", None) or "").strip()
        if not link:
            continue
        raw_title = (getattr(entry, "title", None) or "").strip() or "(no title)"
        title = clean_plain_text(raw_title) or "(no title)"
        summary = _summary(entry)
        date = _entry_date(entry)
        topic = classify_topic(f"{title}\n{summary}")
        out.append(
            CivicItem(
                id=item_id_from_url(link),
                title=title,
                summary=summary,
                source=feed_label,
                url=link,
                date=date,
                topic=topic,
                kind="rss",
                fetched_at=fetched_at,
            )
        )
    return out
