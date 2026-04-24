from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ITEMS_PATH = DATA_DIR / "items.json"
ENV_PATH = ROOT / ".env"
DEFAULT_CONGRESS = 119
CONGRESS_API_BASE = "https://api.congress.gov/v3"

RSS_FEEDS = [
    ("Reuters Politics", "https://feeds.reuters.com/Reuters/PoliticsNews"),
    ("NPR Politics", "https://feeds.npr.org/1014/rss.xml"),
    ("AP Politics", "https://feeds.apnews.com/rss/apf-politics"),
    ("GovTrack", "https://www.govtrack.us/events/govtrack.rss"),
    ("OpenSecrets", "https://www.opensecrets.org/news/feed"),
]


def load_dotenv_file() -> None:
    if not ENV_PATH.exists():
        return
    try:
        text = ENV_PATH.read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            key = k.strip()
            if key and key not in os.environ:
                os.environ[key] = v.strip().strip('"').strip("'")


def congress_api_key() -> str | None:
    key = os.environ.get("CONGRESS_API_KEY")
    return key.strip() if key else None


load_dotenv_file()
