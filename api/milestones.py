from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from _kalshi_client import get_milestones
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            params = parse_qs(urlparse(self.path).query)
            category = params.get("category", [None])[0]
            competition = params.get("competition", [None])[0]
            milestone_type = params.get("type", [None])[0]
            min_date = params.get("min_date", [None])[0]
            limit = int(params.get("limit", [100])[0])
            cursor = params.get("cursor", [None])[0]

            data = get_milestones(
                category=category,
                competition=competition,
                milestone_type=milestone_type,
                min_date=min_date,
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
