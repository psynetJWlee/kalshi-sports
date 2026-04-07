from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib_kalshi_client import get_market


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
