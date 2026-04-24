from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from vault.textclean import clean_plain_text


@dataclass
class CivicItem:
    id: str
    title: str
    summary: str
    source: str
    url: str
    date: str  # ISO 8601
    topic: str
    kind: Literal["legislation", "rss", "other"]
    fetched_at: str  # ISO 8601

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CivicItem:
        return cls(
            id=str(d["id"]),
            title=clean_plain_text(str(d.get("title", ""))),
            summary=clean_plain_text(str(d.get("summary", ""))),
            source=str(d.get("source", "")),
            url=str(d.get("url", "")),
            date=str(d.get("date", "")),
            topic=str(d.get("topic", "general")),
            kind=d.get("kind", "other"),  # type: ignore[arg-type]
            fetched_at=str(d.get("fetched_at", "")),
        )

    @staticmethod
    def merge_item_fields(existing: CivicItem, incoming: CivicItem) -> CivicItem:
        summary = (
            incoming.summary
            if len(incoming.summary) > len(existing.summary)
            else existing.summary
        )
        return CivicItem(
            id=existing.id,
            title=incoming.title or existing.title,
            summary=summary,
            source=incoming.source or existing.source,
            url=incoming.url or existing.url,
            date=incoming.date or existing.date,
            topic=incoming.topic or existing.topic,
            kind=incoming.kind,
            fetched_at=max(existing.fetched_at, incoming.fetched_at),
        )
