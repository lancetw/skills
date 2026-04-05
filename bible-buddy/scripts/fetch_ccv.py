#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Fetch 新漢語譯本 (CCV) scripture text from chinesebible.org.hk.

Uses two systems:
- OT (available books): new API at /bible/onlinebible2/bible_ccv
- NT (all books): old iframe system at /onlinebible/

Usage:
    uv run scripts/fetch_ccv.py <book> <chapter> [start_verse] [end_verse]

Examples:
    uv run scripts/fetch_ccv.py 創世記 1 1 5
    uv run scripts/fetch_ccv.py 馬太福音 5 17 20
    uv run scripts/fetch_ccv.py Isaiah 7 14
    uv run scripts/fetch_ccv.py Jonah 1
"""

import html as html_mod
import http.cookiejar
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.request
import os

sys.path.insert(0, os.path.dirname(__file__))
from book_names import lookup

NT_BOOKS = {
    "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor",
    "Gal", "Eph", "Phil", "Col", "1Thess", "2Thess", "1Tim", "2Tim",
    "Titus", "Phlm", "Heb", "Jas", "1Pet", "2Pet", "1John", "2John",
    "3John", "Jude", "Rev",
}


def fetch(book: str, chapter: int, start_verse: int = None, end_verse: int = None) -> dict:
    info = lookup(book)
    if not info:
        return {"error": f"Unknown book: {book}"}

    chinese_name, _, osis, _ = info
    ref = _make_ref(chinese_name, chapter, start_verse, end_verse)

    if osis in NT_BOOKS:
        return _fetch_nt(osis, chinese_name, chapter, start_verse, end_verse, ref)
    else:
        return _fetch_ot(osis, chinese_name, chapter, start_verse, end_verse, ref)


def _fetch_ot(osis, chinese_name, chapter, start_v, end_v, ref):
    """Fetch OT from new API system (/bible/onlinebible2/bible_ccv)."""
    base = "https://www.chinesebible.org.hk/bible/onlinebible2/bible_ccv"
    api = "https://www.chinesebible.org.hk/bible/onlinebible2/fetchReadingContent"

    try:
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        opener.addheaders = [("User-Agent", "Mozilla/5.0")]

        resp = opener.open(base, timeout=15)
        page = resp.read().decode("utf-8")
        csrf = re.search(r'<meta\s+name="csrf-token"\s+content="([^"]+)"', page)
        if not csrf:
            return {"error": "No CSRF token", "reference": ref}

        payload = json.dumps({
            "csrf_test_name": csrf.group(1),
            "table": "bible_ccv",
            "book": osis,
            "chapter": str(chapter),
            "verse": "",
            "typesettingStyleObj": None,
        }).encode("utf-8")

        req = urllib.request.Request(api, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Requested-With", "XMLHttpRequest")
        req.add_header("X-CSRF-TOKEN", csrf.group(1))
        req.add_header("Referer", base)

        resp2 = opener.open(req, timeout=15)
        data = json.loads(resp2.read().decode("utf-8"))

        raw = data.get("data", {}).get("osisContentRaw", [])
        verses = []
        for v in raw:
            content = v.get("content", "")
            if not content:
                continue
            num = int(v.get("verse", "0"))
            if start_v and end_v and not (start_v <= num <= end_v):
                continue
            elif start_v and not end_v and num != start_v:
                continue
            text = _parse_osis(content)
            if text:
                verses.append({"verse": str(num), "text": text})

        if not verses and raw:
            return {
                "source": "chinesebible.org.hk",
                "reference": ref,
                "version": "新漢語譯本 (CCV)",
                "verses": [],
                "note": f"⚠ {chinese_name}的新漢語譯本尚未上線（翻譯進行中）。",
            }

        return {
            "source": "chinesebible.org.hk (新漢語譯本 OT API)",
            "reference": ref,
            "version": "新漢語譯本 (CCV)",
            "verses": verses,
        }
    except Exception as e:
        return {"error": str(e), "reference": ref}


def _fetch_nt(osis, chinese_name, chapter, start_v, end_v, ref):
    """Fetch NT from old iframe system (/onlinebible/)."""
    base = "https://www.chinesebible.org.hk/onlinebible"

    try:
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        opener.addheaders = [("User-Agent", "Mozilla/5.0")]

        # Establish session
        opener.open(f"{base}/", timeout=15)
        # Select book (OSIS code)
        opener.open(f"{base}/change_biblebook.php?biblebook={osis}", timeout=15)
        # Select chapter
        opener.open(f"{base}/change_chapter.php?chapter={chapter}", timeout=15)
        # Get content
        resp = opener.open(f"{base}/window1.php", timeout=15)
        page = resp.read().decode("utf-8")

        if "此譯本沒有" in page:
            return {
                "source": "chinesebible.org.hk",
                "reference": ref,
                "version": "新漢語譯本 (CCV)",
                "verses": [],
                "note": f"⚠ {chinese_name}的新漢語譯本在網路版無此內容。",
            }

        verses = _parse_nt_html(page, start_v, end_v)
        return {
            "source": "chinesebible.org.hk (新漢語譯本 NT)",
            "reference": ref,
            "version": "新漢語譯本 (CCV)",
            "verses": verses,
        }
    except Exception as e:
        return {"error": str(e), "reference": ref}


def _parse_osis(content: str) -> str:
    """Parse OSIS XML to plain text."""
    text = re.sub(r'<title[^>]*>.*?</title>', '', content, flags=re.DOTALL)
    text = re.sub(r'<note[^>]*>.*?</note>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_mod.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def _parse_nt_html(page: str, start_v, end_v) -> list[dict]:
    """Parse NT verse text from old system HTML."""
    verses = []

    # Pattern: <span class="verse">17</span> text...
    parts = re.split(r'<span\s+class="verse"[^>]*>', page)

    for part in parts[1:]:
        num_match = re.match(r'(\d+)\s*</span>(.*)', part, re.DOTALL)
        if not num_match:
            continue
        num = int(num_match.group(1))
        raw = num_match.group(2)

        if start_v and end_v and not (start_v <= num <= end_v):
            continue
        elif start_v and not end_v and num != start_v:
            continue

        # Remove footnote <a> tags entirely (they contain onclick with footnote text)
        clean = re.sub(r'<a[^>]*class="footnote_normal"[^>]*>.*?</a>', '', raw, flags=re.DOTALL)
        # Remove section title divs
        clean = re.sub(r'<div[^>]*class="title"[^>]*>.*?</div>', '', clean, flags=re.DOTALL)
        # Remove all remaining HTML tags
        clean = re.sub(r'<[^>]+>', '', clean)
        clean = html_mod.unescape(clean)
        clean = re.sub(r'\s+', ' ', clean).strip()

        if clean:
            verses.append({"verse": str(num), "text": clean})

    return verses


def _make_ref(chinese_name, chapter, start_verse, end_verse):
    ref = f"{chinese_name} {chapter}"
    if start_verse and end_verse:
        ref += f":{start_verse}-{end_verse}"
    elif start_verse:
        ref += f":{start_verse}"
    return ref


def format_output(result: dict) -> str:
    if result.get("error"):
        return f"⚠ Error: {result['error']}"

    lines = [
        f"📖 {result['reference']}",
        f"譯本: {result.get('version', '新漢語譯本')}",
        f"來源: {result.get('source', 'chinesebible.org.hk')}",
        "",
    ]

    for v in result.get("verses", []):
        lines.append(f"  [{v['verse']}] {v['text']}")

    if not result.get("verses"):
        lines.append("  (無經文內容)")

    if result.get("note"):
        lines.append(f"\n{result['note']}")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    # Handle multi-word book names (e.g., Song of Songs 1 1 → book="Song of Songs")
    args = sys.argv[1:]
    chapter_idx = next((i for i, a in enumerate(args) if a.isdigit()), None)
    if chapter_idx is not None and chapter_idx > 0:
        book = " ".join(args[:chapter_idx])
        nums = args[chapter_idx:]
    else:
        book = args[0]
        nums = args[1:]

    chapter = int(nums[0])
    start_v = int(nums[1]) if len(nums) > 1 else None
    end_v = int(nums[2]) if len(nums) > 2 else None

    result = fetch(book, chapter, start_v, end_v)
    print(format_output(result))
