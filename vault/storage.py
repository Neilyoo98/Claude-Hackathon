from __future__ import annotations

import json

from vault.config import DATA_DIR, ITEMS_PATH
from vault.models import CivicItem


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_items() -> dict[str, CivicItem]:
    if not ITEMS_PATH.exists():
        return {}
    data = json.loads(ITEMS_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return {}
    out: dict[str, CivicItem] = {}
    for row in data:
        if isinstance(row, dict) and "id" in row:
            item = CivicItem.from_dict(row)
            out[item.id] = item
    return out


def save_items(items: dict[str, CivicItem]) -> None:
    ensure_data_dir()
    sorted_items = sorted(items.values(), key=lambda x: (x.date, x.title), reverse=True)
    ITEMS_PATH.write_text(
        json.dumps([i.to_dict() for i in sorted_items], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def merge_dedupe(existing: dict[str, CivicItem], incoming: list[CivicItem]) -> tuple[dict[str, CivicItem], int]:
    merges = 0
    for item in incoming:
        if item.id in existing:
            existing[item.id] = CivicItem.merge_item_fields(existing[item.id], item)
            merges += 1
        else:
            existing[item.id] = item
    return existing, merges
