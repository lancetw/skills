"""Fetch pseudepigrapha and deuterocanonical text from pseudepigrapha.com.

Usage:
    python fetch_pseudepigrapha.py <book> [chapter] [start_verse] [end_verse]
    python fetch_pseudepigrapha.py list

Examples:
    python fetch_pseudepigrapha.py list
    python fetch_pseudepigrapha.py "1 Enoch" 1
    python fetch_pseudepigrapha.py "1 Enoch" 1 1 5
    python fetch_pseudepigrapha.py Tobit 3
    python fetch_pseudepigrapha.py Sirach 24 1 12
    python fetch_pseudepigrapha.py Jubilees 2
"""

import html
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.request
import urllib.error

# ── Book catalog ─────────────────────────────────────────────────────
# (display_name, url_path, chapter_format)
# chapter_format:
#   "h3"    = <h3>Abbr.N</h3> + [<b>V</b>] verses  (apocrypha_ot)
#   "enoch" = <A Name="ChN"> + <FONT> verse nums     (1 Enoch)
#   "flat"  = no chapters, whole text on one page      (short texts)

BOOKS = {
    # ── OT Apocrypha / Deuterocanon ──
    "1 esdras":           ("1 Esdras",           "/apocrypha_ot/1esdr.htm",    "h3"),
    "2 esdras":           ("2 Esdras",           "/apocrypha_ot/2esdr.htm",    "h3"),
    "1 maccabees":        ("1 Maccabees",        "/apocrypha_ot/1macc.htm",    "h3"),
    "2 maccabees":        ("2 Maccabees",        "/apocrypha_ot/2macc.htm",    "h3"),
    "3 maccabees":        ("3 Maccabees",        "/apocrypha_ot/3macc.htm",    "h3"),
    "4 maccabees":        ("4 Maccabees",        "/apocrypha_ot/4macc.htm",    "h3"),
    "tobit":              ("Tobit",              "/apocrypha_ot/tobit.htm",    "h3"),
    "judith":             ("Judith",             "/apocrypha_ot/judith.htm",   "h3"),
    "sirach":             ("Wisdom of Sirach",   "/apocrypha_ot/sirac.htm",    "h3"),
    "wisdom of sirach":   ("Wisdom of Sirach",   "/apocrypha_ot/sirac.htm",    "h3"),
    "ecclesiasticus":     ("Wisdom of Sirach",   "/apocrypha_ot/sirac.htm",    "h3"),
    "wisdom of solomon":  ("Wisdom of Solomon",  "/apocrypha_ot/wisolom.htm",  "h3"),
    "wisdom":             ("Wisdom of Solomon",  "/apocrypha_ot/wisolom.htm",  "h3"),
    "baruch":             ("Baruch",             "/apocrypha_ot/baruc.htm",    "h3"),
    "letter of jeremiah": ("Letter of Jeremiah", "/apocrypha_ot/letojer.htm",  "h3"),
    "prayer of azariah":  ("Prayer of Azariah",  "/apocrypha_ot/azariah.htm",  "h3"),
    "bel and the dragon": ("Bel and the Dragon", "/apocrypha_ot/beldrag.htm",  "h3"),
    "susanna":            ("Susanna",            "/apocrypha_ot/susan1.htm",   "h3"),
    "additions to esther":("Additions to Esther","/apocrypha_ot/esther.htm",   "h3"),
    "prayer of manasseh": ("Prayer of Manasseh", "/apocrypha_ot/manas.htm",    "flat"),
    "psalm 151":          ("Psalm 151",          "/apocrypha_ot/Pslm151.htm",  "flat"),
    # ── Pseudepigrapha ──
    "1 enoch":            ("1 Enoch",            "/pseudepigrapha/enoch.htm",   "enoch"),
    "2 enoch":            ("2 Enoch",            "/pseudepigrapha/enochs2.htm", "enoch"),
    "jubilees":           ("Jubilees",           "/jubilees/{ch}.htm",          "jubilees"),
    "2 baruch":           ("2 Baruch",           "/pseudepigrapha/2Baruch.html","flat"),
    "3 baruch":           ("3 Baruch",           "/pseudepigrapha/3Baruch.html","flat"),
    "testament of abraham":("Testament of Abraham","/pseudepigrapha/1007.htm",  "flat"),
    "apocalypse of abraham":("Apocalypse of Abraham","/pseudepigrapha/Apocalypse_of_Abraham.html","flat"),
    "letter of aristeas": ("Letter of Aristeas", "/pseudepigrapha/aristeas.htm","flat"),
    "martyrdom of isaiah":("Martyrdom of Isaiah","/pseudepigrapha/amartis.htm", "flat"),
    "ascension of isaiah":("Ascension of Isaiah","/pseudepigrapha/AscensionOfIsaiah.html","flat"),
    "assumption of moses":("Assumption of Moses","/pseudepigrapha/assumptionofmoses.html","flat"),
    "revelation of esdras":("Revelation of Esdras","/pseudepigrapha/revesd.htm","flat"),
    "apocalypse of elijah":("Apocalypse of Elijah","/pseudepigrapha/TheApocalypseOfElijah.html","flat"),
    "book of jasher":     ("Book of Jasher",     "/pseudepigrapha/jasher.html", "flat"),
    "story of ahikar":    ("Story of Ahikar",    "/pseudepigrapha/ahikar.htm",  "flat"),
    "zadokite document":  ("Zadokite Document",  "/pseudepigrapha/zadokite.html","flat"),
}

