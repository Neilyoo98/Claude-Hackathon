from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from vault.config import CONGRESS_API_BASE, DEFAULT_CONGRESS, congress_api_key
from vault.ids import item_id_from_url
from vault.models import CivicItem
from vault.textclean import clean_plain_text
from vault.topics import classify_topic


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def congress_bill_public_url(congress: int, bill_type: str, number: str) -> str:
    bt = bill_type.upper()
    slug_map = {
        "HR": "house-bill",
        "S": "senate-bill",
        "HJRES": "house-joint-resolution",
        "SJRES": "senate-joint-resolution",
        "HCONRES": "house-concurrent-resolution",
        "SCONRES": "senate-concurrent-resolution",
        "HRES": "house-resolution",
        "SRES": "senate-resolution",
    }
    slug = slug_map.get(bt, "house-bill")
    return f"https://www.congress.gov/bill/{_ordinal(congress)}-congress/{slug}/{number}"


def fetch_congress_items(
    congress: int | None = None,
    bill_types: tuple[str, ...] = ("hr", "s"),
    limit_per_type: int = 25,
    timeout: int = 30,
) -> list[CivicItem]:
    api_key = congress_api_key()
    if not api_key:
        return []

    cong = congress or DEFAULT_CONGRESS
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    session = requests.Session()
    out: list[CivicItem] = []

    for btype in bill_types:
        url = f"{CONGRESS_API_BASE}/bill/{cong}/{btype}"
        params: dict[str, Any] = {
            "api_key": api_key,
            "format": "json",
            "limit": limit_per_type,
            "sort": "updateDate+desc",
        }
        try:
            r = session.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError):
            continue

        bills = data.get("bills") or []
        if isinstance(bills, dict):
            inner = bills.get("bill")
            bills = inner if isinstance(inner, list) else ([inner] if isinstance(inner, dict) else [])

        for row in bills:
            if not isinstance(row, dict):
                continue
            b = row.get("bill") if isinstance(row.get("bill"), dict) else row
            if not isinstance(b, dict):
                continue

            num = str(b.get("number") or b.get("billNumber") or "").strip()
            typ = str(b.get("type") or b.get("billType") or btype).strip().upper() or btype.upper()
            cong_val = b.get("congress")
            cong_use = (
                int(cong_val)
                if isinstance(cong_val, int) or (isinstance(cong_val, str) and str(cong_val).isdigit())
                else cong
            )
            if not num:
                continue

            title = clean_plain_text((b.get("title") or "").strip() or f"{typ} {num}")
            latest = b.get("latestAction") or {}
            if not isinstance(latest, dict):
                latest = {}
            action_text = clean_plain_text((latest.get("text") or "").strip())
            action_date = (latest.get("actionDate") or "").strip()
            intro = (b.get("introducedDate") or "").strip()
            date = action_date or intro or ""
            policy = b.get("policyArea") or {}
            policy_name = clean_plain_text((policy.get("name") or "").strip()) if isinstance(policy, dict) else ""
            parts = [p for p in (action_text, f"Introduced: {intro}" if intro else "") if p]
            summary = clean_plain_text(" — ".join(parts) if parts else title[:500], max_len=800)
            url_public = congress_bill_public_url(cong_use, typ, num)
            topic = classify_topic(f"{title}\n{summary}\n{policy_name}")

            out.append(
                CivicItem(
                    id=item_id_from_url(url_public),
                    title=title,
                    summary=summary,
                    source=f"Congress.gov — {typ} {num} ({cong_use})",
                    url=url_public,
                    date=date,
                    topic=topic,
                    kind="legislation",
                    fetched_at=now,
                )
            )
    return out
