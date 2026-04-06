"""Fetch Septuagint (LXX) Greek text from Swete's edition via GitHub.

Source: nathans/lxx-swete (MIT license), Swete's Septuagint (1894-1930).
Covers: Full LXX including deuterocanon, Psalms of Solomon, Daniel OG/Th.

Usage:
    python fetch_lxx.py <book> <chapter> [start_verse] [end_verse]
    python fetch_lxx.py list

Examples:
    python fetch_lxx.py Genesis 1 1 5
    python fetch_lxx.py 創世記 1 1 3
    python fetch_lxx.py Isaiah 7 14
    python fetch_lxx.py "Psalms of Solomon" 17 23 36
    python fetch_lxx.py 所羅門詩篇 17 23 36
    python fetch_lxx.py Daniel-OG 3 1 5
    python fetch_lxx.py Daniel-Th 3 1 5
    python fetch_lxx.py Susanna-OG 1
    python fetch_lxx.py list
"""

import os
import sys
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "https://raw.githubusercontent.com/nathans/lxx-swete/master/data"
CACHE_DIR = os.path.expanduser("~/.cache/bible-buddy/lxx-swete")

# ── Book catalog: (file_stem, display_name, display_name_zh) ──────────
BOOKS = [
    ("01.Genesis",          "Genesis",          "創世記"),
    ("02.Exodus",           "Exodus",           "出埃及記"),
    ("03.Leviticus",        "Leviticus",        "利未記"),
    ("04.Numeri",           "Numbers",          "民數記"),
    ("05.Deuteronomium",    "Deuteronomy",      "申命記"),
    ("06.Josue",            "Joshua",           "約書亞記"),
    ("08.Judices",          "Judges",           "士師記"),
    ("10.Ruth",             "Ruth",             "路得記"),
    ("11.Regnorum_I",       "1 Samuel",         "撒母耳記上"),
    ("12.Regnorum_II",      "2 Samuel",         "撒母耳記下"),
    ("13.Regnorum_III",     "1 Kings",          "列王紀上"),
    ("14.Regnorum_IV",      "2 Kings",          "列王紀下"),
    ("15.Paralipomenon_I",  "1 Chronicles",     "歷代志上"),
    ("16.Paralipomenon_II", "2 Chronicles",     "歷代志下"),
    ("17.Esdras_A",         "1 Esdras",         "以斯拉一書"),
    ("18.Esdras_B",         "Ezra-Nehemiah",    "以斯拉-尼希米"),
    ("19.Esther",           "Esther",           "以斯帖記"),
    ("20.Judith",           "Judith",           "友弟德傳"),
    ("21.Tobias",           "Tobit",            "多俾亞傳"),
    ("23.Machabaeorum_i",   "1 Maccabees",      "瑪加伯上"),
    ("24.Machabaeorum_ii",  "2 Maccabees",      "瑪加伯下"),
    ("25.Machabaeorum_iii", "3 Maccabees",      "瑪加伯三書"),
    ("26.Machabaeorum_iv",  "4 Maccabees",      "瑪加伯四書"),
    ("27.Psalmi",           "Psalms",           "詩篇"),
    ("28.Odae",             "Odes",             "頌歌集"),
    ("29.Proverbia",        "Proverbs",         "箴言"),
    ("31.Canticum",         "Song of Songs",    "雅歌"),
    ("32.Job",              "Job",              "約伯記"),
    ("33.Sapientia_Salomonis", "Wisdom of Solomon", "智慧篇"),
    ("34.Ecclesiasticus",   "Sirach",           "德訓篇"),
    ("35.Psalmi_Salomonis", "Psalms of Solomon", "所羅門詩篇"),
    ("36.Osee",             "Hosea",            "何西阿書"),
    ("37.Amos",             "Amos",             "阿摩司書"),
    ("38.Michaeas",         "Micah",            "彌迦書"),
    ("39.Joel",             "Joel",             "約珥書"),
    ("40.Abdias",           "Obadiah",          "俄巴底亞書"),
    ("41.Jonas",            "Jonah",            "約拿書"),
    ("42.Nahum",            "Nahum",            "那鴻書"),
    ("43.Habacuc",          "Habakkuk",         "哈巴谷書"),
    ("44.Sophonias",        "Zephaniah",        "西番雅書"),
    ("45.Aggaeus",          "Haggai",           "哈該書"),
    ("46.Zacharias",        "Zechariah",        "撒迦利亞書"),
    ("47.Malachias",        "Malachi",          "瑪拉基書"),
    ("48.Isaias",           "Isaiah",           "以賽亞書"),
    ("49.Jeremias",         "Jeremiah",         "耶利米書"),
    ("50.Baruch",           "Baruch",           "巴錄書"),
    ("51.Threni_seu_Lamentationes", "Lamentations", "哀歌"),
    ("52.Epistula_Jeremiae", "Letter of Jeremiah", "耶利米書信"),
    ("53.Ezechiel",         "Ezekiel",          "以西結書"),
    ("54.Susanna_translatio_Graeca", "Susanna-OG", "蘇撒拿傳(古希臘)"),
    ("55.Susanna_Theodotionis_versio", "Susanna-Th", "蘇撒拿傳(提奧多田)"),
    ("56.Daniel_translatio_Graeca", "Daniel-OG", "但以理書(古希臘)"),
    ("57.Daniel_Theodotionis_versio", "Daniel-Th", "但以理書(提奧多田)"),
    ("58.Bel_et_Draco_translatio_Graeca", "Bel and Dragon-OG", "比勒與大龍(古希臘)"),
    ("59.Bel_et_Draco_Theodotionis_versio", "Bel and Dragon-Th", "比勒與大龍(提奧多田)"),
]

