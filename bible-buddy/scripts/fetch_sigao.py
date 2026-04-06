"""Fetch 思高譯本 (Sigao/Studium Biblicum) from ccreadbible.org.

Full 73-book Catholic canon including deuterocanonical books.

Usage:
    python fetch_sigao.py <book> <chapter> [start_verse] [end_verse]

Examples:
    python fetch_sigao.py 多俾亞傳 1
    python fetch_sigao.py Tobit 1 1 5
    python fetch_sigao.py 德訓篇 24 1 12
    python fetch_sigao.py 馬太福音 5 1 12
    python fetch_sigao.py 創世記 1
"""

import html as html_mod
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.request
import urllib.error
import os

sys.path.insert(0, os.path.dirname(__file__))
from book_names import lookup

BASE_URL = "https://www.ccreadbible.org/chinesebible/sigao"

# ── Book ID mapping: OSIS code → ccreadbible URL slug ────────────────
# Protestant canon (same OSIS codes as book_names.py)
SIGAO_SLUG = {
    "Gen": "Genesis", "Exod": "Exodus", "Lev": "Leviticus",
    "Num": "Numbers", "Deut": "Deuteronomy", "Josh": "Joshua",
    "Judg": "Judges", "Ruth": "Ruth", "1Sam": "1_Samuel",
    "2Sam": "2_Samuel", "1Kgs": "1_Kings", "2Kgs": "2_Kings",
    "1Chr": "1_Chronicles", "2Chr": "2_Chronicles", "Ezra": "Ezra",
    "Neh": "Nehemiah", "Esth": "Esther", "Job": "Job",
    "Ps": "Psalms", "Prov": "Proverbs", "Eccl": "Ecclesiastes",
    "Song": "Song_of_Songs", "Isa": "Isaiah", "Jer": "Jeremiah",
    "Lam": "Lamentations", "Ezek": "Ezekiel", "Dan": "Daniel",
    "Hos": "Hosea", "Joel": "Joel", "Amos": "Amos",
    "Obad": "Obadiah", "Jonah": "Jonah", "Mic": "Micah",
    "Nah": "Nahum", "Hab": "Habakkuk", "Zeph": "Zephaniah",
    "Hag": "Haggai", "Zech": "Zechariah", "Mal": "Malachi",
    "Matt": "Matthew", "Mark": "Mark", "Luke": "Luke",
    "John": "John", "Acts": "Acts", "Rom": "Romans",
    "1Cor": "1_Corinthians", "2Cor": "2_Corinthians", "Gal": "Galatians",
    "Eph": "Ephesians", "Phil": "Philippians", "Col": "Colossians",
    "1Thess": "1_Thessalonians", "2Thess": "2_Thessalonians",
    "1Tim": "1_Timothy", "2Tim": "2_Timothy", "Titus": "Titus",
    "Phlm": "Philemon", "Heb": "Hebrews", "Jas": "James",
    "1Pet": "1_Peter", "2Pet": "2_Peter", "1John": "1_John",
    "2John": "2_John", "3John": "3_John", "Jude": "Jude",
    "Rev": "Revelation",
}

# ── Deuterocanonical books (not in book_names.py) ────────────────────
# (chinese_name, slug)
DEUTERO_BOOKS = {
    "多俾亞傳": ("多俾亞傳", "Tobit"),
    "tobit":    ("多俾亞傳", "Tobit"),
    "友弟德傳": ("友弟德傳", "Judith"),
    "judith":   ("友弟德傳", "Judith"),
    "瑪加伯上": ("瑪加伯上", "1_Maccabees"),
    "1 maccabees": ("瑪加伯上", "1_Maccabees"),
    "瑪加伯下": ("瑪加伯下", "2_Maccabees"),
    "2 maccabees": ("瑪加伯下", "2_Maccabees"),
    "智慧篇":   ("智慧篇", "Wisdom"),
    "wisdom":   ("智慧篇", "Wisdom"),
    "德訓篇":   ("德訓篇", "Sirach"),
    "sirach":   ("德訓篇", "Sirach"),
    "ecclesiasticus": ("德訓篇", "Sirach"),
    "巴路克":   ("巴路克", "Baruch"),
    "baruch":   ("巴路克", "Baruch"),
}


