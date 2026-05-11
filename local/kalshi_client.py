"""
Kalshi API Client - Sports Market Explorer
Public endpoints only (no authentication required)
"""

import requests
import re
from datetime import datetime, timezone


BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

# Series title -> URL slug cache
_series_slug_cache = {}


def _get(endpoint, params=None):
    """Base GET request to Kalshi API"""
    url = f"{BASE_URL}{endpoint}"
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def slugify(text):
    """Convert series title to URL slug (kebab-case)"""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def build_market_url(series_ticker, series_title, market_ticker):
    """Build the Kalshi market page URL"""
    slug = slugify(series_title)
    return f"https://kalshi.com/markets/{series_ticker}/{slug}/{market_ticker}"


# ─── Series ──────────────────────────────────────────────

def get_series_list(category=None):
    """
    GET /series
    Get all series, optionally filtered by category (e.g. "Sports")
    """
    params = {}
    if category:
        params["category"] = category
    data = _get("/series", params)
    series_list = data.get("series", [])

    # cache slugs
    for s in series_list:
        _series_slug_cache[s["ticker"]] = slugify(s["title"])

    return series_list


def get_series(series_ticker):
    """GET /series/{series_ticker}"""
    data = _get(f"/series/{series_ticker}")
    s = data.get("series", {})
    if s:
        _series_slug_cache[s["ticker"]] = slugify(s["title"])
    return s


# ─── Sports Filters ─────────────────────────────────────

def get_filters_by_sport():
    """
    GET /search/filters_by_sport
    Returns available sport filters (competitions, scopes, etc.)
    """
    return _get("/search/filters_by_sport")


# ─── Sport Categorization ───────────────────────────────

# Maps Kalshi milestone `type` to a stable sport_category label.
# Authoritative because Kalshi sets `type` per milestone (e.g. basketball_game)
# rather than relying on free-text league names.
SPORT_BY_TYPE = {
    "basketball_game": "Basketball",
    "soccer_tournament_multi_leg": "Soccer",
    "soccer_game": "Soccer",
    "baseball_game": "Baseball",
    "hockey_match": "Hockey",
    "hockey_tournament": "Hockey",
    "football_game": "Football",
    "cricket_match": "Cricket",
    "afl_match": "Aussie Rules",
    "tennis_tournament_singles": "Tennis",
    "tennis_match": "Tennis",
    "boxing_match": "Combat Sports",
    "mma_match": "Combat Sports",
    "rugby_match": "Rugby",
    "lacrosse_match": "Lacrosse",
    "racing_tournament": "Racing",
    "squash_match": "Squash",
    "golf_tournament": "Golf",
}

# Secondary fallback: league name → sport, used when milestone `type` is
# generic (e.g. one_off_milestone) or missing.
SPORT_BY_LEAGUE = {
    # Basketball
    "NBA": "Basketball", "WNBA": "Basketball", "NCAAMB": "Basketball",
    "South Korea KBL": "Basketball", "EuroLeague": "Basketball",
    "EuroCup": "Basketball", "Chinese Basketball Association": "Basketball",
    "Japan B League": "Basketball", "Liga Nacional de Basquetbol": "Basketball",
    "Russia VTB United League": "Basketball", "Turkey BSL": "Basketball",
    "Adriatic ABA League": "Basketball", "Germany BBL": "Basketball",
    "FIBA Champions League": "Basketball", "FIBA Europe Cup": "Basketball",
    "Italy Serie A": "Basketball", "Greek Basketball League": "Basketball",
    "Israeli Super League": "Basketball", "LNB Elite": "Basketball",
    "Spain Liga ACB": "Basketball", "New Zealand NBL": "Basketball",
    # Baseball
    "MLB": "Baseball", "Korea KBO": "Baseball", "Japan NPB": "Baseball",
    "College Baseball": "Baseball",
    # Hockey
    "NHL": "Hockey", "AHL": "Hockey", "KHL": "Hockey", "SHL": "Hockey",
    "Czech Extraliga": "Hockey", "Finland Liiga": "Hockey",
    "Germany DEL": "Hockey", "Switzerland National League": "Hockey",
    # Football
    "NFL": "Football", "UFL": "Football", "College Football": "Football",
    # Cricket
    "IPL": "Cricket", "PSL": "Cricket", "T20 International": "Cricket",
    # Aussie Rules
    "AFL": "Aussie Rules",
}


