from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import json
from _kalshi_client import get_market
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Extract ticker from path: /api/market/{ticker}
            path = urlparse(self.path).path
            ticker = path.rstrip("/").split("/")[-1]

            market = get_market(ticker)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"market": market}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
