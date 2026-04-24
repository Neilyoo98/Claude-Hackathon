"""Local personalization: reorder and soft-hide items from title keywords."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vault.config import DATA_DIR
from vault.keywords import extract_keywords
from vault.models import CivicItem

_PREFS_PATH = DATA_DIR / "user_prefs.json"


def _default_prefs() -> dict[str, Any]:
    return {"hidden_ids": [], "keyword_weights": {}}


def load_prefs() -> dict[str, Any]:
    if not _PREFS_PATH.is_file():
        return _default_prefs()
    try:
        data = json.loads(_PREFS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _default_prefs()
    if not isinstance(data, dict):
        return _default_prefs()
    hidden = data.get("hidden_ids")
    if not isinstance(hidden, list):
        hidden = []
    kw = data.get("keyword_weights")
    if not isinstance(kw, dict):
        kw = {}
    kw_clean = {str(k): float(v) for k, v in kw.items() if isinstance(v, (int, float))}
    return {"hidden_ids": [str(x) for x in hidden], "keyword_weights": kw_clean}


def save_prefs(prefs: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "hidden_ids": list(prefs.get("hidden_ids", [])),
        "keyword_weights": dict(prefs.get("keyword_weights", {})),
    }
    _PREFS_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def score_item(item: CivicItem, prefs: dict[str, Any]) -> float:
    weights: dict[str, float] = prefs.get("keyword_weights", {})
    s = 0.0
    for w in extract_keywords(item.title):
        s += float(weights.get(w, 0.0))
    return s


def rank_personalized(items: dict[str, CivicItem]) -> list[CivicItem]:
    prefs = load_prefs()
    hidden = set(prefs.get("hidden_ids", []))
    pool = [it for it in items.values() if it.id not in hidden]
    return sorted(
        pool,
        key=lambda it: (score_item(it, prefs), it.date or "", it.title),
        reverse=True,
    )


def apply_feedback(item: CivicItem, signal: str) -> dict[str, Any]:
    prefs = load_prefs()
    hidden: list[str] = list(prefs.get("hidden_ids", []))
    kw: dict[str, float] = dict(prefs.get("keyword_weights", {}))
    words = extract_keywords(item.title)

    if signal == "interested":
        for w in words:
            kw[w] = kw.get(w, 0.0) + 1.0
    elif signal == "not_interested":
        for w in words:
            kw[w] = kw.get(w, 0.0) - 1.25
        if item.id not in hidden:
            hidden.append(item.id)
    else:
        raise ValueError("signal must be interested or not_interested")

    prefs["hidden_ids"] = hidden
    prefs["keyword_weights"] = kw
    save_prefs(prefs)
    return prefs
