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
