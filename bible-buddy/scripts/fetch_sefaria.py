"""Fetch Hebrew scripture text from Sefaria.org API.

Usage:
    python fetch_sefaria.py <book> <chapter> [start_verse] [end_verse]

Examples:
    python fetch_sefaria.py 以賽亞書 7
    python fetch_sefaria.py Isaiah 7 10 17
    python fetch_sefaria.py Gen 1 1 3
"""

import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.parse
import urllib.request
import urllib.error
import os

sys.path.insert(0, os.path.dirname(__file__))
from book_names import lookup


def fetch(book: str, chapter: int, start_verse: int = None, end_verse: int = None) -> dict:
    info = lookup(book)
    if not info:
        return {"error": f"Unknown book: {book}"}

    chinese_name, sefaria_name, osis, _ = info

    # Build Sefaria API URL
    if start_verse and end_verse:
        ref = f"{sefaria_name}.{chapter}.{start_verse}-{end_verse}"
    elif start_verse:
        ref = f"{sefaria_name}.{chapter}.{start_verse}"
    else:
        ref = f"{sefaria_name}.{chapter}"

    url = f"https://www.sefaria.org/api/v3/texts/{urllib.parse.quote(ref)}?version=source&version=all"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "torah-first-century-skill/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"Sefaria API error: {e.code} {e.reason}", "url": url}
    except Exception as e:
        return {"error": f"Request failed: {e}", "url": url}

    # Extract Hebrew text
    hebrew_versions = data.get("versions", [])
    hebrew_text = None
    for v in hebrew_versions:
        if v.get("language") == "he":
            hebrew_text = v.get("text")
            break

    # Extract English text
    english_text = None
    for v in hebrew_versions:
        if v.get("language") == "en":
            english_text = v.get("text")
            break

    # Format output
    result = {
        "source": "Sefaria.org",
        "reference": f"{chinese_name} {chapter}" + (f":{start_verse}-{end_verse}" if start_verse and end_verse else f":{start_verse}" if start_verse else ""),
        "sefaria_ref": ref,
        "url": f"https://www.sefaria.org/{ref.replace(' ', '_')}",
        "hebrew": hebrew_text,
        "english": english_text,
    }
    return result


def format_output(result: dict) -> str:
    if "error" in result:
        return f"⚠ Error: {result['error']}\n  URL: {result.get('url', 'N/A')}"

    lines = [
        f"📖 {result['reference']}",
        f"來源: {result['source']} ({result['url']})",
        "",
    ]

    he = result.get("hebrew")
    en = result.get("english")

    if isinstance(he, list):
        for i, verse in enumerate(he, 1):
            # Strip HTML tags
            clean = verse.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "") if isinstance(verse, str) else str(verse)
            lines.append(f"  [{i}] {clean}")
    elif isinstance(he, str):
        lines.append(f"  {he}")
    else:
        lines.append("  ⚠ Hebrew text not available")

    if en:
        lines.append("")
        lines.append("English:")
        if isinstance(en, list):
            for i, verse in enumerate(en, 1):
                clean = verse.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "") if isinstance(verse, str) else str(verse)
                lines.append(f"  [{i}] {clean}")
        elif isinstance(en, str):
            lines.append(f"  {en}")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    # Handle multi-word book names (e.g., I Chronicles 21 1 → book="I Chronicles")
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
