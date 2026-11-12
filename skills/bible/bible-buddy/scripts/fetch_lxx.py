"""Fetch Septuagint (LXX) Greek text from CenterBLC/LXX (Rahlfs 1935) via Text-Fabric.

Source: CenterBLC/LXX — Rahlfs' critical edition (CATSS/UPenn data).
Covers: 57 books including deuterocanon, Psalms of Solomon, Daniel/Susanna/Bel OG+Th.
Features: Greek text, English glosses, morphology, Strong's numbers.

Usage:
    python fetch_lxx.py <book> <chapter> [start_verse] [end_verse]
    python fetch_lxx.py list

Examples:
    python fetch_lxx.py Genesis 1 1 5
    python fetch_lxx.py 創世記 1 1 3
    python fetch_lxx.py Isaiah 7 14
    python fetch_lxx.py "Psalms of Solomon" 17 21
    python fetch_lxx.py 所羅門詩篇 17 21 32
    python fetch_lxx.py Daniel-OG 7 13 14
    python fetch_lxx.py Daniel-Th 7 13 14
    python fetch_lxx.py Susanna-OG 1 1 5
    python fetch_lxx.py list
"""

import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = os.path.expanduser("~/.cache/bible-buddy/CenterBLC-LXX")
TF_PATH = os.path.join(DATA_DIR, "tf")
REPO_URL = "https://github.com/CenterBLC/LXX.git"

# ── Book name mapping: TF name → (English, Chinese) ─────────────────
BOOK_INFO = {
    "Gen":    ("Genesis",           "創世記"),
    "Exod":   ("Exodus",            "出埃及記"),
    "Lev":    ("Leviticus",         "利未記"),
    "Num":    ("Numbers",           "民數記"),
    "Deut":   ("Deuteronomy",       "申命記"),
    "Josh":   ("Joshua",            "約書亞記"),
    "Judg":   ("Judges",            "士師記"),
    "Ruth":   ("Ruth",              "路得記"),
    "1Sam":   ("1 Samuel",          "撒母耳記上"),
    "2Sam":   ("2 Samuel",          "撒母耳記下"),
    "1Kgs":   ("1 Kings",           "列王紀上"),
    "2Kgs":   ("2 Kings",           "列王紀下"),
    "1Chr":   ("1 Chronicles",      "歷代志上"),
    "2Chr":   ("2 Chronicles",      "歷代志下"),
    "1Esdr":  ("1 Esdras",          "以斯拉一書"),
    "2Esdr":  ("Ezra-Nehemiah",     "以斯拉-尼希米"),
    "Esth":   ("Esther",            "以斯帖記"),
    "Jdt":    ("Judith",            "友弟德傳"),
    "TobBA":  ("Tobit (BA)",        "多俾亞傳(BA)"),
    "TobS":   ("Tobit (S)",         "多俾亞傳(S)"),
    "1Mac":   ("1 Maccabees",       "瑪加伯上"),
    "2Mac":   ("2 Maccabees",       "瑪加伯下"),
    "3Mac":   ("3 Maccabees",       "瑪加伯三書"),
    "4Mac":   ("4 Maccabees",       "瑪加伯四書"),
    "Ps":     ("Psalms",            "詩篇"),
    "Od":     ("Odes",              "頌歌集"),
    "Prov":   ("Proverbs",          "箴言"),
    "Qoh":    ("Ecclesiastes",      "傳道書"),
    "Cant":   ("Song of Songs",     "雅歌"),
    "Job":    ("Job",               "約伯記"),
    "Wis":    ("Wisdom of Solomon", "智慧篇"),
    "Sir":    ("Sirach",            "德訓篇"),
    "PsSol":  ("Psalms of Solomon", "所羅門詩篇"),
    "Hos":    ("Hosea",             "何西阿書"),
    "Mic":    ("Micah",             "彌迦書"),
    "Amos":   ("Amos",              "阿摩司書"),
    "Joel":   ("Joel",              "約珥書"),
    "Jonah":  ("Jonah",             "約拿書"),
    "Obad":   ("Obadiah",           "俄巴底亞書"),
    "Nah":    ("Nahum",             "那鴻書"),
    "Hab":    ("Habakkuk",          "哈巴谷書"),
    "Zeph":   ("Zephaniah",         "西番雅書"),
    "Hag":    ("Haggai",            "哈該書"),
    "Zech":   ("Zechariah",         "撒迦利亞書"),
    "Mal":    ("Malachi",           "瑪拉基書"),
    "Isa":    ("Isaiah",            "以賽亞書"),
    "Jer":    ("Jeremiah",          "耶利米書"),
    "Bar":    ("Baruch",            "巴錄書"),
    "EpJer":  ("Letter of Jeremiah","耶利米書信"),
    "Lam":    ("Lamentations",      "哀歌"),
    "Ezek":   ("Ezekiel",           "以西結書"),
    "Bel":    ("Bel and Dragon-OG", "比勒與大龍(古希臘)"),
    "BelTh":  ("Bel and Dragon-Th", "比勒與大龍(提奧多田)"),
    "Dan":    ("Daniel-OG",         "但以理書(古希臘)"),
    "DanTh":  ("Daniel-Th",         "但以理書(提奧多田)"),
    "Sus":    ("Susanna-OG",        "蘇撒拿傳(古希臘)"),
    "SusTh":  ("Susanna-Th",        "蘇撒拿傳(提奧多田)"),
}

