"""Tiny router over the handlers. Sessions come from the Authorization header."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from . import auth, handlers


class Handler(BaseHTTPRequestHandler):
    def _session(self):
        token = self.headers.get("Authorization", "").removeprefix("Bearer ")
        return auth.read_session(token)

    def _send(self, status, payload):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        session = self._session()
        if not session:
            return self._send(401, {"error": "sign in"})
        url = urlparse(self.path)
        try:
            if url.path == "/notes":
                return self._send(200, handlers.list_notes(session))
            if url.path.startswith("/notes/"):
                return self._send(200, handlers.get_note(session, url.path.split("/")[2]))
        except handlers.HttpError as err:
            return self._send(err.status, {"error": str(err)})
        self._send(404, {"error": "not found"})

    def do_DELETE(self):
        session = self._session()
        if not session:
            return self._send(401, {"error": "sign in"})
        url = urlparse(self.path)
        try:
            if url.path.startswith("/notes/"):
                handlers.delete_note(session, url.path.split("/")[2])
                return self._send(204, {})
            if url.path.startswith("/members/"):
                handlers.remove_member(session, url.path.split("/")[2])
                return self._send(204, {})
        except handlers.HttpError as err:
            return self._send(err.status, {"error": str(err)})
        self._send(404, {"error": "not found"})


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
