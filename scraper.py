"""
scraper.py — shared utilities for ESPN news scraping.
Provides HTTP fetching, caching, and push helpers.
"""

import json
import time
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────

ESPN_BASE = "http://site.api.espn.com/apis/site/v2/sports"

# Where to POST scraped data (your backend API)
NEXT_URL     = "https://api.sharpedgy.com"   # ← change to your backend URL
POST_HEADERS = {"Content-Type": "application/json"}

# Local cache directory
CACHE_DIR = Path(__file__).resolve().parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Maps league name → ESPN sport/league URL path
LEAGUE_CONFIG = {
    "nfl": "football/nfl",
    "nba": "basketball/nba",
    "mlb": "baseball/mlb",
    "nhl": "hockey/nhl",
    "ncaaf": "football/college-football",
    "ncaab": "basketball/mens-college-basketball",
}


# ── URL helpers ───────────────────────────────────────────────────────────────

def _espn_path(league: str) -> str:
    """Return the ESPN URL path segment for a league, e.g. 'football/nfl'."""
    path = LEAGUE_CONFIG.get(league.lower())
    if not path:
        raise ValueError(f"Unknown league: {league}")
    return path


# ── HTTP fetch ────────────────────────────────────────────────────────────────

def espn_fetch(url: str, retries: int = 3, timeout: int = 30) -> dict | None:
    """GET a URL and return parsed JSON, with retries."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            print(f"    [!] HTTP error {e} — {url}")
            return None
        except requests.exceptions.RequestException as e:
            wait = 2 ** attempt
            print(f"    [!] Fetch error (attempt {attempt+1}/{retries}): {e} — retrying in {wait}s")
            time.sleep(wait)
    print(f"    [!] All retries failed: {url}")
    return None


# ── Cache helpers ─────────────────────────────────────────────────────────────

def _cache_path(*parts: str) -> Path:
    """Build a deterministic cache file path from key parts."""
    key  = "_".join(str(p) for p in parts if p)
    slug = key.replace("/", "-").replace(" ", "_").lower()
    # Keep filenames short by hashing if too long
    if len(slug) > 80:
        slug = hashlib.md5(slug.encode()).hexdigest()
    return CACHE_DIR / f"{slug}.json"


def cache_get(*parts: str, ttl: int = 3600) -> dict | None:
    """Return cached data if it exists and is fresher than ttl seconds."""
    path = _cache_path(*parts)
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > ttl:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def cache_set(*parts: str, data: dict):
    """Write data to the cache as JSON."""
    path = _cache_path(*parts)
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"    [!] Cache write error: {e}")


# ── Safe nested dict access ───────────────────────────────────────────────────

def safe_get(obj: dict, *keys, default=None):
    """Safely traverse nested dicts/lists without raising KeyError."""
    cur = obj
    for key in keys:
        if isinstance(cur, dict):
            cur = cur.get(key)
        elif isinstance(cur, list) and isinstance(key, int):
            cur = cur[key] if key < len(cur) else None
        else:
            return default
        if cur is None:
            return default
    return cur


# ── Push to backend ───────────────────────────────────────────────────────────

def _post_json(endpoint: str, payload: dict) -> bool:
    """POST JSON payload to your backend API. Returns True on success."""
    url = f"{NEXT_URL}{endpoint}"
    try:
        resp = requests.post(url, json=payload, headers=POST_HEADERS, timeout=30)
        resp.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"    [!] POST failed {endpoint}: {e}")
        return False