def classify_sport(milestone_type, league=None):
    """
    Resolve a milestone's sport category.
    Priority: milestone.type (authoritative) → league name → 'Other'.
    """
    if milestone_type and milestone_type in SPORT_BY_TYPE:
        return SPORT_BY_TYPE[milestone_type]
    if league and league in SPORT_BY_LEAGUE:
        return SPORT_BY_LEAGUE[league]
    return "Other"


def enrich_milestones_with_sport(milestones):
    """Inject `sport_category` field into each milestone in-place."""
    for m in milestones:
        league = (m.get("details") or {}).get("league") or ""
        m["sport_category"] = classify_sport(m.get("type"), league)
    return milestones


# ─── Milestones (Games) ─────────────────────────────────

def get_milestones(category=None, competition=None, milestone_type=None,
                   min_date=None, limit=100, cursor=None):
    """
    GET /milestones
    Get milestone (game) list with filters.

    Args:
        category: "Sports", "Elections", "Esports", "Crypto"
        competition: "Pro Football", "Pro Basketball (M)", "Pro Baseball", etc.
        milestone_type: "football_game", "basketball_game", etc.
        min_date: RFC3339 date string or datetime object
        limit: 1-500
        cursor: pagination cursor
    """
    params = {"limit": limit}

    if category:
        params["category"] = category
    if competition:
        params["competition"] = competition
    if milestone_type:
        params["type"] = milestone_type
    if min_date:
        if isinstance(min_date, datetime):
            params["minimum_start_date"] = min_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            params["minimum_start_date"] = min_date
    if cursor:
        params["cursor"] = cursor

    return _get("/milestones", params)


# ─── Events ──────────────────────────────────────────────

def get_events(series_ticker=None, status=None, with_nested_markets=False,
               with_milestones=False, limit=200, cursor=None):
    """
    GET /events
    Get events with optional nested markets and milestones.
    """
    params = {"limit": limit}

    if series_ticker:
        params["series_ticker"] = series_ticker
    if status:
        params["status"] = status
    if with_nested_markets:
        params["with_nested_markets"] = "true"
    if with_milestones:
        params["with_milestones"] = "true"
    if cursor:
        params["cursor"] = cursor

    return _get("/events", params)


def get_event(event_ticker):
    """GET /events/{event_ticker}"""
    return _get(f"/events/{event_ticker}")


# ─── Markets ─────────────────────────────────────────────

def get_markets(event_ticker=None, series_ticker=None, status=None,
                tickers=None, limit=200, cursor=None):
    """
    GET /markets
    Get markets with various filters.
    """
    params = {"limit": limit}

    if event_ticker:
        params["event_ticker"] = event_ticker
    if series_ticker:
        params["series_ticker"] = series_ticker
    if status:
        params["status"] = status
    if tickers:
        params["tickers"] = tickers
    if cursor:
        params["cursor"] = cursor

    return _get("/markets", params)


def get_market(ticker):
    """GET /markets/{ticker}"""
    data = _get(f"/markets/{ticker}")
    return data.get("market", {})


# ─── URL Helper ──────────────────────────────────────────

def get_series_slug(series_ticker):
    """Get cached slug or fetch from API"""
    if series_ticker in _series_slug_cache:
        return _series_slug_cache[series_ticker]
    try:
        s = get_series(series_ticker)
        return slugify(s.get("title", series_ticker))
    except Exception:
        return series_ticker


def enrich_markets_with_urls(markets, series_ticker=None, series_title=None):
    """Add kalshi_url field to each market dict"""
    for m in markets:
        ticker = m.get("ticker", "")
        st = series_ticker or ticker.split("-")[0] if "-" in ticker else ""

        if series_title:
            slug = slugify(series_title)
        elif st:
            slug = get_series_slug(st)
        else:
            slug = ""

        if st and slug:
            m["kalshi_url"] = f"https://kalshi.com/markets/{st}/{slug}/{ticker}"
        else:
            m["kalshi_url"] = f"https://kalshi.com/markets/{ticker}"

    return markets
