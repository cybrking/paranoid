import socket
from contextlib import ExitStack
from unittest import mock

DNS = {
    "images.example.com": ["93.184.216.34"],
    "cdn.example.org": ["2606:2800:220:1:248:1893:25c8:1946"],
    "internal.example.com": ["10.0.0.7"],
    "rebind.example.com": ["93.184.216.34", "169.254.169.254"],
}


def fake_getaddrinfo(host, port, *args, **kwargs):
    host = host.strip("[]")
    try:
        socket.inet_pton(socket.AF_INET, host)
        addresses = [host]
    except OSError:
        try:
            socket.inet_pton(socket.AF_INET6, host)
            addresses = [host]
        except OSError:
            if host == "localhost":
                addresses = ["127.0.0.1"]
            elif host in DNS:
                addresses = DNS[host]
            else:
                raise socket.gaierror("unknown host " + host)
    out = []
    for addr in addresses:
        family = socket.AF_INET6 if ":" in addr else socket.AF_INET
        sockaddr = (addr, port or 0, 0, 0) if family == socket.AF_INET6 else (addr, port or 0)
        out.append((family, socket.SOCK_STREAM, 6, "", sockaddr))
    return out


class FakeNet:
    """Patch every way the code could reach the network and record what it tried."""

    def __init__(self, body=b"\x89PNG fake image"):
        self.body = body
        self.fetched = []
        self._stack = ExitStack()

    def _fetch(self, url, *args, **kwargs):
        self.fetched.append(str(url))
        return self.body

    def _urlopen(self, url, *args, **kwargs):
        target = getattr(url, "full_url", url)
        self.fetched.append(str(target))
        body = self.body

        class Response:
            status = 200
            headers = {"Content-Type": "image/png", "Content-Length": str(len(body))}

            def read(self, n=-1):
                return body if n is None or n < 0 else body[:n]

            def getheader(self, name, default=None):
                return self.headers.get(name, default)

            def geturl(self):
                return str(target)

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        return Response()

    def __enter__(self):
        import app.net
        self._stack.enter_context(mock.patch("socket.getaddrinfo", fake_getaddrinfo))
        self._stack.enter_context(mock.patch("socket.gethostbyname", lambda h: fake_getaddrinfo(h, 0)[0][4][0]))
        self._stack.enter_context(mock.patch.object(app.net, "fetch", self._fetch))
        self._stack.enter_context(mock.patch("urllib.request.urlopen", self._urlopen))
        self._stack.enter_context(mock.patch("socket.create_connection", side_effect=OSError("network disabled in tests")))
        return self

    def __exit__(self, *exc):
        self._stack.close()
        return False
