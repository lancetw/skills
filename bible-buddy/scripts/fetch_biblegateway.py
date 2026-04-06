"""Fetch Chinese scripture text from BibleGateway.com.

Supports: RCUV (RCU17TS), 新譯本 (CNVT)

Usage:
    python fetch_biblegateway.py <book> <chapter>:<start_verse>-<end_verse> [version]

Examples:
    python fetch_biblegateway.py 以賽亞書 7:10-17
    python fetch_biblegateway.py Isaiah 7:14
    python fetch_biblegateway.py Gen 1:1-3 CNVT
    python fetch_biblegateway.py 馬太福音 5:17-20
"""

import html
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.request
import urllib.error
import os

sys.path.insert(0, os.path.dirname(__file__))
from book_names import lookup

VERSION_MAP = {
    "RCUV": "RCU17TS",
    "RCU17TS": "RCU17TS",
    "和合本修訂版": "RCU17TS",
    "CNVT": "CNVT",
    "新譯本": "CNVT",
    "CUV": "CUV",
    "和合本": "CUV",
    "NRSVUE": "NRSVUE",
    "NRSV": "NRSVUE",
}

VERSION_NAMES = {
    "RCU17TS": "和合本修訂版 (RCUV, 2010)",
    "CNVT": "新譯本 (CNV)",
    "CUV": "舊和合本 (CUV, 1919)",
    "NRSVUE": "NRSVUE (2021)",
}

# ── Deuterocanonical books (not in book_names.py) ────────────────────
# (lookup_keys, display_name, bg_search_name)
_DEUTERO_BOOKS = [
    # Books on BibleGateway NRSVUE but NOT on Sefaria
    (["1 esdras", "以斯拉續篇上"],      "1 Esdras",           "1+Esdras"),
    (["2 esdras", "以斯拉續篇下"],      "2 Esdras",           "2+Esdras"),
    (["3 maccabees", "瑪加伯三書"],     "3 Maccabees",        "3+Maccabees"),
    (["4 maccabees", "瑪加伯四書"],     "4 Maccabees",        "4+Maccabees"),
    (["baruch", "巴路克"],              "Baruch",             "Baruch"),
    (["bel and the dragon", "比勒與大龍"],"Bel and the Dragon","Bel+and+the+Dragon"),
    (["letter of jeremiah", "耶利米書信"],"Letter of Jeremiah","Letter+of+Jeremiah"),
    (["prayer of azariah", "亞撒利雅禱詞"],"Prayer of Azariah","Prayer+of+Azariah"),
    # Books on BOTH BibleGateway NRSVUE and Sefaria
    (["sirach", "德訓篇", "ecclesiasticus", "ben sira"], "Sirach", "Sirach"),
    (["tobit", "多俾亞傳"],            "Tobit",              "Tobit"),
    (["judith", "友弟德傳"],            "Judith",             "Judith"),
    (["wisdom of solomon", "智慧篇", "wisdom"], "Wisdom of Solomon", "Wisdom+of+Solomon"),
    (["1 maccabees", "瑪加伯上"],       "1 Maccabees",        "1+Maccabees"),
    (["2 maccabees", "瑪加伯下"],       "2 Maccabees",        "2+Maccabees"),
    (["susanna", "蘇撒拿傳"],           "Susanna",            "Susanna"),
    (["prayer of manasseh", "瑪拿西禱詞"], "Prayer of Manasseh", "Prayer+of+Manasseh"),
    (["psalm 151", "詩篇 151"],        "Psalm 151",          "Psalm+151"),
]

def _lookup_deutero(name: str):
    """Look up deuterocanonical book for Bible Gateway. Returns (display_name, bg_name) or None.

    Uses exact match first, then partial. Called BEFORE canonical lookup
    to prevent fuzzy conflicts (e.g., '詩篇 151' matching '詩篇').
    """
    key = name.lower().strip()
    # Exact match on any alias
    for keys, display, bg in _DEUTERO_BOOKS:
        for k in keys:
            if key == k:
                return display, bg
    # Partial match (only if key is long enough to avoid false positives)
    if len(key) > 4:
        for keys, display, bg in _DEUTERO_BOOKS:
            for k in keys:
                if key in k or k in key:
                    return display, bg
    return None


def fetch(book: str, ref: str, version: str = "RCU17TS") -> dict:
    # Check deuterocanonical FIRST (exact match) to avoid fuzzy conflicts
    # e.g., "詩篇 151" must not fuzzy-match "詩篇" (Psalms)
    deutero = _lookup_deutero(book)
    if deutero:
        chinese_name, bg_name = deutero
        # Deuterocanonical books default to NRSVUE (not available in Chinese versions)
        if version == "RCU17TS":
            version = "NRSVUE"
        info = None
    else:
        info = lookup(book)
        if not info:
            return {"error": f"Unknown book: {book}"}
        chinese_name, _, _, bg_name = info

    version_code = VERSION_MAP.get(version, version)

    # Build URL
    search = f"{bg_name}+{ref}".replace(":", "%3A")
    url = f"https://www.biblegateway.com/passage/?search={search}&version={version_code}"

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            page_html = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": f"Passage not found on Bible Gateway. Check book/chapter/verse. Ref: {bg_name} {ref}", "url": url}
        return {"error": f"Bible Gateway error: {e.code} {e.reason}", "url": url}
    except urllib.error.URLError as e:
        return {"error": f"Cannot reach Bible Gateway (network issue). Detail: {e.reason}", "url": url}
    except Exception as e:
        return {"error": f"Request failed: {e}", "url": url}

    # Extract passage text from HTML
    verses = extract_verses(page_html)

    return {
        "source": f"BibleGateway.com ({VERSION_NAMES.get(version_code, version_code)})",
        "reference": f"{chinese_name} {ref}",
        "version": version_code,
        "version_name": VERSION_NAMES.get(version_code, version_code),
        "url": url,
        "verses": verses,
    }