# Chinese aliases
ALIASES = {
    "以諾一書": "1 enoch", "以諾二書": "2 enoch",
    "多俾亞傳": "tobit", "友弟德傳": "judith",
    "德訓篇": "sirach", "智慧篇": "wisdom of solomon",
    "巴路克": "baruch", "瑪加伯上": "1 maccabees", "瑪加伯下": "2 maccabees",
    "禧年書": "jubilees", "亞伯拉罕遺訓": "testament of abraham",
    "亞伯拉罕啟示錄": "apocalypse of abraham",
    "以賽亞升天記": "ascension of isaiah", "以賽亞殉道記": "martyrdom of isaiah",
    "摩西升天記": "assumption of moses", "巴錄二書": "2 baruch", "巴錄三書": "3 baruch",
    "以斯拉一書": "1 esdras", "以斯拉二書": "2 esdras",
    "瑪加伯三書": "3 maccabees", "瑪加伯四書": "4 maccabees",
    "耶利米書信": "letter of jeremiah", "亞撒利雅禱詞": "prayer of azariah",
    "比勒與大龍": "bel and the dragon", "蘇撒拿傳": "susanna",
    "以斯帖補篇": "additions to esther", "瑪拿西禱詞": "prayer of manasseh",
    "詩篇 151": "psalm 151", "雅煞珥書": "book of jasher",
    "撒督文獻": "zadokite document", "以利亞啟示錄": "apocalypse of elijah",
}

BASE_URL = "https://pseudepigrapha.com"


def lookup(name: str) -> tuple | None:
    """Resolve book name → (display_name, url_path, chapter_format)."""
    key = name.lower().strip()
    if key in BOOKS:
        return BOOKS[key]
    if key in ALIASES:
        return BOOKS[ALIASES[key]]
    # Fuzzy: try partial match
    for k, v in BOOKS.items():
        if key in k or k in key:
            return v
    for alias, target in ALIASES.items():
        if key in alias or alias in key:
            return BOOKS[target]
    return None


