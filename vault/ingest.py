from __future__ import annotations

from datetime import datetime, timezone

from vault.config import RSS_FEEDS, congress_api_key
from vault.fetchers.congress import fetch_congress_items
from vault.fetchers.rss_fetcher import fetch_rss_items
from vault.models import CivicItem
from vault.storage import load_items, merge_dedupe, save_items


def collect_all(congress_limit: int = 25) -> tuple[list[CivicItem], dict[str, int]]:
    """Fetch all sources; does not persist."""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    stats: dict[str, int] = {"rss_entries": 0, "legislation": 0, "congress_skipped_no_key": 0}
    items: list[CivicItem] = []

    for label, url in RSS_FEEDS:
        batch = fetch_rss_items(label, url, fetched_at=now)
        items.extend(batch)
        stats["rss_entries"] += len(batch)

    bills = fetch_congress_items(limit_per_type=congress_limit)
    if not bills and congress_api_key() is None:
        stats["congress_skipped_no_key"] = 1
    items.extend(bills)
    stats["legislation"] = len(bills)

    return items, stats


def refresh_database(congress_limit: int = 25) -> dict[str, int]:
    incoming, stats = collect_all(congress_limit=congress_limit)
    existing = load_items()
    merged, merge_count = merge_dedupe(existing, incoming)
    save_items(merged)
    stats["merged"] = merge_count
    stats["stored_total"] = len(merged)
    return stats
