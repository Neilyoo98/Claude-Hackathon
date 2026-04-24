

# Legiscope - Claude UMD Hackathon

> A Python CLI that pulls real legislative and civic signals, stores them locally, and resurfaces content based on your energy level — turning passive awareness into active civic engagement.

---

## What It Does

Most people don't follow legislation because it's inaccessible, overwhelming, or biased. Civic Signal Vault solves this by:

- **Aggregating** RSS civic feeds + U.S. Congress bills into a single local vault
- **Deduplicating** intelligently by canonical URL + SHA-256 fingerprint
- **Classifying** content into 10 policy topics without ML or API calls
- **Surfacing** content adaptively — one item when you're tired, three with a synthesis prompt when you're engaged
- **Staying offline-first** — no accounts, no cloud, full data ownership

---

## Features

| Feature | Description |
|---|---|
| Multi-source ingestion | RSS feeds + Congress.gov API (optional) |
| Local JSON vault | All data in `data/items.json`, fully yours |
| Smart deduplication | SHA-256 URL fingerprinting + field merging |
| Topic classification | 10 keyword-based buckets (climate, health, economy, ...) |
| Energy-adaptive recall | Low energy → 1 item. High energy → 3 items + synthesis prompt |
| Offline-first | Works without any API key via RSS alone |
| Windows-safe | UTF-8 stdout fix included |

---

## Project Structure

```
civic-signal-vault/
│
├── main.py                     # CLI entry point
├── requirements.txt            # feedparser, requests
├── .env.example                # API key template (never commit .env)
├── .gitignore
│
├── vault/
│   ├── __init__.py             # __version__ = "0.1.0"
│   ├── config.py               # Paths, feed list, env loading
│   ├── models.py               # CivicItem dataclass
│   ├── ids.py                  # URL normalization + SHA-256 IDs
│   ├── topics.py               # Keyword-based topic classifier
│   ├── storage.py              # JSON load / save / merge-dedupe
│   ├── ingest.py               # Orchestrates all fetchers
│   └── recall.py               # Low/high energy item selection
│
└── vault/fetchers/
    ├── __init__.py             # Re-exports fetch_rss_items, fetch_congress_items
    ├── rss_fetcher.py          # feedparser → CivicItem list
    └── congress.py             # Congress.gov API → CivicItem list
```

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/your-username/civic-signal-vault.git
cd civic-signal-vault
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. (Optional) Add a Congress.gov API key

```bash
cp .env.example .env
# Edit .env and add: CONGRESS_API_KEY=your_key_here
```

