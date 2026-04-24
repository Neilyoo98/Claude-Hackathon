from __future__ import annotations

import random
from dataclasses import dataclass

from vault.models import CivicItem

HIGH_ENERGY_PROMPT = (
    "You're reading these 3 civic signals. What systemic pattern connects them? "
    "Who benefits, who's burdened, and what would you ask your representative?"
)


@dataclass
class RecallBundle:
    mode: str
    items: list[CivicItem]
    prompt: str | None = None


def recall_low_energy(items: dict[str, CivicItem]) -> RecallBundle:
    pool = sorted(items.values(), key=lambda x: x.date, reverse=True)[:20]
    if not pool:
        return RecallBundle(mode="low", items=[], prompt="Vault is empty.")
    item = random.choice(pool)
    return RecallBundle(mode="low", items=[item])


def recall_high_energy(items: dict[str, CivicItem]) -> RecallBundle:
    all_items = list(items.values())
    if not all_items:
        return RecallBundle(mode="high", items=[], prompt="Vault is empty.")

    bills = [i for i in all_items if i.kind == "legislation"]
    rss = [i for i in all_items if i.kind == "rss"]
    n_old = max(len(all_items) // 3, 1)
    old = sorted(all_items, key=lambda x: x.date)[:n_old]

    selected: list[CivicItem] = []
    seen_topics: set[str] = set()

    for pool in (bills, rss, old, all_items):
        pool_copy = list(pool)
        random.shuffle(pool_copy)
        for item in pool_copy:
            if item.id not in {i.id for i in selected} and item.topic not in seen_topics:
                selected.append(item)
                seen_topics.add(item.topic)
            if len(selected) == 3:
                break
        if len(selected) == 3:
            break

    # Backfill if we could not get 3 distinct topics
    if len(selected) < 3:
        random.shuffle(all_items)
        for item in all_items:
            if item.id not in {i.id for i in selected}:
                selected.append(item)
            if len(selected) == 3:
                break

    return RecallBundle(mode="high", items=selected[:3], prompt=HIGH_ENERGY_PROMPT)
