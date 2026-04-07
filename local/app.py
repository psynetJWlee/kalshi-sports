"""
Kalshi Sports Market Explorer - Flask Server
Run: cd local && python app.py
Open: http://localhost:5000
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify
from datetime import datetime, timezone
import kalshi_client as kc

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))


@app.route("/")
def index():
    return render_template("index.html")


# ─── API Proxy Endpoints ─────────────────────────────────

@app.route("/api/sports")
def api_sports():
    """Get available sport filters"""
    try:
        data = kc.get_filters_by_sport()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/series")
def api_series():
    """Get sports series list"""
    try:
        category = request.args.get("category", "Sports")
        series = kc.get_series_list(category=category)
        return jsonify({"series": series})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/milestones")
def api_milestones():
    """Get milestones (games) with filters"""
    try:
        category = request.args.get("category", "Sports")
        competition = request.args.get("competition", None)
        milestone_type = request.args.get("type", None)
        min_date = request.args.get("min_date", None)
        limit = int(request.args.get("limit", 100))
        cursor = request.args.get("cursor", None)

        data = kc.get_milestones(
            category=category,
            competition=competition,
            milestone_type=milestone_type,
            min_date=min_date,
            limit=limit,
            cursor=cursor,
        )
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/events")
def api_events():
    """Get events with nested markets"""
    try:
        series_ticker = request.args.get("series_ticker", None)
        status = request.args.get("status", None)
        with_markets = request.args.get("with_nested_markets", "true") == "true"
        with_milestones = request.args.get("with_milestones", "false") == "true"
        limit = int(request.args.get("limit", 200))
        cursor = request.args.get("cursor", None)

        data = kc.get_events(
            series_ticker=series_ticker,
            status=status,
            with_nested_markets=with_markets,
            with_milestones=with_milestones,
            limit=limit,
            cursor=cursor,
        )
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/markets")
def api_markets():
    """Get markets for a specific event, enriched with URLs"""
    try:
        event_ticker = request.args.get("event_ticker", None)
        series_ticker = request.args.get("series_ticker", None)
        status = request.args.get("status", None)
        limit = int(request.args.get("limit", 200))
        cursor = request.args.get("cursor", None)

        data = kc.get_markets(
            event_ticker=event_ticker,
            series_ticker=series_ticker,
            status=status,
            limit=limit,
            cursor=cursor,
        )

        markets = data.get("markets", [])

        # Try to get series info for URL building
        series_title = None
        if series_ticker:
            try:
                s = kc.get_series(series_ticker)
                series_title = s.get("title", "")
            except Exception:
                pass

        kc.enrich_markets_with_urls(markets, series_ticker, series_title)
        data["markets"] = markets

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/market/<ticker>")
def api_market_detail(ticker):
    """Get single market detail"""
    try:
        market = kc.get_market(ticker)
        return jsonify({"market": market})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("  Kalshi Sports Market Explorer")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
