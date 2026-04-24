from __future__ import annotations

BUCKETS: dict[str, list[str]] = {
    "climate": ["climate", "emissions", "carbon", "epa", "environment", "renewable"],
    "health": ["health", "medicare", "medicaid", "fda", "opioid", "mental health"],
    "economy": ["economy", "tax", "inflation", "gdp", "budget", "debt", "trade"],
    "defense": ["defense", "military", "pentagon", "nato", "veterans", "war"],
    "tech": ["tech", "ai", "artificial intelligence", "cyber", "data privacy"],
    "immigration": ["immigration", "border", "asylum", "visa", "daca", "migrant"],
    "justice": ["justice", "crime", "police", "court", "prison", "civil rights"],
    "education": ["education", "school", "student loan", "college", "curriculum"],
    "housing": ["housing", "rent", "eviction", "mortgage", "zoning", "hud"],
    "foreign policy": ["foreign", "diplomacy", "sanctions", "treaty", "un ", "nato"],
}


def classify_topic(text: str, fallback: str = "general") -> str:
    t = text.lower()
    for topic, keywords in BUCKETS.items():
        if any(kw in t for kw in keywords):
            return topic
    return fallback
