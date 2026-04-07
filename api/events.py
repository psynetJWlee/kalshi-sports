from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib_kalshi_client import get_events


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            params = parse_qs(urlparse(self.path).query)
            series_ticker = params.get("series_ticker", [None])[0]
            status = params.get("status", [None])[0]
            with_markets = params.get("with_nested_markets", ["true"])[0] == "true"
            with_milestones = params.get("with_milestones", ["false"])[0] == "true"
            limit = int(params.get("limit", [200])[0])
            cursor = params.get("cursor", [None])[0]

            data = get_events(
                series_ticker=series_ticker,
                status=status,
                with_nested_markets=with_markets,
                with_milestones=with_milestones,
                limit=limit,
                cursor=cursor,
            )

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
