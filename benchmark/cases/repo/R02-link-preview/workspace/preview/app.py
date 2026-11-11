"""HTTP entry point for previews."""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from .fetch import extract, fetch_page

CARD = '<div class="card"><img src="{image}"><a href="{url}">{title}</a></div>'


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path != "/preview":
            self.send_response(404)
            self.end_headers()
            return
        target = parse_qs(url.query).get("url", [""])[0]
        try:
            info = extract(fetch_page(target))
        except Exception as exc:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(exc).encode())
            return
        card = CARD.format(image=info["image"], url=target, title=info["title"])
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(card.encode())


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
