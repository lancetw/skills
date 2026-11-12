#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Cross-verify a Hebrew/Greek word claim against Sefaria API.

Checks if a word actually appears in a given verse and returns its context.
Useful for verifying claims like "almah appears in Isaiah 7:14."

Usage:
    uv run scripts/verify_claim.py <book> <chapter> <verse> <word>

Examples:
    uv run scripts/verify_claim.py Isaiah 7 14 עַלְמָה
    uv run scripts/verify_claim.py Genesis 1 1 בְּרֵאשִׁית
    uv run scripts/verify_claim.py Psalms 46 10 הַרְפּוּ
"""

import json
import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.parse
import urllib.request
import os

sys.path.insert(0, os.path.dirname(__file__))
from book_names import lookup


def verify(book: str, chapter: int, verse: int, word: str) -> dict:
    info = lookup(book)
    if not info:
        return {"verified": False, "error": f"Unknown book: {book}"}

    chinese_name, sefaria_name, osis, _ = info
    ref = f"{sefaria_name}.{chapter}.{verse}"
    url = f"https://www.sefaria.org/api/v3/texts/{urllib.parse.quote(ref)}?version=source&version=all"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "bible-buddy-verify/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"verified": False, "error": f"Sefaria API error: {e}", "ref": ref}

    # Extract Hebrew text
    hebrew_text = None
    for v in data.get("versions", []):
        if v.get("language") == "he":
            text = v.get("text", "")
            if isinstance(text, list):
                hebrew_text = " ".join(text)
            else:
                hebrew_text = text
            break

    if not hebrew_text:
        return {"verified": False, "error": "No Hebrew text found", "ref": ref}

    # Clean HTML tags from Sefaria text
    hebrew_text = re.sub(r'<[^>]+>', '', hebrew_text)

    # Strip cantillation marks for fuzzy matching
    def strip_accents(s):
        """Remove cantillation marks but keep vowel points."""
        result = []
        for c in unicodedata.normalize("NFD", s):
            cp = ord(c)
            # Keep Hebrew vowel points (U+05B0-U+05BD) and dagesh (U+05BC)
            # Remove cantillation marks (U+0591-U+05AF)
            if 0x0591 <= cp <= 0x05AF:
                continue
            result.append(c)
        return unicodedata.normalize("NFC", "".join(result))

    def strip_all_marks(s):
        """Remove all diacritics for loosest matching."""
        return "".join(c for c in unicodedata.normalize("NFD", s)
                       if unicodedata.category(c) not in ("Mn", "Me", "Mc"))

    # Try exact match, then stripped cantillation, then fully stripped
    found = (word in hebrew_text or
             strip_accents(word) in strip_accents(hebrew_text) or
             strip_all_marks(word) in strip_all_marks(hebrew_text))

    return {
        "verified": found,
        "ref": f"{chinese_name} {chapter}:{verse}",
        "sefaria_ref": ref,
        "word_searched": word,
        "found_in_text": found,
        "hebrew_text": hebrew_text,
        "confidence": "high" if found else "not_found",
    }


def format_output(result: dict) -> str:
    if result.get("error"):
        return f"⚠ Error: {result['error']}"

    status = "✓ VERIFIED" if result["verified"] else "✗ NOT FOUND"
    lines = [
        f"{status}: '{result['word_searched']}' in {result['ref']}",
        f"  Sefaria ref: {result['sefaria_ref']}",
        f"  Hebrew text: {result['hebrew_text'][:150]}",
        f"  Confidence: {result['confidence']}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(__doc__)
        sys.exit(1)

    # Handle multi-word book names (e.g., I Chronicles 21 1 word)
    args = sys.argv[1:]
    chapter_idx = next((i for i, a in enumerate(args) if a.isdigit()), None)
    if chapter_idx is not None and chapter_idx > 0:
        book = " ".join(args[:chapter_idx])
        rest = args[chapter_idx:]
    else:
        book = args[0]
        rest = args[1:]

    chapter = int(rest[0])
    verse = int(rest[1])
    word = rest[2]

    result = verify(book, chapter, verse, word)
    print(format_output(result))
