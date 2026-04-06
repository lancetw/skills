"""Fetch Apostolic Fathers texts from newadvent.org.

Early Church / Apostolic Fathers (~50-200 CE): Didache, 1 Clement,
Epistle of Barnabas, Shepherd of Hermas, Ignatius (7 letters),
Polycarp, Martyrdom of Polycarp, Epistle to Diognetus.

Usage:
    python fetch_apostolic_fathers.py <work> [chapter]
    python fetch_apostolic_fathers.py list

Examples:
    python fetch_apostolic_fathers.py Didache 1
    python fetch_apostolic_fathers.py "1 Clement" 5
    python fetch_apostolic_fathers.py "Ignatius Ephesians" 1
    python fetch_apostolic_fathers.py list
"""

import html as html_mod
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.request
import urllib.error

BASE_URL = "https://www.newadvent.org/fathers"

# (lookup_keys, display_name, url_code, date)
WORKS = [
    (["didache", "十二使徒遺訓"],
     "Didache", "0714", "~50-120 CE"),
    (["1 clement", "克萊孟一書", "clement"],
     "1 Clement", "1010", "~96 CE"),
    (["barnabas", "巴拿巴書信"],
     "Epistle of Barnabas", "0124", "~70-132 CE"),
    (["shepherd of hermas", "黑馬牧人書", "hermas"],
     "Shepherd of Hermas", "0201", "~100-160 CE"),
    (["ignatius ephesians", "依格那丟致以弗所人書"],
     "Ignatius to Ephesians", "0104", "~110 CE"),
    (["ignatius magnesians", "依格那丟致馬格尼西亞人書"],
     "Ignatius to Magnesians", "0105", "~110 CE"),
    (["ignatius trallians", "依格那丟致特拉利安人書"],
     "Ignatius to Trallians", "0106", "~110 CE"),
    (["ignatius romans", "依格那丟致羅馬人書"],
     "Ignatius to Romans", "0107", "~110 CE"),
    (["ignatius philadelphians", "依格那丟致費城人書"],
     "Ignatius to Philadelphians", "0108", "~110 CE"),
    (["ignatius smyrnaeans", "依格那丟致士每拿人書"],
     "Ignatius to Smyrnaeans", "0109", "~110 CE"),
    (["ignatius polycarp", "依格那丟致坡旅甲書"],
     "Ignatius to Polycarp", "0110", "~110 CE"),
    (["polycarp", "坡旅甲致腓立比人書", "polycarp philippians"],
     "Polycarp to Philippians", "0136", "~110-140 CE"),
    (["martyrdom of polycarp", "坡旅甲殉道記"],
     "Martyrdom of Polycarp", "0102", "~155 CE"),
    (["diognetus", "致丟格那妥書"],
     "Epistle to Diognetus", "0101", "~130-200 CE"),
]


def _lookup(name: str):
    """Look up work. Returns (display_name, url_code, date) or None."""
    key = name.lower().strip()
    # Exact match
    for keys, display, code, date in WORKS:
        for k in keys:
            if key == k:
                return display, code, date
    # Partial match
    for keys, display, code, date in WORKS:
        for k in keys:
            if key in k or k in key:
                return display, code, date
    return None


def _fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": "bible-buddy-skill/1.0",
        "Accept": "text/html",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _clean(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = html_mod.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _parse_chapters(page_html: str, chapter: int = None) -> list[dict]:
    """Parse <h2 id/class="chapterN">Title</h2> + <p>text</p> structure."""
    results = []

    # Remove ad divs
    page_html = re.sub(r'<div[^>]*class=["\'](?:catholicadnet|CMtag)[^"\']*["\'][^>]*>.*?</div>',
                       '', page_html, flags=re.DOTALL | re.IGNORECASE)

    # Split by <h2> tags, then extract chapter number from content or attributes
    chunks = re.split(r'<h2[^>]*>(.*?)</h2>', page_html, flags=re.IGNORECASE | re.DOTALL)

    # chunks[0] = before first h2, chunks[1] = h2 content, chunks[2] = body, ...
    results_raw = []
    for i in range(1, len(chunks), 2):
        h2_content = chunks[i]
        body = chunks[i + 1] if i + 1 < len(chunks) else ""

        # Extract chapter number: "Chapter 1. Title" or just a number
        ch_match = re.match(r'(?:Chapter\s+)?(\d+)\.?\s*(.*)', _clean(h2_content), re.IGNORECASE)
        if ch_match:
            results_raw.append((int(ch_match.group(1)), ch_match.group(2).strip(), body))

    for ch_num, ch_title, ch_body in results_raw:

        if chapter is not None and ch_num != chapter:
            continue

        # Extract text from <p> tags
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', ch_body, re.DOTALL | re.IGNORECASE)
        text = ' '.join(_clean(p) for p in paragraphs if _clean(p))

        if text:
            results.append({
                "chapter": ch_num,
                "title": ch_title,
                "text": text,
            })

    return results


def fetch(work: str, chapter: int = None) -> dict:
    info = _lookup(work)
    if not info:
        return {"error": f"Unknown work: {work}. Use 'list' to see available texts."}

    display, code, date = info
    url = f"{BASE_URL}/{code}.htm"

    try:
        page_html = _fetch_html(url)
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}", "url": url}
    except Exception as e:
        return {"error": f"Request failed: {e}", "url": url}

    chapters = _parse_chapters(page_html, chapter)

    if not chapters:
        return {"error": f"No chapters extracted from {display}", "url": url}

    ref = display
    if chapter:
        ref += f" {chapter}"

    return {
        "source": f"newadvent.org ({date})",
        "reference": ref,
        "date": date,
        "url": url,
        "chapters": chapters,
    }


def format_output(result: dict) -> str:
    if "error" in result:
        return f"⚠ Error: {result['error']}\n  URL: {result.get('url', 'N/A')}"

    lines = [
        f"📖 {result['reference']}",
        f"來源: {result['source']} ({result['url']})",
        "",
    ]

    for ch in result.get("chapters", []):
        title = ch.get("title", "")
        if title:
            lines.append(f"  [{ch['chapter']}] {title}")
        # Truncate long chapter text for display
        text = ch["text"]
        if len(text) > 500:
            text = text[:500] + "..."
        lines.append(f"  {text}")
        lines.append("")

    return "\n".join(lines)


def list_works() -> str:
    lines = ["═══ Apostolic Fathers ═══"]
    for keys, display, code, date in WORKS:
        lines.append(f"  • {display:35s} {date:15s} (key: {keys[0]})")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1].lower() == "list":
        print(list_works())
        sys.exit(0)

    args = sys.argv[1:]
    # Find where numeric arg starts
    num_idx = next((i for i, a in enumerate(args) if a.isdigit()), None)
    if num_idx is not None and num_idx > 0:
        work = " ".join(args[:num_idx])
        chapter = int(args[num_idx])
    else:
        work = " ".join(args)
        chapter = None

    result = fetch(work, chapter)
    print(format_output(result))
