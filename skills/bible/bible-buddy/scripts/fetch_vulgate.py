"""Fetch Latin Vulgate text from sacredbible.org (Hetzenauer 1914 Clementine).

Source: sacredbible.org — Clementine Vulgate, 73 books (full Catholic canon).
Public domain.

Usage:
    python fetch_vulgate.py <book> <chapter> [start_verse] [end_verse]
    python fetch_vulgate.py list

Examples:
    python fetch_vulgate.py Genesis 1 1 5
    python fetch_vulgate.py 創世記 1 1 3
    python fetch_vulgate.py Isaiah 7 14
    python fetch_vulgate.py Tobit 1 1 5
    python fetch_vulgate.py 智慧篇 2 12 20
    python fetch_vulgate.py list
"""

import os
import re
import sys
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "https://www.sacredbible.org/vulgate1914"
CACHE_DIR = os.path.expanduser("~/.cache/bible-buddy/vulgate1914")

# ── Book catalog: (file_path, latin_name, english_name, chinese_name) ──
BOOKS = [
    ("VT-01_Genesis.htm",          "Genesis",          "Genesis",          "創世記"),
    ("VT-02_Exodus.htm",           "Exodus",           "Exodus",           "出埃及記"),
    ("VT-03_Leviticus.htm",        "Leviticus",        "Leviticus",        "利未記"),
    ("VT-04_Numeri.htm",           "Numeri",           "Numbers",          "民數記"),
    ("VT-05_Deuteronomium.htm",    "Deuteronomium",    "Deuteronomy",      "申命記"),
    ("VT-06_Josue.htm",            "Josue",            "Joshua",           "約書亞記"),
    ("VT-07_Judices.htm",          "Judices",          "Judges",           "士師記"),
    ("VT-08_Ruth.htm",             "Ruth",             "Ruth",             "路得記"),
    ("VT-09_1-Samuel.htm",         "I Samuel",         "1 Samuel",         "撒母耳記上"),
    ("VT-10_2-Samuel.htm",         "II Samuel",        "2 Samuel",         "撒母耳記下"),
    ("VT-11_1-Reges.htm",          "I Reges",          "1 Kings",          "列王紀上"),
    ("VT-12_2-Reges.htm",          "II Reges",         "2 Kings",          "列王紀下"),
    ("VT-13_1-Paralipomenon.htm",  "I Paralipomenon",  "1 Chronicles",     "歷代志上"),
    ("VT-14_2-Paralipomenon.htm",  "II Paralipomenon", "2 Chronicles",     "歷代志下"),
    ("VT-15_Esdras.htm",           "Esdras",           "Ezra",             "以斯拉記"),
    ("VT-16_Nehemias.htm",         "Nehemias",         "Nehemiah",         "尼希米記"),
    ("VT-17_Tobias.htm",           "Tobias",           "Tobit",            "多俾亞傳"),
    ("VT-18_Judith.htm",           "Judith",           "Judith",           "友弟德傳"),
    ("VT-19_Esther.htm",           "Esther",           "Esther",           "以斯帖記"),
    ("VT-20_Job.htm",              "Job",              "Job",              "約伯記"),
    ("VT-21_Psalmi.htm",           "Psalmi",           "Psalms",           "詩篇"),
    ("VT-22_Proverbia.htm",        "Proverbia",        "Proverbs",         "箴言"),
    ("VT-23_Ecclesiastes.htm",     "Ecclesiastes",     "Ecclesiastes",     "傳道書"),
    ("VT-24_Canticum.htm",         "Canticum",         "Song of Songs",    "雅歌"),
    ("VT-25_Sapientia.htm",        "Sapientia",        "Wisdom",           "智慧篇"),
    ("VT-26_Ecclesiasticus.htm",   "Ecclesiasticus",   "Sirach",           "德訓篇"),
    ("VT-27_Isaias.htm",           "Isaias",           "Isaiah",           "以賽亞書"),
    ("VT-28_Jeremias.htm",         "Jeremias",         "Jeremiah",         "耶利米書"),
    ("VT-29_Lamentationes.htm",    "Lamentationes",    "Lamentations",     "哀歌"),
    ("VT-30_Baruch.htm",           "Baruch",           "Baruch",           "巴錄書"),
    ("VT-31_Ezechiel.htm",         "Ezechiel",         "Ezekiel",          "以西結書"),
    ("VT-32_Daniel.htm",           "Daniel",           "Daniel",           "但以理書"),
    ("VT-33_Osee.htm",             "Osee",             "Hosea",            "何西阿書"),
    ("VT-34_Joel.htm",             "Joel",             "Joel",             "約珥書"),
    ("VT-35_Amos.htm",             "Amos",             "Amos",             "阿摩司書"),
    ("VT-36_Abdias.htm",           "Abdias",           "Obadiah",          "俄巴底亞書"),
    ("VT-37_Jonas.htm",            "Jonas",            "Jonah",            "約拿書"),
    ("VT-38_Michaeas.htm",         "Michaeas",         "Micah",            "彌迦書"),
    ("VT-39_Nahum.htm",            "Nahum",            "Nahum",            "那鴻書"),
    ("VT-40_Habacuc.htm",          "Habacuc",          "Habakkuk",         "哈巴谷書"),
    ("VT-41_Sophonias.htm",        "Sophonias",        "Zephaniah",        "西番雅書"),
    ("VT-42_Aggaeus.htm",          "Aggaeus",          "Haggai",           "哈該書"),
    ("VT-43_Zacharias.htm",        "Zacharias",        "Zechariah",        "撒迦利亞書"),
    ("VT-44_Malachias.htm",        "Malachias",        "Malachi",          "瑪拉基書"),
    ("VT-45_1-Machabaeus.htm",     "I Machabaeus",     "1 Maccabees",      "瑪加伯上"),
    ("VT-46_2-Machabaeus.htm",     "II Machabaeus",    "2 Maccabees",      "瑪加伯下"),
    ("NT-01_Matthaeus.htm",        "Matthaeus",        "Matthew",          "馬太福音"),
    ("NT-02_Marcus.htm",           "Marcus",           "Mark",             "馬可福音"),
    ("NT-03_Lucas.htm",            "Lucas",            "Luke",             "路加福音"),
    ("NT-04_Joannes.htm",          "Joannes",          "John",             "約翰福音"),
    ("NT-05_Actus.htm",            "Actus",            "Acts",             "使徒行傳"),
    ("NT-06_Romani.htm",           "Romani",           "Romans",           "羅馬書"),
    ("NT-07_1-Corinthii.htm",      "I Corinthii",      "1 Corinthians",    "哥林多前書"),
    ("NT-08_2-Corinthii.htm",      "II Corinthii",     "2 Corinthians",    "哥林多後書"),
    ("NT-09_Galatae.htm",          "Galatae",          "Galatians",        "加拉太書"),
    ("NT-10_Ephesii.htm",          "Ephesii",          "Ephesians",        "以弗所書"),
    ("NT-11_Philippenses.htm",     "Philippenses",     "Philippians",      "腓立比書"),
    ("NT-12_Colossenses.htm",      "Colossenses",      "Colossians",       "歌羅西書"),
    ("NT-13_1-Thessalonicenses.htm","I Thessalonicenses","1 Thessalonians", "帖撒羅尼迦前書"),
    ("NT-14_2-Thessalonicenses.htm","II Thessalonicenses","2 Thessalonians","帖撒羅尼迦後書"),
    ("NT-15_1-Timotheus.htm",      "I Timotheus",      "1 Timothy",        "提摩太前書"),
    ("NT-16_2-Timotheus.htm",      "II Timotheus",     "2 Timothy",        "提摩太後書"),
    ("NT-17_Titus.htm",            "Titus",            "Titus",            "提多書"),
    ("NT-18_Philemon.htm",         "Philemon",         "Philemon",         "腓利門書"),
    ("NT-19_Hebraei.htm",          "Hebraei",          "Hebrews",          "希伯來書"),
    ("NT-20_Jacobus.htm",          "Jacobus",          "James",            "雅各書"),
    ("NT-21_1-Petrus.htm",         "I Petrus",         "1 Peter",          "彼得前書"),
    ("NT-22_2-Petrus.htm",         "II Petrus",        "2 Peter",          "彼得後書"),
    ("NT-23_1-Joannes.htm",        "I Joannes",        "1 John",           "約翰一書"),
    ("NT-24_2-Joannes.htm",        "II Joannes",       "2 John",           "約翰二書"),
    ("NT-25_3-Joannes.htm",        "III Joannes",      "3 John",           "約翰三書"),
    ("NT-26_Judas.htm",            "Judas",            "Jude",             "猶大書"),
    ("NT-27_Apocalypsis.htm",      "Apocalypsis",      "Revelation",       "啟示錄"),
]