def _fetch_html(url: str) -> str:
    """Fetch raw HTML from a URL."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "bible-buddy-skill/1.0",
        "Accept": "text/html",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _clean(text: str) -> str:
    """Strip HTML tags, copyright notices, and normalize whitespace."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    # Remove trailing copyright / attribution boilerplate
    text = re.sub(r'\s*Translated by R\.?\s*H\..*$', '', text, flags=re.DOTALL)
    text = re.sub(r'\s*©\s*Copyright.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ── Parser: h3 format (apocrypha_ot) ────────────────────────────────

def _parse_h3(page_html: str, chapter: int = None,
              start_verse: int = None, end_verse: int = None) -> list[dict]:
    """Parse <h3>Abbr.N</h3> + [<b>V</b>] verse format."""
    # Split by chapter headers
    chapters = re.split(r'<h3[^>]*>\s*', page_html, flags=re.IGNORECASE)

    results = []
    for chunk in chapters:
        # Extract chapter number from header like "Tob.1</h3>"
        ch_match = re.match(r'[A-Za-z0-9\s]+\.(\d+)\s*</h3>', chunk, re.IGNORECASE)
        if not ch_match:
            continue
        ch_num = int(ch_match.group(1))
        if chapter is not None and ch_num != chapter:
            continue

        # Extract verses: [<b>N</b>] text
        parts = re.split(r'\[<b>(\d+)</b>\]', chunk)
        for i in range(1, len(parts), 2):
            v_num = int(parts[i])
            v_text = _clean(parts[i + 1]) if i + 1 < len(parts) else ""
            if not v_text:
                continue
            if start_verse and v_num < start_verse:
                continue
            if end_verse and v_num > end_verse:
                continue
            results.append({"chapter": ch_num, "verse": str(v_num), "text": v_text})

    return results


# ── Parser: enoch format ─────────────────────────────────────────────

def _parse_enoch(page_html: str, chapter: int = None,
                 start_verse: int = None, end_verse: int = None) -> list[dict]:
    """Parse <A Name="ChN"> + <FONT> verse number format (1 Enoch, 2 Enoch)."""
    # Split by chapter anchors: <A Name="ChN">
    chapters = re.split(r'<A\s+Name="Ch(\d+\w?)"', page_html, flags=re.IGNORECASE)

    results = []
    for i in range(1, len(chapters), 2):
        ch_label = chapters[i]
        ch_text = chapters[i + 1] if i + 1 < len(chapters) else ""

        # Normalize chapter number (handle "91a" etc.)
        ch_num_match = re.match(r'(\d+)', ch_label)
        if not ch_num_match:
            continue
        ch_num = int(ch_num_match.group(1))
        if chapter is not None and ch_num != chapter:
            continue

        # Extract verses: <FONT Color="#0000FF" Size="-2">N.</FONT>
        parts = re.split(
            r'<FONT\s+Color="#0000FF"\s+Size="-2">(\d+)\.</FONT>',
            ch_text, flags=re.IGNORECASE
        )
        for j in range(1, len(parts), 2):
            v_num = int(parts[j])
            v_text = _clean(parts[j + 1]) if j + 1 < len(parts) else ""
            if not v_text:
                continue
            if start_verse and v_num < start_verse:
                continue
            if end_verse and v_num > end_verse:
                continue
            results.append({"chapter": ch_num, "verse": str(v_num), "text": v_text})

    return results


# ── Parser: jubilees format (one chapter per page) ──────────────────

def _parse_jubilees(page_html: str,
                    start_verse: int = None, end_verse: int = None) -> list[dict]:
    """Parse Jubilees pages with <OL><LI> verse format (unclosed LI tags)."""
    results = []

    # Split on <LI> tags (old HTML: no closing </LI>)
    parts = re.split(r'<LI>', page_html, flags=re.IGNORECASE)
    # parts[0] is before the first <LI>, skip it
    for idx, part in enumerate(parts[1:], 1):
        if start_verse and idx < start_verse:
            continue
        if end_verse and idx > end_verse:
            continue
        text = _clean(part)
        if text:
            results.append({"chapter": 0, "verse": str(idx), "text": text})

    return results


# ── Parser: flat format (whole text, no chapters) ───────────────────

def _parse_flat(page_html: str) -> list[dict]:
    """Extract full text from simple pages without chapter structure."""
    # Try verse-numbered format first: [<b>N</b>] or N.
    parts = re.split(r'\[<b>(\d+)</b>\]', page_html)
    if len(parts) > 2:
        results = []
        for i in range(1, len(parts), 2):
            v_num = parts[i]
            v_text = _clean(parts[i + 1]) if i + 1 < len(parts) else ""
            if v_text:
                results.append({"chapter": 0, "verse": v_num, "text": v_text})
        return results

    # Fallback: extract body text
    body = re.search(r'<body[^>]*>(.*)</body>', page_html, re.IGNORECASE | re.DOTALL)
    if body:
        text = _clean(body.group(1))
        # Trim to reasonable length
        if len(text) > 3000:
            text = text[:3000] + "..."
        return [{"chapter": 0, "verse": "1", "text": text}]
    return []


# ── Main fetch function ──────────────────────────────────────────────

def fetch(book: str, chapter: int = None,
          start_verse: int = None, end_verse: int = None) -> dict:
    """Fetch text from pseudepigrapha.com."""
    info = lookup(book)
    if not info:
        return {"error": f"Unknown book: {book}. Use 'list' to see available books."}

    display_name, url_path, fmt = info

    # Build URL
    if fmt == "jubilees":
        if not chapter:
            return {"error": "Jubilees requires a chapter number (1-50)."}
        url = BASE_URL + url_path.replace("{ch}", str(chapter))
    else:
        url = BASE_URL + url_path

    try:
        page_html = _fetch_html(url)
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}", "url": url}
    except Exception as e:
        return {"error": f"Request failed: {e}", "url": url}

    # Parse based on format
    if fmt == "h3":
        verses = _parse_h3(page_html, chapter, start_verse, end_verse)
    elif fmt == "enoch":
        verses = _parse_enoch(page_html, chapter, start_verse, end_verse)
    elif fmt == "jubilees":
        verses = _parse_jubilees(page_html, start_verse, end_verse)
    elif fmt == "flat":
        verses = _parse_flat(page_html)
    else:
        verses = []

    if not verses:
        hint = ""
        if chapter and fmt in ("h3", "enoch"):
            hint = f" (chapter {chapter} may not exist)"
        return {"error": f"No verses extracted from {display_name}{hint}.", "url": url}

    return {
        "source": "pseudepigrapha.com",
        "reference": _build_ref(display_name, chapter, start_verse, end_verse, fmt),
        "url": url,
        "verses": verses,
    }