# Build lookup: lowercase English/Chinese/alias → TF book name
_LOOKUP = {}
for tf_name, (en, zh) in BOOK_INFO.items():
    _LOOKUP[en.lower()] = tf_name
    _LOOKUP[zh] = tf_name
    _LOOKUP[tf_name.lower()] = tf_name
    # Single-word aliases
    for part in en.lower().split():
        if len(part) > 2 and part not in ('the', 'and', 'of'):
            _LOOKUP[part] = tf_name

# Additional aliases
_EXTRA = {
    "gen": "Gen", "ex": "Exod", "exod": "Exod", "lev": "Lev",
    "num": "Num", "deut": "Deut", "josh": "Josh", "judg": "Judg",
    "1sam": "1Sam", "2sam": "2Sam", "1kgs": "1Kgs", "2kgs": "2Kgs",
    "1chr": "1Chr", "2chr": "2Chr",
    "ezra": "2Esdr", "neh": "2Esdr", "以斯拉記": "2Esdr", "尼希米記": "2Esdr",
    "esth": "Esth", "ps": "Ps", "prov": "Prov",
    "eccl": "Qoh", "song": "Cant", "job": "Job",
    "isa": "Isa", "jer": "Jer", "lam": "Lam", "ezek": "Ezek",
    "dan": "DanTh", "dan-og": "Dan", "dan-th": "DanTh",
    "daniel": "DanTh", "daniel-og": "Dan", "daniel-th": "DanTh",
    "但以理書": "DanTh",
    "hos": "Hos", "joel": "Joel", "amos": "Amos",
    "obad": "Obad", "jonah": "Jonah", "mic": "Mic",
    "nah": "Nah", "hab": "Hab", "zeph": "Zeph",
    "hag": "Hag", "zech": "Zech", "mal": "Mal",
    "bar": "Bar", "wis": "Wis", "sir": "Sir",
    "tob": "TobBA", "tobit": "TobBA", "多俾亞傳": "TobBA",
    "jdt": "Jdt", "1macc": "1Mac", "2macc": "2Mac",
    "3macc": "3Mac", "4macc": "4Mac",
    "pssol": "PsSol", "odes": "Od",
    "sus": "SusTh", "sus-og": "Sus", "sus-th": "SusTh",
    "susanna": "SusTh", "susanna-og": "Sus", "susanna-th": "SusTh",
    "蘇撒拿傳": "SusTh",
    "bel": "BelTh", "bel-og": "Bel", "bel-th": "BelTh",
    "比勒與大龍": "BelTh",
    "epjer": "EpJer", "耶利米書信": "EpJer",
    "巴錄書": "Bar",
}
_LOOKUP.update(_EXTRA)


def _resolve_book(name: str) -> str | None:
    key = name.strip()
    if key in _LOOKUP:
        return _LOOKUP[key]
    low = key.lower()
    if low in _LOOKUP:
        return _LOOKUP[low]
    for k, v in _LOOKUP.items():
        if low in k.lower() or k.lower() in low:
            return v
    return None


def _ensure_data():
    """Download CenterBLC/LXX tf data if not cached."""
    if os.path.isdir(os.path.join(TF_PATH, "1935")):
        return
    print("Downloading CenterBLC/LXX data (first run only)...", file=sys.stderr)
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = DATA_DIR + "_tmp"
    subprocess.run([
        "git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
        REPO_URL, tmp,
    ], check=True, capture_output=True)
    subprocess.run(
        ["git", "sparse-checkout", "set", "tf"],
        cwd=tmp, check=True, capture_output=True,
    )
    os.rename(os.path.join(tmp, "tf"), TF_PATH)
    subprocess.run(["rm", "-rf", tmp], capture_output=True)
    print("Done.", file=sys.stderr)


def _load():
    """Load LXX Text-Fabric dataset."""
    _ensure_data()
    from tf.fabric import Fabric
    TF = Fabric(locations=TF_PATH, modules="1935", silent="deep")
    return TF.load("book chapter verse word gloss sp", silent="deep")