# Build lookup indices
_by_file = {}
_by_name = {}
for stem, en, zh in BOOKS:
    _by_file[stem] = (stem, en, zh)
    _by_name[en.lower()] = stem
    _by_name[zh] = stem
    # Short aliases
    parts = en.lower().split()
    if len(parts) == 1:
        _by_name[parts[0]] = stem

# Extra aliases
_ALIASES = {
    "gen": "01.Genesis", "ex": "02.Exodus", "lev": "03.Leviticus",
    "num": "04.Numeri", "deut": "05.Deuteronomium", "josh": "06.Josue",
    "judg": "08.Judices", "ruth": "10.Ruth",
    "1sam": "11.Regnorum_I", "2sam": "12.Regnorum_II",
    "1kgs": "13.Regnorum_III", "2kgs": "14.Regnorum_IV",
    "1chr": "15.Paralipomenon_I", "2chr": "16.Paralipomenon_II",
    "ezra": "18.Esdras_B", "neh": "18.Esdras_B",
    "esth": "19.Esther", "ps": "27.Psalmi", "prov": "29.Proverbia",
    "eccl": "34.Ecclesiasticus", "song": "31.Canticum",
    "job": "32.Job", "isa": "48.Isaias", "jer": "49.Jeremias",
    "lam": "51.Threni_seu_Lamentationes", "ezek": "53.Ezechiel",
    "dan": "57.Daniel_Theodotionis_versio",
    "dan-og": "56.Daniel_translatio_Graeca",
    "dan-th": "57.Daniel_Theodotionis_versio",
    "hos": "36.Osee", "joel": "39.Joel", "amos": "37.Amos",
    "obad": "40.Abdias", "jonah": "41.Jonas", "mic": "38.Michaeas",
    "nah": "42.Nahum", "hab": "43.Habacuc", "zeph": "44.Sophonias",
    "hag": "45.Aggaeus", "zech": "46.Zacharias", "mal": "47.Malachias",
    "bar": "50.Baruch", "wis": "33.Sapientia_Salomonis",
    "sir": "34.Ecclesiasticus", "tob": "21.Tobias",
    "jdt": "20.Judith", "1macc": "23.Machabaeorum_i",
    "2macc": "24.Machabaeorum_ii", "3macc": "25.Machabaeorum_iii",
    "4macc": "26.Machabaeorum_iv",
    "pssol": "35.Psalmi_Salomonis", "odes": "28.Odae",
    "sus": "55.Susanna_Theodotionis_versio",
    "sus-og": "54.Susanna_translatio_Graeca",
    "sus-th": "55.Susanna_Theodotionis_versio",
    "bel": "59.Bel_et_Draco_Theodotionis_versio",
    "bel-og": "58.Bel_et_Draco_translatio_Graeca",
    "bel-th": "59.Bel_et_Draco_Theodotionis_versio",
    "epjer": "52.Epistula_Jeremiae",
    # Chinese extras
    "傳道書": "34.Ecclesiasticus",
    "以斯拉記": "18.Esdras_B", "尼希米記": "18.Esdras_B",
    "但以理書": "57.Daniel_Theodotionis_versio",
    "蘇撒拿傳": "55.Susanna_Theodotionis_versio",
    "比勒與大龍": "59.Bel_et_Draco_Theodotionis_versio",
    "巴錄書": "50.Baruch",
}
_by_name.update(_ALIASES)


def _resolve_book(name: str) -> str | None:
    """Resolve book name to file stem."""
    key = name.strip()
    if key in _by_name:
        return _by_name[key]
    low = key.lower()
    if low in _by_name:
        return _by_name[low]
    # Partial match
    for k, v in _by_name.items():
        if low in k.lower() or k.lower() in low:
            return v
    return None


