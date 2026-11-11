"""Fetch a page and pull out its title and image."""

import re
import urllib.request

TIMEOUT = 10


def fetch_page(url):
    request = urllib.request.Request(url, headers={"User-Agent": "link-preview/1.0"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read(2_000_000).decode("utf-8", "replace")


def extract(html):
    title = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    image = re.search(r'<meta property="og:image" content="([^"]+)"', html, re.I)
    return {
        "title": title.group(1).strip() if title else "",
        "image": image.group(1) if image else "",
    }
