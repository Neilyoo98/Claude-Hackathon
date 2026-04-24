#!/usr/bin/env python3
"""
Quizlet-style study UI for LegiScope.

  cd c:\\civics
  python -m pip install -r requirements.txt
  python serve.py

Open http://127.0.0.1:5050
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from vault.dual_lens import dual_lens_for_item
from vault.ingest import refresh_database
from vault.lead_image import lead_image_url
from vault.models import CivicItem
from vault.preferences import apply_feedback, rank_personalized
from vault.storage import load_items

_ROOT = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(_ROOT / "web" / "templates"),
    static_folder=str(_ROOT / "web" / "static"),
    static_url_path="/static",
)


def _item_to_dict(item: CivicItem) -> dict:
    return item.to_dict()


@app.get("/")
def index():
    return render_template("dashboard.html")


@app.get("/api/items")
def api_items():
    items = load_items()
    rows = rank_personalized(items)
    return jsonify({"ok": True, "items": [_item_to_dict(i) for i in rows]})


@app.get("/api/image/<item_id>")
def api_image(item_id: str):
    items = load_items()
    item = items.get(item_id)
    if not item:
        return jsonify({"ok": False, "error": "Not found"}), 404
    try:
        url = lead_image_url(item)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True, "url": url})


@app.post("/api/feedback")
def api_feedback():
    data = request.get_json(silent=True) or {}
    item_id = data.get("item_id")
    signal = (data.get("signal") or "").strip().lower()
    if not item_id or signal not in ("interested", "not_interested"):
        return jsonify({"ok": False, "error": "item_id and signal (interested|not_interested) required"}), 400
    items = load_items()
    item = items.get(str(item_id))
    if not item:
        return jsonify({"ok": False, "error": "Not found"}), 404
    try:
        apply_feedback(item, signal)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True})


@app.post("/api/update")
def api_update():
    try:
        stats = refresh_database()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True, "stats": stats})


@app.get("/api/signal/<item_id>")
def api_signal(item_id: str):
    items = load_items()
    item = items.get(item_id)
    if not item:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify(
        {
            "ok": True,
            "item": _item_to_dict(item),
            "dual_lens": dual_lens_for_item(item),
        }
    )


if __name__ == "__main__":
    print("LegiScope — http://127.0.0.1:5050")
    app.run(host="127.0.0.1", port=5050, debug=False)
