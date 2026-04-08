"""Fetch Apostolic Fathers Greek original text from First1KGreek (TEI XML).

Source: OpenGreekAndLatin/First1KGreek (GitHub) — Kirsopp Lake editions (1912/1917).
Covers: Didache, 1-2 Clement, Barnabas, Hermas, Ignatius (7 letters),
        Polycarp, Martyrdom of Polycarp, Epistle to Diognetus.
Note: Fragments of Papias not available in First1KGreek.

Usage:
    python fetch_apostolic_fathers_greek.py <work> [chapter] [section]
    python fetch_apostolic_fathers_greek.py list

Examples:
    python fetch_apostolic_fathers_greek.py list
    python fetch_apostolic_fathers_greek.py didache 1
    python fetch_apostolic_fathers_greek.py "1 clement" 5
    python fetch_apostolic_fathers_greek.py barnabas 5 3
    python fetch_apostolic_fathers_greek.py "ignatius ephesians" 1
    python fetch_apostolic_fathers_greek.py "hermas visions" 1
    python fetch_apostolic_fathers_greek.py "hermas mandates" 12 3
    python fetch_apostolic_fathers_greek.py "黑馬牧人書：異象" 1
    python fetch_apostolic_fathers_greek.py "巴拿巴書信" 4
"""

import re
import sys
import xml.etree.ElementTree as ET
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/master/data"
NS = {"tei": "http://www.tei-c.org/ns/1.0"}

# ── Work definitions ────────────────────────────────────────────────
# structure: "flat" = chapter→section
#            "hermas" = book→chapter→section with division mapping
#            "ignatius" = epistle→chapter→section

