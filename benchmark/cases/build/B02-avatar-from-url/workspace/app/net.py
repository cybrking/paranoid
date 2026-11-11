"""Thin network helpers so the rest of the app doesn't import urllib directly."""

import socket
import urllib.request


def resolve(host):
    """Return the IP addresses a hostname resolves to."""
    return sorted({info[4][0] for info in socket.getaddrinfo(host, None)})


def fetch(url, timeout=5):
    """Download a URL and return the body bytes."""
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read()
