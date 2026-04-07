from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from _kalshi_client import get_markets, get_series, enrich_markets_with_urls
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            params = parse_qs(urlparse(self.path).query)
            event_ticker = params.get("event_ticker", [None])[0]
            series_ticker = params.get("series_ticker", [None])[0]
            status = params.get("status", [None])[0]
            limit = int(params.get("limit", [200])[0])
            cursor = params.get("cursor", [None])[0]

            data = get_markets(
                event_ticker=event_ticker,
                series_ticker=series_ticker,
                status=status,
                limit=limit,
                cursor=cursor,
            )

            markets = data.get("markets", [])

            series_title = None
            if series_ticker:
                try:
                    s = get_series(series_ticker)
                    series_title = s.get("title", "")
                except Exception:
                    pass

            enrich_markets_with_urls(markets, series_ticker, series_title)
            data["markets"] = markets

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