WORKS = [
    # ── Flat chapter→section works ──────────────────────────────────
    {
        "keys": ["didache", "十二使徒遺訓"],
        "name": "Didache (Greek)",
        "tlg": "tlg1311/tlg001",
        "xml": "tlg1311.tlg001.1st1K-grc1.xml",
        "date": "~50-120 CE",
        "structure": "flat",
    },
    {
        "keys": ["1 clement", "克萊孟一書", "clement", "first clement"],
        "name": "1 Clement (Greek)",
        "tlg": "tlg1271/tlg001",
        "xml": "tlg1271.tlg001.1st1K-grc1.xml",
        "date": "~96 CE",
        "structure": "flat",
    },
    {
        "keys": ["2 clement", "克萊孟二書", "second clement"],
        "name": "2 Clement (Greek)",
        "tlg": "tlg1271/tlg002",
        "xml": "tlg1271.tlg002.1st1K-grc1.xml",
        "date": "~100-140 CE",
        "structure": "flat",
    },
    {
        "keys": ["barnabas", "巴拿巴書信", "epistle of barnabas"],
        "name": "Epistle of Barnabas (Greek)",
        "tlg": "tlg1216/tlg001",
        "xml": "tlg1216.tlg001.opp-grc1.xml",
        "date": "~70-132 CE",
        "structure": "flat",
    },
    {
        "keys": ["polycarp", "坡旅甲致腓立比人書", "polycarp philippians"],
        "name": "Polycarp to Philippians (Greek)",
        "tlg": "tlg1622/tlg001",
        "xml": "tlg1622.tlg001.1st1K-grc1.xml",
        "date": "~110-140 CE",
        "structure": "flat",
    },
    {
        "keys": ["martyrdom of polycarp", "坡旅甲殉道記", "martyrdom polycarp"],
        "name": "Martyrdom of Polycarp (Greek)",
        "tlg": "tlg1484/tlg001",
        "xml": "tlg1484.tlg001.1st1K-grc1.xml",
        "date": "~155 CE",
        "structure": "flat",
    },
    {
        "keys": ["diognetus", "致丟格那妥書", "epistle to diognetus"],
        "name": "Epistle to Diognetus (Greek)",
        "tlg": "tlg0646/tlg004",
        "xml": "tlg0646.tlg004.1st1K-grc1.xml",
        "date": "~130-200 CE",
        "structure": "flat",
    },
    # ── Ignatius: 7 letters in one XML ──────────────────────────────
    {
        "keys": ["ignatius ephesians", "依格那丟致以弗所人書"],
        "name": "Ignatius to Ephesians (Greek)",
        "tlg": "tlg1443/tlg001",
        "xml": "tlg1443.tlg001.1st1K-grc1.xml",
        "date": "~110 CE",
        "structure": "ignatius",
        "epistle_n": 1,
    },
    {
        "keys": ["ignatius magnesians", "依格那丟致馬格尼西亞人書"],
        "name": "Ignatius to Magnesians (Greek)",
        "tlg": "tlg1443/tlg001",
        "xml": "tlg1443.tlg001.1st1K-grc1.xml",
        "date": "~110 CE",
        "structure": "ignatius",
        "epistle_n": 2,
    },
    {
        "keys": ["ignatius trallians", "依格那丟致特拉利安人書"],
        "name": "Ignatius to Trallians (Greek)",
        "tlg": "tlg1443/tlg001",
        "xml": "tlg1443.tlg001.1st1K-grc1.xml",
        "date": "~110 CE",
        "structure": "ignatius",
        "epistle_n": 3,
    },
    {
        "keys": ["ignatius romans", "依格那丟致羅馬人書"],
        "name": "Ignatius to Romans (Greek)",
        "tlg": "tlg1443/tlg001",
        "xml": "tlg1443.tlg001.1st1K-grc1.xml",
        "date": "~110 CE",
        "structure": "ignatius",
        "epistle_n": 4,
    },
    {
        "keys": ["ignatius philadelphians", "依格那丟致費城人書"],
        "name": "Ignatius to Philadelphians (Greek)",
        "tlg": "tlg1443/tlg001",
        "xml": "tlg1443.tlg001.1st1K-grc1.xml",
        "date": "~110 CE",
        "structure": "ignatius",
        "epistle_n": 5,
    },
    {
        "keys": ["ignatius smyrnaeans", "依格那丟致士每拿人書"],
        "name": "Ignatius to Smyrnaeans (Greek)",
        "tlg": "tlg1443/tlg001",
        "xml": "tlg1443.tlg001.1st1K-grc1.xml",
        "date": "~110 CE",
        "structure": "ignatius",
        "epistle_n": 6,
    },
    {
        "keys": ["ignatius polycarp", "依格那丟致坡旅甲書"],
        "name": "Ignatius to Polycarp (Greek)",
        "tlg": "tlg1443/tlg001",
        "xml": "tlg1443.tlg001.1st1K-grc1.xml",
        "date": "~110 CE",
        "structure": "ignatius",
        "epistle_n": 7,
    },
    # ── Hermas: 27 books → 3 divisions ──────────────────────────────
    {
        "keys": ["hermas visions", "黑馬牧人書：異象", "shepherd visions"],
        "name": "Shepherd of Hermas: Visions (Greek)",
        "tlg": "tlg1419/tlg001",
        "xml": "tlg1419.tlg001.1st1K-grc1.xml",
        "date": "~100-160 CE",
        "structure": "hermas",
        "book_range": (1, 5),
    },
    {
        "keys": ["hermas mandates", "黑馬牧人書：誡命", "shepherd mandates",
                 "hermas commandments", "shepherd commandments"],
        "name": "Shepherd of Hermas: Mandates (Greek)",
        "tlg": "tlg1419/tlg001",
        "xml": "tlg1419.tlg001.1st1K-grc1.xml",
        "date": "~100-160 CE",
        "structure": "hermas",
        "book_range": (6, 17),
    },
    {
        "keys": ["hermas similitudes", "黑馬牧人書：比喻", "shepherd similitudes",
                 "hermas parables"],
        "name": "Shepherd of Hermas: Similitudes (Greek)",
        "tlg": "tlg1419/tlg001",
        "xml": "tlg1419.tlg001.1st1K-grc1.xml",
        "date": "~100-160 CE",
        "structure": "hermas",
        "book_range": (18, 27),
    },
]


def _lookup(name: str):
    """Find work entry by key. Returns dict or None."""
    key = name.lower().strip()
    for w in WORKS:
        for k in w["keys"]:
            if key == k:
                return w
    for w in WORKS:
        for k in w["keys"]:
            if key in k or k in key:
                return w
    return None


# ── XML helpers ─────────────────────────────────────────────────────

_xml_cache: dict[str, ET.Element] = {}


def _fetch_xml(tlg: str, xml_file: str) -> ET.Element:
    """Download and parse TEI XML, with in-process cache."""
    cache_key = f"{tlg}/{xml_file}"
    if cache_key in _xml_cache:
        return _xml_cache[cache_key]

    url = f"{BASE}/{tlg}/{xml_file}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "bible-buddy-skill/1.0",
        "Accept": "application/xml",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()

    root = ET.fromstring(data)
    _xml_cache[cache_key] = root
    return root


def _extract_text(elem) -> str:
    """Extract Greek text from TEI element, skipping <note> and <head>."""
    parts = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        tag = child.tag.replace("{http://www.tei-c.org/ns/1.0}", "")
        if tag in ("note", "head"):
            if child.tail:
                parts.append(child.tail)
        else:
            parts.append(_extract_text(child))
            if child.tail:
                parts.append(child.tail)
    return "".join(parts)


