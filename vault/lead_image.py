"""Resolve a lead image: Open Graph / Twitter from source URL, with cache + title fallback."""

from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from vault.config import DATA_DIR
from vault.keywords import extract_keywords
from vault.models import CivicItem

_CACHE_PATH = DATA_DIR / "image_cache.json"
_SESSION = requests.Session()
_SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
)


def _load_cache() -> dict[str, str]:
    if not _CACHE_PATH.is_file():
        return {}
    try:
        data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {str(k): str(v) for k, v in data.items() if isinstance(k, str) and isinstance(v, str)}


def _save_cache(cache: dict[str, str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(cache, indent=0, ensure_ascii=False) + "\n", encoding="utf-8")


def _abs_url(base: str, candidate: str | None) -> str | None:
    if not candidate or not candidate.strip():
        return None
    c = candidate.strip()
    if c.startswith("//"):
        return "https:" + c
    if c.startswith("http://") or c.startswith("https://"):
        return c
    try:
        return urljoin(base, c)
    except Exception:
        return None


def _pick_meta_image(soup: BeautifulSoup, base_url: str) -> str | None:
    keys = {"og:image", "og:image:url", "twitter:image", "twitter:image:src"}
    for tag in soup.find_all("meta"):
        prop = (tag.get("property") or "").strip().lower()
        name = (tag.get("name") or "").strip().lower()
        key = prop or name
        if key not in keys:
            continue
        u = _abs_url(base_url, tag.get("content"))
        if u:
            return u
    for link in soup.find_all("link", href=True):
        rel = link.get("rel")
        rels = rel if isinstance(rel, list) else ([rel] if rel else [])
        if any(str(r).lower() == "image_src" for r in rels):
            u = _abs_url(base_url, link.get("href"))
            if u:
                return u
    return None


def _scrape_og(url: str, timeout: int = 12) -> str | None:
    if not url or not urlparse(url).scheme.startswith("http"):
        return None
    try:
        r = _SESSION.get(url, timeout=timeout, allow_redirects=True, stream=True)
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or "").lower()
        if "html" not in ctype and "xml" not in ctype:
            return None
        chunk = b""
        for part in r.iter_content(chunk_size=65536):
            chunk += part
            if len(chunk) >= 1_200_000 or b"</head>" in chunk.lower():
                break
        text = chunk.decode("utf-8", errors="replace")
        soup = BeautifulSoup(text, "html.parser")
        return _pick_meta_image(soup, r.url)
    except Exception:
        return None


def _fallback_image_url(title: str) -> str:
    """Deterministic image loosely tied to title keywords (no external scrape)."""
    seed = hashlib.sha256((title or "signal").encode("utf-8")).hexdigest()[:16]
    words = extract_keywords(title or "")
    if words:
        seed = hashlib.sha256(("|".join(words[:5])).encode("utf-8")).hexdigest()[:16]
    return f"https://picsum.photos/seed/{seed}/960/540"


def lead_image_url(item: CivicItem, *, bust_cache: bool = False) -> str:
    """
    Return HTTPS URL for cover image. Uses JSON cache keyed by item id.
    Tries OG/Twitter from item.url, then keyword-seeded placeholder.
    """
    cache = _load_cache()
    if not bust_cache and item.id in cache:
        return cache[item.id]

    scraped = _scrape_og(item.url) if item.url else None
    if scraped and re.match(r"^https?://", scraped, re.I):
        final = scraped
    else:
        final = _fallback_image_url(item.title)

    cache[item.id] = final
    _save_cache(cache)
    return final