# Build lookup
_LOOKUP = {}
for fpath, lat, en, zh in BOOKS:
    _LOOKUP[lat.lower()] = fpath
    _LOOKUP[en.lower()] = fpath
    _LOOKUP[zh] = fpath
    # Single word aliases
    for w in en.lower().split():
        if len(w) > 2 and w not in ('the', 'of'):
            _LOOKUP[w] = fpath

_ALIASES = {
    "gen": "VT-01_Genesis.htm", "ex": "VT-02_Exodus.htm",
    "lev": "VT-03_Leviticus.htm", "num": "VT-04_Numeri.htm",
    "deut": "VT-05_Deuteronomium.htm", "josh": "VT-06_Josue.htm",
    "judg": "VT-07_Judices.htm", "1sam": "VT-09_1-Samuel.htm",
    "2sam": "VT-10_2-Samuel.htm", "1kgs": "VT-11_1-Reges.htm",
    "2kgs": "VT-12_2-Reges.htm", "1chr": "VT-13_1-Paralipomenon.htm",
    "2chr": "VT-14_2-Paralipomenon.htm",
    "ezra": "VT-15_Esdras.htm", "neh": "VT-16_Nehemias.htm",
    "tob": "VT-17_Tobias.htm", "jdt": "VT-18_Judith.htm",
    "esth": "VT-19_Esther.htm", "ps": "VT-21_Psalmi.htm",
    "prov": "VT-22_Proverbia.htm", "eccl": "VT-23_Ecclesiastes.htm",
    "song": "VT-24_Canticum.htm", "wis": "VT-25_Sapientia.htm",
    "sir": "VT-26_Ecclesiasticus.htm", "isa": "VT-27_Isaias.htm",
    "jer": "VT-28_Jeremias.htm", "lam": "VT-29_Lamentationes.htm",
    "bar": "VT-30_Baruch.htm", "ezek": "VT-31_Ezechiel.htm",
    "dan": "VT-32_Daniel.htm", "hos": "VT-33_Osee.htm",
    "joel": "VT-34_Joel.htm", "amos": "VT-35_Amos.htm",
    "obad": "VT-36_Abdias.htm", "jonah": "VT-37_Jonas.htm",
    "mic": "VT-38_Michaeas.htm", "nah": "VT-39_Nahum.htm",
    "hab": "VT-40_Habacuc.htm", "zeph": "VT-41_Sophonias.htm",
    "hag": "VT-42_Aggaeus.htm", "zech": "VT-43_Zacharias.htm",
    "mal": "VT-44_Malachias.htm",
    "1macc": "VT-45_1-Machabaeus.htm", "2macc": "VT-46_2-Machabaeus.htm",
    "matt": "NT-01_Matthaeus.htm", "mk": "NT-02_Marcus.htm",
    "lk": "NT-03_Lucas.htm", "jn": "NT-04_Joannes.htm",
    "acts": "NT-05_Actus.htm", "rom": "NT-06_Romani.htm",
    "1cor": "NT-07_1-Corinthii.htm", "2cor": "NT-08_2-Corinthii.htm",
    "gal": "NT-09_Galatae.htm", "eph": "NT-10_Ephesii.htm",
    "phil": "NT-11_Philippenses.htm", "col": "NT-12_Colossenses.htm",
    "1thess": "NT-13_1-Thessalonicenses.htm",
    "2thess": "NT-14_2-Thessalonicenses.htm",
    "1tim": "NT-15_1-Timotheus.htm", "2tim": "NT-16_2-Timotheus.htm",
    "titus": "NT-17_Titus.htm", "phlm": "NT-18_Philemon.htm",
    "heb": "NT-19_Hebraei.htm", "jas": "NT-20_Jacobus.htm",
    "1pet": "NT-21_1-Petrus.htm", "2pet": "NT-22_2-Petrus.htm",
    "1jn": "NT-23_1-Joannes.htm", "2jn": "NT-24_2-Joannes.htm",
    "3jn": "NT-25_3-Joannes.htm", "jude": "NT-26_Judas.htm",
    "rev": "NT-27_Apocalypsis.htm",
}
_LOOKUP.update(_ALIASES)


