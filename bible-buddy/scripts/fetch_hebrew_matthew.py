#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Fetch Hebrew Matthew manuscripts (Shem-Tov / Du Tillet).

Sources:
  shem-tov  — Even Bohan (שם טוב, c.1380), hebreeuwsmattheus/data (GitHub)
  du-tillet — Heb. MSS 132, Paris (1553), bjarnard/text (GitHub)

Usage:
    uv run scripts/fetch_hebrew_matthew.py <manuscript> <chapter> [start_verse] [end_verse]
    uv run scripts/fetch_hebrew_matthew.py list

Examples:
    uv run scripts/fetch_hebrew_matthew.py shem-tov 5 1 12
    uv run scripts/fetch_hebrew_matthew.py du-tillet 1 1 5
    uv run scripts/fetch_hebrew_matthew.py shem-tov 28
    uv run scripts/fetch_hebrew_matthew.py list
"""

import re
import sys
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.request

MANUSCRIPTS = {
    "shem-tov": "Shem-Tov (Even Bohan, c.1380)",
    "du-tillet": "Du Tillet (Heb. MSS 132, Paris, 1553)",
}

SHEM_TOV_URL = (
    "https://raw.githubusercontent.com/hebreeuwsmattheus/data/master/he/{chapter}.txt"
)
DU_TILLET_URL_CH1 = (
    "https://raw.githubusercontent.com/bjarnard/text/master/begin.html"
)
DU_TILLET_URL = (
    "https://raw.githubusercontent.com/bjarnard/text/master/ch{chapter}.html"
)


# ── HTML parser for Du Tillet grid layout ─────────────────────────────


class _GridItemParser(HTMLParser):
    """Extract text content from <div class="grid-item"> elements."""

    def __init__(self):
        super().__init__()
        self.items: list[str] = []
        self._in_item = False
        self._depth = 0
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            if self._in_item:
                self._depth += 1
            elif "grid-item" in dict(attrs).get("class", ""):
                self._in_item = True
                self._depth = 1
                self._buf = []

    def handle_endtag(self, tag):
        if tag == "div" and self._in_item:
            self._depth -= 1
            if self._depth <= 0:
                self.items.append("".join(self._buf).strip())
                self._in_item = False

    def handle_data(self, data):
        if self._in_item:
            self._buf.append(data)

    def handle_entityref(self, name):
        if self._in_item:
            import html as html_mod

            self._buf.append(html_mod.unescape(f"&{name};"))

    def handle_charref(self, name):
        if self._in_item:
            import html as html_mod

            self._buf.append(html_mod.unescape(f"&#{name};"))


# ── Fetching & parsing ────────────────────────────────────────────────


def _fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "bible-buddy/1.0"})
    resp = urllib.request.urlopen(req, timeout=15)
    return resp.read().decode("utf-8")


def _parse_shem_tov(text: str) -> list[dict]:
    """Parse Shem-Tov chapter: verse blocks separated by blank lines.

    Format:
        1.
        Hebrew text here

        2.
        More Hebrew text
    """
    verses = []
    blocks = re.split(r"\n\n+", text.strip())
    for block in blocks:
        lines = block.strip().split("\n")
        if not lines:
            continue
        # Verse number on its own line: "1."
        m = re.match(r"(\d+)\.\s*$", lines[0])
        if m:
            vnum = m.group(1)
            vtext = " ".join(ln.strip() for ln in lines[1:] if ln.strip())
            if vtext:
                verses.append({"verse": vnum, "text": vtext})
            continue
        # Verse number + text on same line: "1. text"
        m = re.match(r"(\d+)\.\s+(.+)", lines[0])
        if m:
            vnum = m.group(1)
            rest = [m.group(2)] + lines[1:]
            vtext = " ".join(ln.strip() for ln in rest if ln.strip())
            if vtext:
                verses.append({"verse": vnum, "text": vtext})
    return verses


def _strip_variants(text: str) -> str:
    """Strip variant readings from Du Tillet text.

    {…} = Shem-Tov variants, <…> = Münster variants, ~…~ = editorial.
    1. Strip matched pairs within the same verse.
    2. Strip cross-verse tails: last unmatched { to end (STV starts here).
    3. Strip cross-verse heads: start to first unmatched } (STV ends here).
    4. Remove any remaining stray marker characters.
    """
    # 1. Strip matched pairs
    text = re.sub(r"\{[^}]*\}", "", text)
    text = re.sub(r"~[^~]*~", "", text)
    text = re.sub(r"<[^>]*>", "", text)
    # 2. Unmatched { — strip from last { to end (STV variant tail)
    if "{" in text:
        before = text[: text.rfind("{")]
        text = before if before.strip() else text.replace("{", "")
    # 3. Unmatched } — strip from start to first } (STV variant head)
    if "}" in text:
        after = text[text.index("}") + 1 :]
        text = after if after.strip() else text.replace("}", "")
    # 4. Stray markers and cleanup
    text = text.replace("{", "").replace("}", "").replace("~", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_du_tillet(html: str) -> list[dict]:
    """Parse Du Tillet HTML grid: triplets of (English, verse#, Hebrew)."""
    parser = _GridItemParser()
    parser.feed(html)
    items = parser.items

    verses = []
    seen = set()
    for i in range(0, len(items) - 2, 3):
        vnum = items[i + 1].strip()
        hebrew = items[i + 2].strip()
        if not vnum or not hebrew:
            continue
        # Deduplicate (source has duplicate verses in some chapters)
        if vnum in seen:
            continue
        seen.add(vnum)
        hebrew = _strip_variants(hebrew)
        if hebrew:
            verses.append({"verse": vnum, "text": hebrew})
    return verses


def fetch(
    manuscript: str,
    chapter: int,
    start_verse: int = None,
    end_verse: int = None,
) -> dict:
    ms = manuscript.lower().strip()
    if ms not in MANUSCRIPTS:
        return {
            "error": f"Unknown manuscript: {manuscript}. Use: {', '.join(MANUSCRIPTS)}"
        }

    if chapter < 1 or chapter > 28:
        return {"error": f"Matthew has 28 chapters (got {chapter})"}

    ms_label = MANUSCRIPTS[ms]

    try:
        if ms == "shem-tov":
            url = SHEM_TOV_URL.format(chapter=chapter)
            raw = _fetch_url(url)
            verses = _parse_shem_tov(raw)
        else:
            url = (
                DU_TILLET_URL_CH1
                if chapter == 1
                else DU_TILLET_URL.format(chapter=chapter)
            )
            raw = _fetch_url(url)
            verses = _parse_du_tillet(raw)
    except Exception as e:
        return {"error": f"Fetch failed: {e}"}

    # Filter by verse range
    if start_verse is not None:
        ev = end_verse if end_verse is not None else start_verse
        verses = [v for v in verses if start_verse <= int(v["verse"]) <= ev]

    ref = f"馬太福音 {chapter}"
    if start_verse and end_verse:
        ref += f":{start_verse}-{end_verse}"
    elif start_verse:
        ref += f":{start_verse}"

    return {
        "source": f"Hebrew Matthew — {ms_label}",
        "reference": ref,
        "manuscript": ms,
        "verses": verses,
    }


def format_output(result: dict) -> str:
    if result.get("error"):
        return f"Error: {result['error']}"

    lines = [
        f"{result['reference']}",
        f"Manuscript: {result['source']}",
        "",
    ]
    for v in result.get("verses", []):
        lines.append(f"  [{v['verse']}] {v['text']}")

    if not result.get("verses"):
        lines.append("  (no verses found)")

    return "\n".join(lines)


def cmd_list():
    print("=== Hebrew Matthew Manuscripts ===\n")
    print("Coverage: Matthew 1-28\n")
    for ms, label in MANUSCRIPTS.items():
        print(f"  {ms:<12} {label}")
    print()
    print("Usage: fetch_hebrew_matthew.py <manuscript> <chapter> [start] [end]")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0)

    if args[0] == "list":
        cmd_list()
        return

    manuscript = args[0]
    if len(args) < 2:
        print(
            "Usage: fetch_hebrew_matthew.py <manuscript> <chapter> [start_verse] [end_verse]",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        chapter = int(args[1])
    except ValueError:
        print(f"Error: invalid chapter '{args[1]}'", file=sys.stderr)
        sys.exit(1)

    start_v = int(args[2]) if len(args) > 2 else None
    end_v = int(args[3]) if len(args) > 3 else None

    result = fetch(manuscript, chapter, start_v, end_v)
    print(format_output(result))


if __name__ == "__main__":
    main()