def _resolve_book(name: str) -> tuple | None:
    """Resolve book name → (chinese_name, slug).

    Checks deuterocanonical books first, then falls back to book_names.py.
    """
    key = name.lower().strip()

    # Deuterocanonical direct match
    if key in DEUTERO_BOOKS:
        return DEUTERO_BOOKS[key]

    # Partial match on deuterocanonical
    for alias, val in DEUTERO_BOOKS.items():
        if key in alias or alias in key:
            return val

    # Protestant canon via book_names.py
    info = lookup(name)
    if info:
        chinese_name, _, osis, _ = info
        slug = SIGAO_SLUG.get(osis)
        if slug:
            return (chinese_name, slug)

    return None


def _fetch_html(url: str) -> str:
    """Fetch raw HTML from a URL."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "bible-buddy-skill/1.0",
        "Accept": "text/html",
        "Accept-Language": "zh-TW,zh;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _parse_verses(page_html: str, start_verse: int = None,
                  end_verse: int = None) -> list[dict]:
    """Extract verses from ccreadbible HTML.

    Structure: <td><sup>N</sup>verse text...</td>
    """
    verses = []

    # Find all <sup>N</sup> followed by text within <td>
    # Pattern: <td ...><sup>N</sup>text</td>
    for m in re.finditer(
        r'<td[^>]*>\s*<sup>(\d+)</sup>(.*?)</td>',
        page_html, re.DOTALL
    ):
        v_num = int(m.group(1))
        v_text = m.group(2)

        if start_verse and v_num < start_verse:
            continue
        if end_verse and v_num > end_verse:
            continue

        # Clean HTML
        v_text = re.sub(r'<[^>]+>', '', v_text)
        v_text = html_mod.unescape(v_text)
        v_text = re.sub(r'\s+', ' ', v_text).strip()

        if v_text:
            verses.append({"verse": str(v_num), "text": v_text})

    return verses


def fetch(book: str, chapter: int,
          start_verse: int = None, end_verse: int = None) -> dict:
    """Fetch a chapter from ccreadbible.org 思高譯本."""
    resolved = _resolve_book(book)
    if not resolved:
        return {"error": f"Unknown book: {book}"}

    chinese_name, slug = resolved
    url = f"{BASE_URL}/{slug}_bible_Ch_{chapter}_.html"

    try:
        page_html = _fetch_html(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": f"{chinese_name} 第{chapter}章不存在", "url": url}
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}", "url": url}
    except Exception as e:
        return {"error": f"Request failed: {e}", "url": url}

    verses = _parse_verses(page_html, start_verse, end_verse)

    if not verses:
        return {"error": f"No verses extracted from {chinese_name} {chapter}", "url": url}

    ref = f"{chinese_name} {chapter}"
    if start_verse and end_verse:
        ref += f":{start_verse}-{end_verse}"
    elif start_verse:
        ref += f":{start_verse}"

    return {
        "source": "ccreadbible.org (思高譯本)",
        "reference": ref,
        "version": "思高譯本",
        "url": url,
        "verses": verses,
    }


def format_output(result: dict) -> str:
    if "error" in result:
        return f"⚠ Error: {result['error']}\n  URL: {result.get('url', 'N/A')}"

    lines = [
        f"📖 {result['reference']}",
        f"譯本: {result['version']}",
        f"來源: {result['source']} ({result['url']})",
        "",
    ]

    for v in result.get("verses", []):
        lines.append(f"  [{v['verse']}] {v['text']}")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    args = sys.argv[1:]

    # Find where numeric args start
    num_idx = next((i for i, a in enumerate(args) if a.isdigit()), None)
    if num_idx is not None and num_idx > 0:
        book = " ".join(args[:num_idx])
        nums = args[num_idx:]
    else:
        book = args[0]
        nums = args[1:]

    chapter = int(nums[0])
    start_v = int(nums[1]) if len(nums) > 1 else None
    end_v = int(nums[2]) if len(nums) > 2 else None

    result = fetch(book, chapter, start_v, end_v)
    print(format_output(result))