def _resolve_book(name: str):
    """Resolve book name → (file_path, latin, english, chinese)."""
    key = name.strip()
    fpath = _LOOKUP.get(key) or _LOOKUP.get(key.lower())
    if not fpath:
        # Partial match
        low = key.lower()
        for k, v in _LOOKUP.items():
            if low in k or k in low:
                fpath = v
                break
    if not fpath:
        return None
    for row in BOOKS:
        if row[0] == fpath:
            return row
    return None


def _download(file_path: str) -> str:
    """Download and cache a book page."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, file_path.replace("/", "_"))
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8", errors="replace") as f:
            return f.read()

    url = f"{BASE_URL}/{file_path}"
    req = urllib.request.Request(url, headers={"User-Agent": "bible-buddy-skill/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
        # sacredbible.org uses windows-1252 encoding
        data = raw.decode("windows-1252", errors="replace")
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(data)
        return data
    except urllib.error.URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _parse_verses(html: str) -> dict:
    """Parse {chapter:verse} formatted text into {(ch, vs): text}."""
    verses = {}
    # Pattern: {chapter:verse} text<BR> or {chapter:verse} text\n
    for m in re.finditer(r'\{(\d+):(\d+)\}\s*(.+?)(?=\{|\Z)', html, re.DOTALL):
        ch = int(m.group(1))
        vs = int(m.group(2))
        text = m.group(3).strip()
        # Clean HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Clean brackets (editorial marks)
        text = text.strip()
        if text:
            verses[(ch, vs)] = text
    return verses


def cmd_list():
    print("=== Latin Vulgate — Clementine (Hetzenauer 1914) ===")
    print("Source: sacredbible.org (public domain)\n")

    cats = [
        ("Pentateuch", BOOKS[:5]),
        ("Historical", BOOKS[5:19]),
        ("Poetry & Wisdom", BOOKS[19:26]),
        ("Prophets", BOOKS[26:46]),
        ("Gospels & Acts", BOOKS[46:51]),
        ("Pauline Epistles", BOOKS[51:64]),
        ("Catholic Epistles & Revelation", BOOKS[64:]),
    ]
    for cat, items in cats:
        print(f"── {cat} ──")
        for _, lat, en, zh in items:
            print(f"  {en:<25} {lat:<25} {zh}")
        print()


def cmd_fetch(book_name: str, chapter: int,
              start_verse: int | None = None, end_verse: int | None = None):
    book = _resolve_book(book_name)
    if not book:
        print(f"Error: unknown book '{book_name}'. Use 'list' for catalog.", file=sys.stderr)
        sys.exit(1)

    fpath, lat, en, zh = book
    html = _download(fpath)
    verses = _parse_verses(html)

    # Filter
    ev = end_verse if end_verse is not None else (start_verse if start_verse is not None else None)
    filtered = {}
    for (ch, vs), text in verses.items():
        if ch != chapter:
            continue
        if start_verse is not None and (vs < start_verse or (ev is not None and vs > ev)):
            continue
        filtered[(ch, vs)] = text

    if not filtered:
        all_ch = sorted(set(ch for ch, _ in verses.keys()))
        if all_ch:
            print(f"Error: {en} chapter {chapter} not found. Available: {all_ch[0]}-{all_ch[-1]}",
                  file=sys.stderr)
        else:
            print(f"Error: could not parse {en}.", file=sys.stderr)
        sys.exit(1)

    ref = f"{chapter}"
    if start_verse is not None:
        ref += f":{start_verse}"
        if ev is not None and ev != start_verse:
            ref += f"-{ev}"

    print(f"📖 {en} ({zh}) {ref}")
    print(f"Vulgata Clementina (Hetzenauer 1914)\n")

    for (ch, vs) in sorted(filtered.keys()):
        print(f"  [{vs}] {filtered[(ch, vs)]}")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0)

    if args[0] == "list":
        cmd_list()
        return

    book = args[0]
    if len(args) < 2:
        print("Usage: fetch_vulgate.py <book> <chapter> [start_verse] [end_verse]",
              file=sys.stderr)
        sys.exit(1)

    try:
        chapter = int(args[1])
        start_v = int(args[2]) if len(args) > 2 else None
        end_v = int(args[3]) if len(args) > 3 else None
    except ValueError:
        # Multi-word book: "Song of Songs", "1 Maccabees"
        for i in range(1, len(args)):
            try:
                chapter = int(args[i])
                book = " ".join(args[:i])
                start_v = int(args[i + 1]) if len(args) > i + 1 else None
                end_v = int(args[i + 2]) if len(args) > i + 2 else None
                break
            except (ValueError, IndexError):
                continue
        else:
            print("Error: could not parse chapter number.", file=sys.stderr)
            sys.exit(1)

    cmd_fetch(book, chapter, start_v, end_v)


if __name__ == "__main__":
    main()
