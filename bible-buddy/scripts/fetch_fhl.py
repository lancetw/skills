#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Fetch scripture text from 信望愛 bible.fhl.net API.

Supports 88 versions. Default: 和合本修訂版(rcuv).
Common: rcuv(和合本修訂版), lcc(呂振中), ncv(新譯本), lxx(七十士),
        bhs(馬索拉原文), esv, kjv. Run --list-versions for full list.
Note: requests for 和合本(unv) are auto-redirected to 和合本修訂版(rcuv).

API docs: https://bible.fhl.net/api/

Usage:
    uv run scripts/fetch_fhl.py <book> <chapter> [start_verse] [end_verse] [version]

Examples:
    uv run scripts/fetch_fhl.py 以賽亞書 7 10 17
    uv run scripts/fetch_fhl.py 以賽亞書 7 14 14 lcc
    uv run scripts/fetch_fhl.py Genesis 1 1 5 rcuv
    uv run scripts/fetch_fhl.py 馬太福音 5 17 20
"""

import html as html_mod
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.request
import os

sys.path.insert(0, os.path.dirname(__file__))
from book_names import lookup

API_BASE = "https://bible.fhl.net/api/qb.php"

# bid: Protestant canon order, 1-66
BOOK_BID = {
    "Gen": 1, "Exod": 2, "Lev": 3, "Num": 4, "Deut": 5,
    "Josh": 6, "Judg": 7, "Ruth": 8, "1Sam": 9, "2Sam": 10,
    "1Kgs": 11, "2Kgs": 12, "1Chr": 13, "2Chr": 14, "Ezra": 15,
    "Neh": 16, "Esth": 17, "Job": 18, "Ps": 19, "Prov": 20,
    "Eccl": 21, "Song": 22, "Isa": 23, "Jer": 24, "Lam": 25,
    "Ezek": 26, "Dan": 27, "Hos": 28, "Joel": 29, "Amos": 30,
    "Obad": 31, "Jonah": 32, "Mic": 33, "Nah": 34, "Hab": 35,
    "Zeph": 36, "Hag": 37, "Zech": 38, "Mal": 39,
    "Matt": 40, "Mark": 41, "Luke": 42, "John": 43, "Acts": 44,
    "Rom": 45, "1Cor": 46, "2Cor": 47, "Gal": 48, "Eph": 49,
    "Phil": 50, "Col": 51, "1Thess": 52, "2Thess": 53,
    "1Tim": 54, "2Tim": 55, "Titus": 56, "Phlm": 57, "Heb": 58,
    "Jas": 59, "1Pet": 60, "2Pet": 61, "1John": 62, "2John": 63,
    "3John": 64, "Jude": 65, "Rev": 66,
}

def _get_version_names() -> dict:
    """Fetch version names from FHL API (cached after first call)."""
    if hasattr(_get_version_names, "_cache"):
        return _get_version_names._cache

    # Hardcoded common versions as fallback
    names = {
        "unv": "和合本", "rcuv": "和合本2010", "lcc": "呂振中譯本",
        "ncv": "新譯本", "tcv95": "現代中文譯本1995", "tcv2019": "現代中文譯本2019",
        "ofm": "思高譯本", "recover": "恢復本", "wcb": "環球譯本",
        "cnet": "NET聖經中譯本", "csb": "中文標準譯本", "cbol": "原文直譯",
        "bhs": "舊約馬索拉原文", "fhlwh": "新約原文", "lxx": "七十士譯本",
        "kjv": "KJV", "esv": "ESV", "nasb": "NASB", "asv": "ASV",
        "bbe": "BBE", "web": "WEB", "darby": "Darby", "erv": "ERV",
    }

    try:
        url = "https://bible.fhl.net/api/abv.php"
        req = urllib.request.Request(url, headers={"User-Agent": "torah-first-century-skill/1.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))
        for r in data.get("record", []):
            code = r.get("book", "")
            cname = r.get("cname", "")
            if code and cname:
                names[code] = cname
    except Exception:
        pass

    _get_version_names._cache = names
    return names


VERSION_NAMES = None  # Loaded lazily

def _version_name(code: str) -> str:
    global VERSION_NAMES
    if VERSION_NAMES is None:
        VERSION_NAMES = _get_version_names()
    return VERSION_NAMES.get(code, code)


def fetch(book: str, chapter: int, start_verse: int = None, end_verse: int = None, version: str = "rcuv") -> dict:
    # Always redirect 和合本(unv) to 和合本修訂版(rcuv)
    if version == "unv":
        version = "rcuv"
    info = lookup(book)
    if not info:
        return {"error": f"Unknown book: {book}"}

    chinese_name, _, osis, _ = info
    bid = BOOK_BID.get(osis)
    if not bid:
        return {"error": f"No bid for: {osis}"}

    # Build sec parameter
    if start_verse and end_verse:
        sec = f"{start_verse}-{end_verse}"
    elif start_verse:
        sec = str(start_verse)
    else:
        sec = ""  # entire chapter

    # Build API URL
    params = f"bid={bid}&chap={chapter}"
    if sec:
        params += f"&sec={sec}"
    if version and version != "unv":
        params += f"&version={version}"

    url = f"{API_BASE}?{params}"
    version_name = _version_name(version)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "torah-first-century-skill/1.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": f"FHL API error: {e}", "url": url}

    if data.get("status") != "success":
        return {"error": f"API returned: {data.get('status', 'unknown')}", "url": url}

    # Extract verses
    verses = []
    for rec in data.get("record", []):
        text = rec.get("bible_text", "")
        if not text:
            continue
        # Clean up: remove HTML tags, heading markers
        text = re.sub(r'<[^>]+>', '', text)
        text = html_mod.unescape(text).strip()
        text = re.sub(r'\s+', ' ', text)
        # Remove footnote markers like 【6】
        text = re.sub(r'【\d+】', '', text)
        verses.append({"verse": str(rec.get("sec", "?")), "text": text})

    ref = f"{chinese_name} {chapter}"
    if start_verse and end_verse:
        ref += f":{start_verse}-{end_verse}"
    elif start_verse:
        ref += f":{start_verse}"

    return {
        "source": f"信望愛 bible.fhl.net ({version_name})",
        "reference": ref,
        "version": version_name,
        "url": f"https://bible.fhl.net/new/read.php?bid={bid}&chap={chapter}",
        "verses": verses,
    }


def format_output(result: dict) -> str:
    if result.get("error"):
        return f"⚠ Error: {result['error']}\n  URL: {result.get('url', 'N/A')}"

    lines = [
        f"📖 {result['reference']}",
        f"譯本: {result['version']}",
        f"來源: {result['source']}",
        "",
    ]

    for v in result.get("verses", []):
        lines.append(f"  [{v['verse']}] {v['text']}")

    if not result.get("verses"):
        lines.append("  ⚠ No verses found.")

    return "\n".join(lines)


if __name__ == "__main__":
    # Special: --list-versions
    if len(sys.argv) > 1 and sys.argv[1] == "--list-versions":
        names = _get_version_names()
        for code, name in sorted(names.items()):
            print(f"  {code:15s}  {name}")
        sys.exit(0)

    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    # Handle multi-word book names (e.g., I Corinthians 3 8 → book="I Corinthians")
    args = sys.argv[1:]
    chapter_idx = next((i for i, a in enumerate(args) if a.isdigit()), None)
    if chapter_idx is not None and chapter_idx > 0:
        book = " ".join(args[:chapter_idx])
        rest = args[chapter_idx:]
    else:
        book = args[0]
        rest = args[1:]

    chapter = int(rest[0])
    start_v = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else None
    end_v = int(rest[2]) if len(rest) > 2 and rest[2].isdigit() else None

    # Last non-digit arg is version code (default: rcuv)
    version = "rcuv"
    for arg in rest[1:]:
        if not arg.isdigit():
            version = arg

    result = fetch(book, chapter, start_v, end_v, version)
    print(format_output(result))