def _clean(text: str) -> str:
    """Normalize whitespace."""
    return re.sub(r"\s+", " ", text).strip()


def _safe_int(val: str) -> int | None:
    """Convert string to int, returning None for non-numeric (preface, etc)."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


# ── Parsers ─────────────────────────────────────────────────────────

def _parse_flat(root, chapter=None, section=None) -> list[dict]:
    """Parse flat chapter→section structure (most works)."""
    body = root.find(".//tei:text/tei:body", NS)
    top = body.find("tei:div", NS)
    chapters = top.findall("tei:div", NS)

    results = []
    for ch in chapters:
        ch_n_str = ch.get("n", "")
        ch_n = _safe_int(ch_n_str)

        if chapter is not None:
            if ch_n != chapter:
                continue

        sections = ch.findall("tei:div", NS)
        if sections:
            sec_texts = []
            for sec in sections:
                sec_n_str = sec.get("n", "")
                sec_n = _safe_int(sec_n_str)
                if section is not None and sec_n != section:
                    continue
                text = _clean(_extract_text(sec))
                if text:
                    sec_texts.append(f"[{sec_n_str}] {text}")
            if sec_texts:
                label = ch_n if ch_n is not None else ch_n_str
                results.append({"chapter": label, "text": "\n".join(sec_texts)})
        else:
            # Chapter with no section subdivisions (e.g. praef with direct text)
            text = _clean(_extract_text(ch))
            if text:
                label = ch_n if ch_n is not None else ch_n_str
                results.append({"chapter": label, "text": text})

    return results


def _parse_ignatius(root, epistle_n: int,
                    chapter=None, section=None) -> list[dict]:
    """Parse Ignatius XML — select one epistle by number."""
    body = root.find(".//tei:text/tei:body", NS)
    top = body.find("tei:div", NS)
    epistles = top.findall("tei:div", NS)

    target = None
    for ep in epistles:
        if _safe_int(ep.get("n")) == epistle_n:
            target = ep
            break
    if target is None:
        return []

    results = []
    for ch in target.findall("tei:div", NS):
        ch_n_str = ch.get("n", "")
        ch_n = _safe_int(ch_n_str)

        if chapter is not None and ch_n != chapter:
            continue

        sections = ch.findall("tei:div", NS)
        if sections:
            sec_texts = []
            for sec in sections:
                sec_n_str = sec.get("n", "")
                sec_n = _safe_int(sec_n_str)
                if section is not None and sec_n != section:
                    continue
                text = _clean(_extract_text(sec))
                if text:
                    sec_texts.append(f"[{sec_n_str}] {text}")
            if sec_texts:
                label = ch_n if ch_n is not None else ch_n_str
                results.append({"chapter": label, "text": "\n".join(sec_texts)})
        else:
            text = _clean(_extract_text(ch))
            if text:
                label = ch_n if ch_n is not None else ch_n_str
                results.append({"chapter": label, "text": text})

    return results


def _parse_hermas(root, book_start: int, book_end: int,
                  div_num=None, chapter=None) -> list[dict]:
    """Parse Hermas XML for a specific division range."""
    body = root.find(".//tei:text/tei:body", NS)
    top = body.find("tei:div", NS)
    all_books = top.findall("tei:div", NS)

    results = []
    for book in all_books:
        book_n = _safe_int(book.get("n"))
        if book_n is None or book_n < book_start or book_n > book_end:
            continue

        local_num = book_n - book_start + 1
        if div_num is not None and local_num != div_num:
            continue

        for ch in book.findall("tei:div", NS):
            ch_n = _safe_int(ch.get("n"))
            if ch_n is None:
                continue
            if chapter is not None and ch_n != chapter:
                continue

            sec_texts = []
            for sec in ch.findall("tei:div", NS):
                text = _clean(_extract_text(sec))
                if text:
                    sec_texts.append(f"[{sec.get('n')}] {text}")

            if sec_texts:
                results.append({
                    "division": local_num,
                    "chapter": ch_n,
                    "text": "\n".join(sec_texts),
                })

    return results


# ── Public API ──────────────────────────────────────────────────────

def fetch(work: str, arg1: int = None, arg2: int = None) -> dict:
    """Fetch Greek text.

    Flat works:    fetch("didache", chapter, section)
    Ignatius:      fetch("ignatius ephesians", chapter, section)
    Hermas:        fetch("hermas visions", division_num, chapter)
    """
    info = _lookup(work)
    if not info:
        return {"error": f"Unknown work: {work}. Use 'list' to see available."}

    try:
        root = _fetch_xml(info["tlg"], info["xml"])
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": f"Request failed: {e}"}

    url = f"{BASE}/{info['tlg']}/{info['xml']}"
    structure = info["structure"]

    if structure == "hermas":
        start, end = info["book_range"]
        entries = _parse_hermas(root, start, end, arg1, arg2)
    elif structure == "ignatius":
        entries = _parse_ignatius(root, info["epistle_n"], arg1, arg2)
    else:
        entries = _parse_flat(root, arg1, arg2)

    ref = info["name"]
    if arg1 is not None:
        ref += f" {arg1}"
        if arg2 is not None:
            ref += f".{arg2}"

    if not entries:
        return {"error": f"No text found for {ref}", "url": url}

    return {
        "source": f"First1KGreek / Kirsopp Lake ({info['date']})",
        "reference": ref,
        "date": info["date"],
        "url": url,
        "language": "Greek",
        "entries": entries,
    }


def format_output(result: dict) -> str:
    if "error" in result:
        return f"Error: {result['error']}"

    lines = [
        f"{result['reference']}",
        f"Source: {result['source']}",
        f"Language: {result['language']}",
        "",
    ]

    for entry in result.get("entries", []):
        if "division" in entry:
            lines.append(f"  --- {entry['division']}.{entry['chapter']} ---")
        else:
            lines.append(f"  --- Chapter {entry['chapter']} ---")
        lines.append(f"  {entry['text']}")
        lines.append("")

    return "\n".join(lines)


def list_works() -> str:
    lines = [
        "=== Apostolic Fathers Greek (First1KGreek / Kirsopp Lake) ===",
        "",
        "Didache (TLG 1311)              ~50-120 CE   key: didache / 十二使徒遺訓",
        "1 Clement (TLG 1271)            ~96 CE       key: 1 clement / 克萊孟一書",
        "2 Clement (TLG 1271)            ~100-140 CE  key: 2 clement / 克萊孟二書",
        "Epistle of Barnabas (TLG 1216)  ~70-132 CE   key: barnabas / 巴拿巴書信",
        "Polycarp to Phil. (TLG 1622)    ~110-140 CE  key: polycarp / 坡旅甲致腓立比人書",
        "Martyrdom of Polycarp (TLG 1484) ~155 CE     key: martyrdom of polycarp / 坡旅甲殉道記",
        "Epistle to Diognetus (TLG 0646) ~130-200 CE  key: diognetus / 致丟格那妥書",
        "",
        "Ignatius (TLG 1443) — 7 letters, ~110 CE:",
        "  Ephesians       key: ignatius ephesians / 依格那丟致以弗所人書",
        "  Magnesians      key: ignatius magnesians / 依格那丟致馬格尼西亞人書",
        "  Trallians       key: ignatius trallians / 依格那丟致特拉利安人書",
        "  Romans          key: ignatius romans / 依格那丟致羅馬人書",
        "  Philadelphians  key: ignatius philadelphians / 依格那丟致費城人書",
        "  Smyrnaeans      key: ignatius smyrnaeans / 依格那丟致士每拿人書",
        "  To Polycarp     key: ignatius polycarp / 依格那丟致坡旅甲書",
        "",
        "Shepherd of Hermas (TLG 1419) — ~100-160 CE:",
        "  Visions 1-5      key: hermas visions / 黑馬牧人書：異象",
        "  Mandates 1-12    key: hermas mandates / 黑馬牧人書：誡命",
        "  Similitudes 1-10 key: hermas similitudes / 黑馬牧人書：比喻",
        "",
        "Not available: Fragments of Papias (not in First1KGreek)",
        "",
        "Usage:",
        '  fetch_apostolic_fathers_greek.py didache 1',
        '  fetch_apostolic_fathers_greek.py "1 clement" 5',
        '  fetch_apostolic_fathers_greek.py "ignatius ephesians" 1',
        '  fetch_apostolic_fathers_greek.py "hermas mandates" 12 3',
        '  fetch_apostolic_fathers_greek.py barnabas 5 3',
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1].lower() == "list":
        print(list_works())
        sys.exit(0)

    args = sys.argv[1:]
    num_idx = next((i for i, a in enumerate(args) if a.isdigit()), None)
    if num_idx is not None and num_idx > 0:
        work_name = " ".join(args[:num_idx])
        nums = [int(a) for a in args[num_idx:] if a.isdigit()]
    else:
        work_name = " ".join(args)
        nums = []

    a1 = nums[0] if len(nums) >= 1 else None
    a2 = nums[1] if len(nums) >= 2 else None

    result = fetch(work_name, a1, a2)
    print(format_output(result))
