#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["trafilatura"]
# ///
"""Fetch a URL and extract main article text via trafilatura.

Usage:
    uv run scripts/fetch_url.py <URL>

Uses urllib with browser headers (bypasses 403 blocks),
then trafilatura for content extraction (strips nav/ads/footers).
"""

import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

import trafilatura


def fetch(url: str, timeout: int = 15) -> str | None:
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8",
    })
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="replace")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run scripts/fetch_url.py <URL>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    try:
        html = fetch(url)
    except (URLError, HTTPError) as e:
        print(f"Fetch failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not html:
        print("Empty response", file=sys.stderr)
        sys.exit(1)

    text = trafilatura.extract(html, favor_recall=True, include_comments=False)
    if not text:
        print("trafilatura extraction returned empty", file=sys.stderr)
        sys.exit(1)

    print(text)


if __name__ == "__main__":
    main()