def cmd_list(api):
    F = api.F
    print("=== Septuagint (LXX) — Rahlfs 1935 ===")
    print("Source: CenterBLC/LXX (CATSS/UPenn)\n")

    categories = [
        ("Torah / Pentateuch", ["Gen", "Exod", "Lev", "Num", "Deut"]),
        ("Historical Books", ["Josh", "Judg", "Ruth", "1Sam", "2Sam", "1Kgs", "2Kgs",
                              "1Chr", "2Chr", "1Esdr", "2Esdr", "Esth"]),
        ("Deuterocanon / Apocrypha", ["Jdt", "TobBA", "TobS", "1Mac", "2Mac", "3Mac",
                                       "4Mac", "Wis", "Sir", "PsSol", "Bar", "EpJer"]),
        ("Poetry & Wisdom", ["Ps", "Od", "Prov", "Qoh", "Cant", "Job"]),
        ("Prophets", ["Hos", "Mic", "Amos", "Joel", "Jonah", "Obad", "Nah", "Hab",
                       "Zeph", "Hag", "Zech", "Mal", "Isa", "Jer", "Lam", "Ezek"]),
        ("Daniel & Additions (OG + Theodotion)", ["Dan", "DanTh", "Sus", "SusTh",
                                                    "Bel", "BelTh"]),
    ]

    # Collect word counts
    word_counts = {}
    for w in F.otype.s('word'):
        bk = F.book.v(w)
        word_counts[bk] = word_counts.get(bk, 0) + 1

    for cat_name, book_list in categories:
        print(f"── {cat_name} ──")
        for tf_name in book_list:
            if tf_name in BOOK_INFO:
                en, zh = BOOK_INFO[tf_name]
                wc = word_counts.get(tf_name, 0)
                if wc > 0:
                    print(f"  {en:<30} {zh:<12} {wc:>7} words")
        print()


def cmd_fetch(api, book_name: str, chapter: int,
              start_verse: int | None = None, end_verse: int | None = None):
    F = api.F

    tf_name = _resolve_book(book_name)
    if not tf_name:
        print(f"Error: unknown book '{book_name}'. Use 'list' for catalog.", file=sys.stderr)
        sys.exit(1)

    if tf_name not in BOOK_INFO:
        print(f"Error: book '{tf_name}' not in catalog.", file=sys.stderr)
        sys.exit(1)

    en_name, zh_name = BOOK_INFO[tf_name]
    ev = end_verse if end_verse is not None else (start_verse if start_verse is not None else None)

    # Collect verses
    verses = {}
    for w in F.otype.s('word'):
        if F.book.v(w) != tf_name:
            continue
        ch = F.chapter.v(w)
        if ch != chapter:
            continue
        vs = F.verse.v(w)
        if start_verse is not None and (vs < start_verse or (ev is not None and vs > ev)):
            continue
        verses.setdefault(vs, []).append(w)

    if not verses:
        # Find available chapters
        chapters = set()
        for w in F.otype.s('word'):
            if F.book.v(w) == tf_name:
                chapters.add(F.chapter.v(w))
        if chapters:
            ch_range = sorted(chapters)
            print(f"Error: {en_name} chapter {chapter} not found. Available: {ch_range[0]}-{ch_range[-1]}",
                  file=sys.stderr)
        else:
            print(f"Error: {en_name} not found.", file=sys.stderr)
        sys.exit(1)

    # Header
    ref = f"{chapter}"
    if start_verse is not None:
        ref += f":{start_verse}"
        if ev is not None and ev != start_verse:
            ref += f"-{ev}"

    print(f"📖 {en_name} ({zh_name}) {ref}")
    print(f"LXX Rahlfs 1935\n")

    for vs in sorted(verses.keys()):
        word_nodes = verses[vs]
        text = " ".join(F.word.v(w) for w in word_nodes)
        print(f"  [{vs}] {text}")

    # Show glosses for single verse or short range
    total_vs = len(verses)
    if total_vs <= 3:
        print(f"\n  ── Glosses ──")
        for vs in sorted(verses.keys()):
            for w in verses[vs]:
                wd = F.word.v(w)
                gl = F.gloss.v(w) or ""
                sp_val = F.sp.v(w) or ""
                if gl:
                    print(f"    {wd:<20} {gl:<30} [{sp_val}]")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0)

    api = _load()

    if args[0] == "list":
        cmd_list(api)
        return

    book = args[0]
    if len(args) < 2:
        print("Usage: fetch_lxx.py <book> <chapter> [start_verse] [end_verse]", file=sys.stderr)
        sys.exit(1)

    try:
        chapter = int(args[1])
        start_v = int(args[2]) if len(args) > 2 else None
        end_v = int(args[3]) if len(args) > 3 else None
    except ValueError:
        # Multi-word book name: "Psalms of Solomon"
        book = " ".join(args[:len(args) - (len(args) - 1 if len(args) > 1 else 0)])
        # Find where chapter starts
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

    cmd_fetch(api, book, chapter, start_v, end_v)


if __name__ == "__main__":
    main()