def _build_ref(name: str, chapter: int, start_v: int, end_v: int, fmt: str) -> str:
    if not chapter:
        return name
    ref = f"{name} {chapter}"
    if start_v and end_v:
        ref += f":{start_v}-{end_v}"
    elif start_v:
        ref += f":{start_v}"
    return ref


# ── Output formatting ────────────────────────────────────────────────

def format_output(result: dict) -> str:
    if "error" in result:
        return f"⚠ Error: {result['error']}\n  URL: {result.get('url', 'N/A')}"

    lines = [
        f"📖 {result['reference']}",
        f"來源: {result['source']} ({result['url']})",
        "",
    ]

    for v in result.get("verses", []):
        ch = v.get("chapter", 0)
        vn = v["verse"]
        if ch:
            lines.append(f"  [{ch}:{vn}] {v['text']}")
        else:
            lines.append(f"  [{vn}] {v['text']}")

    return "\n".join(lines)


def list_books() -> str:
    """List all available books grouped by category."""
    apocrypha = []
    pseudepigrapha = []
    seen = set()

    for key, (display, path, _) in BOOKS.items():
        if display in seen:
            continue
        seen.add(display)
        if "/apocrypha_ot/" in path:
            apocrypha.append(display)
        else:
            pseudepigrapha.append(display)

    lines = ["═══ OT Apocrypha / Deuterocanon ═══"]
    for name in sorted(apocrypha):
        lines.append(f"  • {name}")
    lines.append("")
    lines.append("═══ Pseudepigrapha ═══")
    for name in sorted(pseudepigrapha):
        lines.append(f"  • {name}")
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1].lower() == "list":
        print(list_books())
        sys.exit(0)

    # Parse args: book [chapter] [start_verse] [end_verse]
    args = sys.argv[1:]

    # Find where numeric args start
    num_idx = next((i for i, a in enumerate(args) if a.isdigit()), None)
    if num_idx is not None and num_idx > 0:
        book = " ".join(args[:num_idx])
        nums = args[num_idx:]
    else:
        book = args[0]
        nums = args[1:]

    chapter = int(nums[0]) if len(nums) > 0 else None
    start_v = int(nums[1]) if len(nums) > 1 else None
    end_v = int(nums[2]) if len(nums) > 2 else None

    result = fetch(book, chapter, start_v, end_v)
    print(format_output(result))
