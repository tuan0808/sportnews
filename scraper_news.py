"""
scraper_news.py

Fetch league-wide and team-specific news from ESPN.

Endpoints:
  - League news:  http://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/news
  - Team news:    http://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{id}/news
"""

import sys
from pathlib import Path

_backend_dir = str(Path(__file__).resolve().parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from scraper import (
    ESPN_BASE, _espn_path, espn_fetch,
    cache_get, cache_set, _post_json,
)

# ── ESPN Team ID Maps ─────────────────────────────────────────────────────────

ESPN_TEAM_IDS = {
    "nfl": {
        "ARI": 22, "ATL": 1,  "BAL": 33, "BUF": 2,  "CAR": 29, "CHI": 3,
        "CIN": 4,  "CLE": 5,  "DAL": 6,  "DEN": 7,  "DET": 8,  "GB": 9,
        "HOU": 34, "IND": 11, "JAX": 30, "KC": 12,  "LV": 13,  "LAC": 24,
        "LAR": 14, "MIA": 15, "MIN": 16, "NE": 17,  "NO": 18,  "NYG": 19,
        "NYJ": 20, "PHI": 21, "PIT": 23, "SF": 25,  "SEA": 26, "TB": 27,
        "TEN": 10, "WAS": 28,
    },
    "nba": {
        "ATL": 1,  "BOS": 2,  "BKN": 17, "CHA": 30, "CHI": 4,  "CLE": 5,
        "DAL": 6,  "DEN": 7,  "DET": 8,  "GSW": 9,  "HOU": 10, "IND": 11,
        "LAC": 12, "LAL": 13, "MEM": 29, "MIA": 14, "MIL": 15, "MIN": 16,
        "NOP": 3,  "NYK": 18, "OKC": 25, "ORL": 19, "PHI": 20, "PHX": 21,
        "POR": 22, "SAC": 23, "SAS": 24, "TOR": 28, "UTA": 26, "WAS": 27,
    },
    "mlb": {
        "ARI": 29, "ATL": 15, "BAL": 1,  "BOS": 2,  "CHC": 16, "CWS": 4,
        "CIN": 17, "CLE": 5,  "COL": 27, "DET": 6,  "HOU": 18, "KC": 7,
        "LAA": 3,  "LAD": 19, "MIA": 28, "MIL": 8,  "MIN": 9,  "NYM": 21,
        "NYY": 10, "OAK": 11, "PHI": 22, "PIT": 23, "SD": 25,  "SF": 26,
        "SEA": 12, "STL": 24, "TB": 30,  "TEX": 13, "TOR": 14, "WSH": 20,
    },
    "nhl": {
        "ANA": 25, "ARI": 24, "BOS": 1,  "BUF": 2,  "CGY": 20, "CAR": 7,
        "CHI": 4,  "COL": 17, "CBJ": 29, "DAL": 9,  "DET": 5,  "EDM": 22,
        "FLA": 26, "LA": 8,   "MIN": 30, "MTL": 8,  "NSH": 18, "NJ": 1,
        "NYI": 2,  "NYR": 3,  "OTT": 9,  "PHI": 10, "PIT": 5,  "SJ": 28,
        "SEA": 55, "STL": 19, "TB": 14,  "TOR": 10, "UTAH": 57,"VAN": 23,
        "VGK": 54, "WPG": 52, "WSH": 15,
    },
    "ncaab": {
        "AAMU": 2010, "ACU": 2000,  "AF": 2005,  "AKR": 2006,  "ALA": 333,   "ALCN": 2016,
        "ALST": 2011, "AMCC": 357,  "AMER": 44,  "APP": 2026,  "APSU": 2046, "ARIZ": 12,
        "ARK": 8,     "ARMY": 349,  "ARST": 2032,"ASU": 9,     "AUB": 2,     "BALL": 2050,
        "BAY": 239,   "BC": 103,    "BCU": 2065, "BEL": 2057,  "BELL": 91,   "BGSU": 189,
        "BING": 2066, "BOIS": 68,   "BRAD": 71,  "BRWN": 225,  "BU": 104,    "BUCK": 2083,
        "BUF": 2084,  "BUT": 2086,  "BYU": 252,  "CAL": 25,    "CAM": 2097,  "CAN": 2099,
        "CARK": 2110, "CCSU": 2115, "CCU": 324,  "CHSO": 2127, "CHST": 2130, "CIN": 2132,
        "CLE": 325,   "CLEM": 228,  "CMU": 2117, "COFC": 232,  "COLG": 2142, "COLO": 38,
        "COLU": 171,  "CONN": 41,   "COPP": 2154,"COR": 172,   "CP": 13,     "CREI": 156,
        "CSU": 36,    "DART": 159,  "DAV": 2166, "DAY": 2168,  "DEL": 48,    "DEP": 305,
        "DSU": 2169,  "DUKE": 150,  "ECU": 151,  "EVAN": 339,  "EWU": 331,   "FAMU": 50,
        "FDU": 161,   "FGCU": 526,  "FLA": 57,   "FRES": 278,  "FSU": 52,    "FUR": 231,
        "GASO": 290,  "GT": 59,     "GTWN": 46,  "GW": 45,     "HARV": 108,  "HAW": 62,
        "HC": 107,    "HOU": 248,   "HOW": 47,   "IDHO": 70,   "IDST": 304,  "ILL": 356,
        "INST": 282,  "IONA": 314,  "ISU": 66,   "IU": 84,     "IUIN": 85,   "JAX": 294,
        "JMU": 256,   "JXST": 55,   "KC": 140,   "KENN": 338,  "LAF": 322,   "LBSU": 299,
        "LIP": 288,   "LOU": 97,    "LR": 2031,  "LSU": 99,    "M-OH": 193,  "MARQ": 269,
        "MASS": 113,  "MD": 120,    "ME": 311,   "MEM": 235,   "MICH": 130,  "MILW": 270,
        "MINN": 135,  "MISS": 145,  "MIZ": 142,  "MONT": 149,  "MRSH": 276,  "MSM": 116,
        "MSST": 344,  "MSU": 127,   "MTST": 147, "MUR": 93,    "NCSU": 152,  "ND": 87,
        "NE": 111,    "NEB": 158,   "NIA": 315,  "NKU": 94,    "NMSU": 166,  "NU": 77,
        "ODU": 295,   "OHIO": 195,  "OKST": 197, "ORST": 204,  "ORU": 198,   "OSU": 194,
        "OU": 201,    "PAC": 279,   "PENN": 219, "PITT": 221,  "PRIN": 163,  "PSU": 213,
        "RGV": 292,   "RICE": 242,  "RICH": 257, "RUTG": 164,  "SAC": 16,    "SBU": 179,
        "SDAK": 233,  "SDSU": 21,   "SIU": 79,   "SJSU": 23,   "SLU": 139,   "STAN": 24,
        "STET": 56,   "STO": 284,   "SUU": 253,  "SYR": 183,   "TA&M": 245,  "TEM": 218,
        "TEX": 251,   "TLSA": 202,  "TOW": 119,  "TXST": 326,  "UAB": 5,     "UALB": 399,
        "UAPB": 2029, "UCD": 302,   "UCF": 2116, "UCI": 300,   "UCLA": 26,   "UCR": 27,
        "UCSD": 28,   "UGA": 61,    "UIC": 82,   "UK": 96,     "UL": 309,    "UNC": 153,
        "UNCW": 350,  "UND": 155,   "UNH": 160,  "UNM": 167,   "UNT": 249,   "URI": 227,
        "USA": 6,     "USC": 30,    "USD": 301,  "USF": 58,    "USU": 328,   "UTA": 250,
        "UTAH": 254,  "UTC": 236,   "UVA": 258,  "UVM": 261,   "VAN": 238,   "VILL": 222,
        "VT": 259,    "WAKE": 154,  "WASH": 264, "WIS": 275,   "WKU": 98,    "WSU": 265,
        "WVU": 277,   "YALE": 43,
    },
    "ncaaf": {
        "AMH": 7,     "ANN": 15,    "ARIZ": 12,  "ARK": 8,     "ASH": 308,   "ASU": 9,
        "AUB": 2,     "AUG": 124,   "BAL": 188,  "BAT": 121,   "BAY": 239,   "BC": 103,
        "BEL": 266,   "BGSU": 189,  "BOIS": 68,  "BRST": 18,   "BRWN": 225,  "BST": 132,
        "BUENA": 63,  "BYU": 252,   "CAL": 25,   "CAR": 32,    "CAS": 293,   "CHI": 80,
        "CLA": 17,    "CLEM": 228,  "COLBY": 33, "COLO": 38,   "COLU": 171,  "CONN": 41,
        "COR": 172,   "CP": 13,     "CSU": 36,   "CUR": 40,    "DART": 159,  "DEF": 190,
        "DEL": 48,    "DEP": 83,    "DUB": 49,   "DUKE": 150,  "ECU": 151,   "ELM": 72,
        "EUR": 101,   "FAMU": 50,   "FITCH": 114,"FLA": 57,    "FRES": 278,  "FSU": 52,
        "FUR": 231,   "GASO": 290,  "GRI": 65,   "GRO": 146,   "GT": 59,     "GTWN": 46,
        "GVSU": 125,  "HAM": 297,   "HAR": 173,  "HARV": 108,  "HAW": 62,    "HBRT": 174,
        "HC": 107,    "HEI": 191,   "HOU": 248,  "HOW": 47,    "IDHO": 70,   "IDST": 304,
        "ILLWES": 306,"INST": 282,  "ISU": 66,   "ITH": 175,   "IU": 84,     "JHU": 118,
        "JMU": 256,   "JUN": 246,   "JXST": 55,  "KAL": 126,   "KIN": 247,   "KNO": 255,
        "LAK": 262,   "LAW": 268,   "LHU": 209,  "LIN": 203,   "LOR": 263,   "LOU": 97,
        "LSU": 99,    "LUT": 67,    "M-OH": 193, "MAI": 274,   "MAMARI": 110,"MASS": 113,
        "MCM": 241,   "MD": 120,    "MEM": 235,  "MESA": 11,   "MICH": 130,  "MIL": 74,
        "MINN": 135,  "MISS": 145,  "MIT": 109,  "MIZ": 142,   "MONT": 149,  "MOR": 60,
        "MOW": 137,   "MRSH": 276,  "MSU": 127,  "MTH": 291,   "MTST": 147,  "MUR": 93,
        "NCSU": 152,  "ND": 87,     "NEB": 158,  "NMI": 128,   "NMSU": 166,  "NOR": 196,
        "NORTH": 286, "NU": 77,     "NWMS": 138, "ODU": 295,   "OHIO": 195,  "OKST": 197,
        "OLAF": 133,  "ORST": 204,  "OSU": 194,  "OU": 201,    "PAC": 205,   "PENN": 219,
        "PIKEV": 95,  "PITT": 221,  "PRIN": 163, "PST": 90,    "PSU": 213,   "RED": 29,
        "RICE": 242,  "RICH": 257,  "ROC": 184,  "ROSEHUL": 86,"RUTG": 164,  "SAC": 16,
        "SAGI": 129,  "SDAK": 233,  "SDSU": 21,  "SEOS": 199,  "SEU": 267,   "SIU": 79,
        "SJSU": 23,   "SPR": 81,    "SRU": 215,  "STAN": 24,   "STET": 56,   "STN": 200,
        "STO": 284,   "SUS": 216,   "SUU": 253,  "SYR": 183,   "TA&M": 245,  "TEM": 218,
        "TEX": 251,   "TLSA": 202,  "TOW": 119,  "TUF": 112,   "UAB": 5,     "UCD": 302,
        "UCLA": 26,   "UGA": 61,    "UK": 96,    "UL": 309,    "UMD": 134,   "UNC": 153,
        "UND": 155,   "UNH": 160,   "UNM": 167,  "UNNY": 237,  "UNT": 249,   "URI": 227,
        "USA": 6,     "USC": 30,    "USD": 301,  "USF": 58,    "UTAH": 254,  "UTC": 236,
        "UVA": 258,   "VAN": 238,   "VILL": 222, "VT": 259,    "WAB": 89,    "WAKE": 154,
        "WASH": 264,  "WAY": 131,   "WES": 223,  "WIPL": 272,  "WIS": 275,   "WISO": 271,
        "WKU": 98,    "WSTL": 143,  "WSU": 265,  "WVU": 277,   "YALE": 43,
    },
}

CACHE_TTL_NEWS = 900  # 15 minutes
MAJOR_LEAGUES  = ["nfl", "nba", "mlb", "nhl", "ncaab", "ncaaf"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_articles(raw_articles: list) -> list:
    """Normalise ESPN article objects into a flat, consistent shape."""
    articles = []
    for item in raw_articles:
        images = item.get("images", [])
        image_url = images[0].get("url", "") if images else ""

        categories = item.get("categories", [])
        teams = [
            c.get("team", {}).get("abbreviation", "")
            for c in categories
            if c.get("type") == "team" and c.get("team")
        ]

        articles.append({
            "id":          item.get("dataSourceIdentifier", item.get("id", "")),
            "headline":    item.get("headline", ""),
            "description": item.get("description", ""),
            "published":   item.get("published", ""),
            "lastModified":item.get("lastModified", ""),
            "author":      item.get("byline", ""),
            "url":         item.get("links", {}).get("web", {}).get("href", ""),
            "imageUrl":    image_url,
            "teams":       teams,
            "type":        item.get("type", ""),
        })
    return articles


# ── League-wide news ──────────────────────────────────────────────────────────

def scrape_league_news(league: str, limit: int = 50) -> dict | None:
    """Fetch the latest news for an entire league."""
    cached = cache_get("league_news", league, ttl=CACHE_TTL_NEWS)
    if cached:
        return cached

    path = _espn_path(league)
    url  = f"{ESPN_BASE}/{path}/news?limit={limit}"

    data = espn_fetch(url)
    if not data:
        return None

    try:
        articles = _parse_articles(data.get("articles", []))
        result = {
            "league":    league,
            "articles":  articles,
            "fetchedAt": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
        }
        cache_set("league_news", league, data=result)
        return result

    except Exception as e:
        print(f"    [!] League news parse error {league}: {e}")
        return None


# ── Team news ─────────────────────────────────────────────────────────────────

def scrape_team_news(league: str, team_abbr: str, limit: int = 25) -> dict | None:
    """Fetch the latest news for a specific team."""
    espn_id = ESPN_TEAM_IDS.get(league, {}).get(team_abbr.upper())
    if not espn_id:
        print(f"    [!] No ESPN ID for {league}/{team_abbr}")
        return None

    cached = cache_get("team_news", league, team_abbr, ttl=CACHE_TTL_NEWS)
    if cached:
        return cached

    path = _espn_path(league)
    url  = f"{ESPN_BASE}/{path}/teams/{espn_id}/news?limit={limit}"

    data = espn_fetch(url)
    if not data:
        return None

    try:
        articles = _parse_articles(data.get("articles", []))
        result = {
            "league":    league,
            "teamAbbr":  team_abbr.upper(),
            "articles":  articles,
            "fetchedAt": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
        }
        cache_set("team_news", league, team_abbr, data=result)
        return result

    except Exception as e:
        print(f"    [!] Team news parse error {league}/{team_abbr}: {e}")
        return None


# ── Push helpers ──────────────────────────────────────────────────────────────

def push_league_news(league: str, data: dict):
    ok    = _post_json("/api/ingest/league-news", {"league": league, "data": data})
    count = len(data.get("articles", []))
    status = "✓" if ok else "✗"
    print(f"    {status} {league.upper()} news: {count} articles")


def push_team_news(league: str, team_abbr: str, data: dict):
    ok    = _post_json("/api/ingest/team-news", {"league": league, "teamAbbr": team_abbr, "data": data})
    count = len(data.get("articles", []))
    status = "✓" if ok else "✗"
    print(f"    {status} {league.upper()} {team_abbr} news: {count} articles")


# ── Run functions ─────────────────────────────────────────────────────────────

def run_league_news():
    """Scrape and push league-wide news for all major leagues."""
    from datetime import datetime
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scraping league news...")
    for league in MAJOR_LEAGUES:
        data = scrape_league_news(league)
        if data:
            push_league_news(league, data)


def run_team_news():
    """Scrape and push team news for every team in every major league."""
    from datetime import datetime
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scraping team news...")
    for league in MAJOR_LEAGUES:
        ids = ESPN_TEAM_IDS.get(league, {})
        print(f"  {league.upper()}: {len(ids)} teams")
        for abbr in ids:
            data = scrape_team_news(league, abbr)
            if data:
                push_team_news(league, abbr, data)


# ── Standalone runner ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    COMMANDS = {
        "league": run_league_news,
        "teams":  run_team_news,
        "all":    lambda: (run_league_news(), run_team_news()),
    }

    if len(sys.argv) > 1 and sys.argv[1] in COMMANDS:
        COMMANDS[sys.argv[1]]()
    else:
        print("Usage: python3 scraper_news.py [league|teams|all]")
        print("  league  — fetch news for each league (NFL, NBA, MLB, NHL)")
        print("  teams   — fetch news for every individual team")
        print("  all     — both of the above")