def extract_verses(page_html: str) -> list[dict]:
    """Extract verse numbers and text from Bible Gateway HTML."""
    verses = []

    # Find the passage text div
    passage_match = re.search(r'<div class="passage-text">(.*?)</div>\s*</div>\s*</div>', page_html, re.DOTALL)
    if not passage_match:
        # Try alternative pattern
        passage_match = re.search(r'class="passage-col[^"]*">(.*?)<div class="crossrefs', page_html, re.DOTALL)

    if not passage_match:
        return [{"verse": "?", "text": "⚠ Could not parse passage from page"}]

    passage = passage_match.group(1)

    # Remove footnotes and cross-references
    passage = re.sub(r'<sup[^>]*class="footnote"[^>]*>.*?</sup>', '', passage, flags=re.DOTALL)
    passage = re.sub(r'<sup[^>]*class="crossreference"[^>]*>.*?</sup>', '', passage, flags=re.DOTALL)
    passage = re.sub(r'<div class="footnotes">.*', '', passage, flags=re.DOTALL)

    # Extract verse numbers and text
    # Pattern: <sup class="versenum">14&nbsp;</sup>Text here
    parts = re.split(r'<sup[^>]*class="versenum"[^>]*>', passage)

    # Check for chapternum (verse 1) in the part before the first versenum.
    # BibleGateway renders verse 1 as <span class="chapternum">N </span>
    # instead of <sup class="versenum">, so it gets missed by the split.
    if parts:
        ch_match = re.search(r'<span class="chapternum">\d+\s*(?:&nbsp;)?\s*</span>(.*)', parts[0], re.DOTALL)
        if ch_match:
            text = re.sub(r'<[^>]+>', '', ch_match.group(1))
            text = html.unescape(text).strip()
            text = re.sub(r'\s+', ' ', text)
            if text:
                verses.append({"verse": "1", "text": text})

    for part in parts[1:]:  # Skip first part (before first verse number)
        verse_match = re.match(r'(\d+)\s*(?:&nbsp;)?\s*</sup>(.*?)(?=<sup[^>]*class="versenum"|$)', part, re.DOTALL)
        if verse_match:
            verse_num = verse_match.group(1)
            text = verse_match.group(2)
            # Clean HTML
            text = re.sub(r'<[^>]+>', '', text)
            text = html.unescape(text).strip()
            text = re.sub(r'\s+', ' ', text)
            if text:
                verses.append({"verse": verse_num, "text": text})

    # If no verses found with versenum pattern, try chapternum
    if not verses:
        chapter_match = re.search(r'<span class="chapternum">(\d+)\s*</span>(.*?)(?=<sup|$)', passage, re.DOTALL)
        if chapter_match:
            text = re.sub(r'<[^>]+>', '', chapter_match.group(2))
            text = html.unescape(text).strip()
            verses.append({"verse": "1", "text": text})

    if not verses:
        # Last resort: just get clean text
        clean = re.sub(r'<[^>]+>', ' ', passage)
        clean = html.unescape(clean).strip()
        clean = re.sub(r'\s+', ' ', clean)
        if clean:
            verses.append({"verse": "?", "text": clean[:500]})

    return verses


def format_output(result: dict) -> str:
    if "error" in result:
        return f"⚠ Error: {result['error']}\n  URL: {result.get('url', 'N/A')}"

    lines = [
        f"📖 {result['reference']}",
        f"譯本: {result['version_name']}",
        f"來源: {result['url']}",
        "",
    ]

    for v in result.get("verses", []):
        lines.append(f"  [{v['verse']}] {v['text']}")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    book = sys.argv[1]
    ref = sys.argv[2] if len(sys.argv) > 2 else ""
    version = sys.argv[3] if len(sys.argv) > 3 else "RCU17TS"

    # Handle merged "Book Chapter:Verses" in a single argument
    # e.g., "Zechariah 3:1-5" → book="Zechariah", ref="3:1-5"
    # e.g., "1 Chronicles 21:1" → book="1 Chronicles", ref="21:1"
    if not lookup(book):
        parts = book.split()
        for i in range(len(parts) - 1, 0, -1):
            candidate = " ".join(parts[:i])
            rest = " ".join(parts[i:])
            if lookup(candidate):
                if ref and ref.upper() in VERSION_MAP:
                    version = ref
                book, ref = candidate, rest
                break

    result = fetch(book, ref, version)
    print(format_output(result))
