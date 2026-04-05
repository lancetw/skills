#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["trafilatura", "patchright"]
# ///
"""Fetch a URL and extract main article text via trafilatura.

Usage:
    uv run scripts/fetch_url.py <URL>

First tries urllib with browser headers (fast).
Falls back to patchright (headless Chromium) when blocked (403, empty).
"""

import sys
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

import trafilatura


def fetch_urllib(url: str, timeout: int = 15) -> str | None:
    """Fast path: urllib with browser-spoofing headers."""
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8",
    })
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="replace")


def fetch_patchright(url: str, timeout: int = 30000) -> str | None:
    """Slow path: headless Chromium via patchright (bypasses Cloudflare)."""
    from patchright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="zh-TW",
            timezone_id="Asia/Taipei",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()
        page.goto(url, timeout=timeout)
        time.sleep(5)
        html = page.content()
        browser.close()
    return html


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run scripts/fetch_url.py <URL>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]

    # --- fast path: urllib ---
    html = None
    try:
        html = fetch_urllib(url)
    except (URLError, HTTPError) as e:
        print(f"urllib failed ({e}), trying patchright…", file=sys.stderr)

    if html:
        text = trafilatura.extract(html, favor_recall=True, include_comments=False)
        if text:
            print(text)
            return

    # --- slow path: patchright ---
    print("Falling back to patchright…", file=sys.stderr)
    try:
        html = fetch_patchright(url)
    except Exception as e:
        print(f"patchright failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not html:
        print("Empty response from patchright", file=sys.stderr)
        sys.exit(1)

    text = trafilatura.extract(html, favor_recall=True, include_comments=False)
    if not text:
        print("trafilatura extraction returned empty", file=sys.stderr)
        sys.exit(1)

    print(text)


if __name__ == "__main__":
    main()
