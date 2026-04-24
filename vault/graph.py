"""Simple causal-style graph payload for LegisGraph (client renders with vis-network)."""

from __future__ import annotations

from typing import Any

from vault.models import CivicItem


def build_legis_graph(item: CivicItem) -> dict[str, Any]:
    """
    Return nodes/edges for a small policy → impact diagram.
    Groups map to UI colors: policy, system, impact, uncertainty.
    """
    title = item.title.strip() or "Policy signal"
    label = title if len(title) <= 56 else title[:53] + "…"

    nodes = [
        {"id": "n_policy", "label": label, "group": "policy"},
        {"id": "n_impact", "label": "Public outcomes", "group": "impact"},
        {"id": "n_system", "label": "Institutions & delivery", "group": "system"},
        {"id": "n_uncert", "label": "Open questions / debate", "group": "uncertainty"},
    ]
    edges = [
        {"from": "n_policy", "to": "n_impact", "label": "may affect"},
        {"from": "n_policy", "to": "n_system", "label": "shapes"},
        {"from": "n_uncert", "to": "n_policy", "label": "conditions"},
    ]
    return {"nodes": nodes, "edges": edges}