Get a free key at [api.congress.gov](https://api.congress.gov/sign-up/).

### 3. Run the guided wizard

```bash
python main.py wizard
```

This walks you through setup, writes your `.env`, fetches your first vault, and shows a sample recall.

---

## CLI Commands

```bash
# Guided first-run setup
python main.py wizard

# Refresh vault from all sources (save to disk)
python main.py update

# Recall one item (default: low energy)
python main.py recall

# Recall three items + synthesis prompt
python main.py recall --energy high

# Open recalled URLs in browser
python main.py recall --energy high --open-browser

# Fetch and preview without saving
python main.py preview

# Interactive mode: update then prompt for recall
python main.py interactive
```

---

## Data Model

Every item in the vault shares a single normalized shape:

```json
{
  "id": "sha256-hex-fingerprint",
  "title": "Senate passes $1.2T infrastructure bill",
  "summary": "The Senate voted 69-30 to pass...",
  "source": "Reuters Politics",
  "url": "https://reuters.com/...",
  "date": "2024-11-05T14:32:00",
  "topic": "economy",
  "kind": "legislation | rss | other",
  "fetched_at": "2025-04-24T09:00:00"
}
```

---

## Data Flow

```
┌─────────────┐   ┌──────────────────┐
│  RSS Feeds  │   │  Congress.gov API │
│  (feedparser)│   │  (optional key)   │
└──────┬──────┘   └────────┬─────────┘
       │                   │
       └──────────┬────────┘
                  ▼
          ┌──────────────┐
          │   ingest.py  │  collect_all()
          │  normalize → │  CivicItem list
          │  classify    │
          └──────┬───────┘
                 ▼
          ┌──────────────┐
          │  storage.py  │  merge_dedupe()
          │  load → merge│  SHA-256 dedup
          │  → save      │  sort by date
          └──────┬───────┘
                 ▼
          data/items.json
                 │
                 ▼
          ┌──────────────┐
          │   recall.py  │
          │  low energy  │  → 1 random recent item
          │  high energy │  → bill + rss + archive
          └──────────────┘  + synthesis prompt
```

---

## Topic Classification

Topics are assigned by keyword matching across title + summary — no ML, no network call, instant:

| Topic | Example Keywords |
|---|---|
| climate | climate, emissions, carbon, epa, renewable |
| health | health, medicare, fda, opioid, mental health |
| economy | tax, inflation, gdp, budget, debt, trade |
| defense | military, pentagon, nato, veterans |
| tech | ai, artificial intelligence, cyber, data privacy |
| immigration | border, asylum, visa, daca, migrant |
| justice | crime, police, court, prison, civil rights |
| education | school, student loan, college, curriculum |
| housing | rent, eviction, mortgage, zoning |
| foreign policy | diplomacy, sanctions, treaty, un, nato |

---

## Energy-Adaptive Recall

Civic Signal Vault adapts to how much mental bandwidth you have:

**Low Energy** — one item, randomly selected from the 20 most recent:
```
[1] FTC sues major pharmacy benefit managers over insulin pricing
    Reuters Politics | 2025-04-22 | #health
    https://reuters.com/...
```

**High Energy** — three items from distinct topics (prefers bill + RSS + archive) plus a synthesis prompt:
```
[1] Senate passes biotech IP protection act          #tech
[2] NIH funding cuts spark researcher exodus         #health
[3] Rural hospital closures reach 10-year high       #health (archived)

--- SYNTHESIS PROMPT ---
You're reading these 3 civic signals. What systemic pattern connects them?
Who benefits, who's burdened, and what would you ask your representative?
```

---

## Implementation Details

### Deduplication

Each item is fingerprinted by its canonical URL (scheme + lowercase netloc + stripped path, query and fragment dropped). The SHA-256 hex digest of this becomes the item `id`. On merge, the longer summary and newer `fetched_at` are kept.

### Congress.gov Integration

When `CONGRESS_API_KEY` is set, the fetcher hits `/v3/bill/{congress}` sorted by `updateDate`, maps each bill to a `CivicItem` with `kind=legislation`, and builds the public URL via:

```
https://www.congress.gov/{congress}/{billType}/{number}
```

Without a key, Congress fetching is skipped silently — the vault still works via RSS.

### .env Handling

`config.py` parses `.env` on import using a minimal `KEY=VALUE` parser. It **never overrides** environment variables that are already set (safe for CI/CD). `python-dotenv` is not required.

---

## Configuration

To add your own RSS feeds, edit `vault/config.py`:

```python
RSS_FEEDS = [
    ("Reuters Politics", "https://feeds.reuters.com/Reuters/PoliticsNews"),
    ("Your Feed Label", "https://your-feed-url/rss.xml"),
    # add as many as you like
]
```

To change the default Congress session:

```python
DEFAULT_CONGRESS = 119   # change to 118, 120, etc.
```

---

## Requirements

```
feedparser>=6.0
requests>=2.28
```

Python 3.10+ required (uses `str | None` union syntax).

---

## Privacy

- No data leaves your machine unless you enable Congress.gov API calls
- `data/` is gitignored — your vault never gets committed
- No telemetry, no analytics, no accounts

---

## Roadmap

- [ ] `vault/graph.py` — export cause-effect JSON graph from high-energy recalls
- [ ] `--topic` filter flag on recall commands
- [ ] SQLite backend option for larger vaults
- [ ] Web UI (optional, local-only) for graph visualization
- [ ] Legislation → impact mapping (policy actions → societal effects → stakeholders)

---

## License

MIT — see [LICENSE](LICENSE).