def _download(stem: str) -> str:
    """Download and cache a book file. Returns file path."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{stem}.txt")
    if os.path.exists(cache_path):
        return cache_path

    url = f"{BASE_URL}/{stem}.txt"
    req = urllib.request.Request(url, headers={"User-Agent": "bible-buddy-skill/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(cache_path, "wb") as f:
            f.write(data)
        return cache_path
    except urllib.error.URLError as e:
        print(f"Error downloading {url}: {e}", file=sys.stderr)
        sys.exit(1)


def _parse_verses(filepath: str) -> dict:
    """Parse a book file into {(chapter, verse): [words]}."""
    verses = {}
    # Extract the book number prefix from filename
    basename = os.path.basename(filepath).replace(".txt", "")
    book_num = basename.split(".")[0]

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()
            if not line:
                continue
            parts = line.split(" ", 1)
            if len(parts) != 2:
                continue
            ref, word = parts
            # ref format: "booknum.chapter.verse"
            ref_parts = ref.split(".")
            if len(ref_parts) != 3:
                continue
            _, ch, vs = ref_parts
            try:
                ch_num = int(ch)
                vs_num = int(vs)
            except ValueError:
                continue
            key = (ch_num, vs_num)
            verses.setdefault(key, []).append(word)
    return verses


def cmd_list():
    """List all available books."""
    print("=== Septuagint (LXX) — Swete's Edition ===")
    print("Source: github.com/nathans/lxx-swete (MIT)\n")

    categories = [
        ("Torah / Pentateuch", ["01.", "02.", "03.", "04.", "05."]),
        ("Historical Books", ["06.", "08.", "10.", "11.", "12.", "13.", "14.",
                              "15.", "16.", "17.", "18.", "19."]),
        ("Deuterocanon / Apocrypha", ["20.", "21.", "23.", "24.", "25.", "26.",
                                       "33.", "34.", "35.", "50.", "52."]),
        ("Poetry & Wisdom", ["27.", "28.", "29.", "31.", "32."]),
        ("Prophets", ["36.", "37.", "38.", "39.", "40.", "41.", "42.", "43.",
                       "44.", "45.", "46.", "47.", "48.", "49.", "51.", "53."]),
        ("Daniel & Additions (OG + Theodotion)", ["54.", "55.", "56.", "57.", "58.", "59."]),
    ]

    for cat_name, prefixes in categories:
        print(f"── {cat_name} ──")
        for stem, en, zh in BOOKS:
            if any(stem.startswith(p) for p in prefixes):
                print(f"  {en:<30} {zh}")
        print()


def cmd_fetch(book_name: str, chapter: int, start_verse: int | None = None,
              end_verse: int | None = None):
    """Fetch and display LXX text."""
    stem = _resolve_book(book_name)
    if not stem:
        print(f"Error: unknown book '{book_name}'. Use 'list' to see available books.",
              file=sys.stderr)
        sys.exit(1)

    info = _by_file[stem]
    en_name = info[1]
    zh_name = info[2]

    filepath = _download(stem)
    verses = _parse_verses(filepath)

    # Filter by chapter
    chapter_verses = {k: v for k, v in verses.items() if k[0] == chapter}

    if not chapter_verses:
        # List available chapters
        all_chapters = sorted(set(ch for ch, _ in verses.keys()))
        print(f"Error: chapter {chapter} not found in {en_name}.", file=sys.stderr)
        if all_chapters:
            print(f"Available chapters: {all_chapters[0]}-{all_chapters[-1]}", file=sys.stderr)
        sys.exit(1)

    # Filter by verse range (single verse if end_verse not given)
    if start_verse is not None:
        ev = end_verse if end_verse is not None else start_verse
        chapter_verses = {k: v for k, v in chapter_verses.items()
                         if k[1] >= start_verse and k[1] <= ev}

    if not chapter_verses:
        print(f"Error: no matching verses.", file=sys.stderr)
        sys.exit(1)

    print(f"📖 {en_name} ({zh_name}) {chapter}", end="")
    if start_verse is not None:
        print(f":{start_verse}", end="")
        if end_verse is not None and end_verse != start_verse:
            print(f"-{end_verse}", end="")
    print(f"\nLXX Swete's Edition\n")

    for (ch, vs) in sorted(chapter_verses.keys()):
        text = " ".join(chapter_verses[(ch, vs)])
        print(f"  [{vs}] {text}")


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
        print("Usage: fetch_lxx.py <book> <chapter> [start_verse] [end_verse]",
              file=sys.stderr)
        sys.exit(1)

    try:
        chapter = int(args[1])
    except ValueError:
        # Maybe "book name" is two words: "Psalms of Solomon"
        # Try joining first two args
        book = f"{args[0]} {args[1]}"
        if len(args) < 3:
            print("Usage: fetch_lxx.py <book> <chapter> [start_verse] [end_verse]",
                  file=sys.stderr)
            sys.exit(1)
        chapter = int(args[2])
        start_v = int(args[3]) if len(args) > 3 else None
        end_v = int(args[4]) if len(args) > 4 else None
        cmd_fetch(book, chapter, start_v, end_v)
        return

    start_v = int(args[2]) if len(args) > 2 else None
    end_v = int(args[3]) if len(args) > 3 else None
    cmd_fetch(book, chapter, start_v, end_v)


if __name__ == "__main__":
    main()
