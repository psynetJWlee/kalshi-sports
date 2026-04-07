from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from _kalshi_client import get_series_list


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            params = parse_qs(urlparse(self.path).query)
            category = params.get("category", ["Sports"])[0]

            series = get_series_list(category=category)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"series": series}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
