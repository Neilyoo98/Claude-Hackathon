from __future__ import annotations

import hashlib
from urllib.parse import urlparse, urlunparse


def canonical_url(url: str) -> str:
    p = urlparse(url.strip())
    return urlunparse((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), "", "", ""))


def item_id_from_url(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode()).hexdigest()
