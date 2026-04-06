"""Fetch scripture and extra-canonical text from Sefaria.org API.

Covers: Tanakh, Second Temple literature (Josephus, Philo, Apocrypha,
Pseudepigrapha available on Sefaria). Does NOT cover NT.

Usage:
    python fetch_sefaria.py <book> <chapter> [start_verse] [end_verse]
    python fetch_sefaria.py list-extra

Examples:
    python fetch_sefaria.py 以賽亞書 7
    python fetch_sefaria.py Isaiah 7 10 17
    python fetch_sefaria.py Gen 1 1 3
    python fetch_sefaria.py Jubilees 1
    python fetch_sefaria.py Josephus Antiquities 1 1
    python fetch_sefaria.py "Ben Sira" 1 1 5
    python fetch_sefaria.py 禧年書 2
    python fetch_sefaria.py list-extra
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


# ── Extra-canonical texts on Sefaria ──────────────────────────────────
# (lookup_key, sefaria_title, display_name, ref_style)
# ref_style: "ch" = Title.Chapter, "ch.sec" = Title.Chapter.Section (Josephus/Philo)
EXTRA_CANON = [
    # Apocrypha / Deuterocanon
    ("jubilees",            "Book of Jubilees",           "禧年書",          "ch"),
    ("ben sira",            "Ben Sira",                   "德訓篇(Ben Sira)", "ch"),
    ("sirach",              "Ben Sira",                   "德訓篇(Ben Sira)", "ch"),
    ("tobit",               "Book of Tobit",              "多俾亞傳",        "ch"),
    ("judith",              "Book of Judith",             "友弟德傳",        "ch"),
    ("1 maccabees",         "The Book of Maccabees I",    "瑪加伯上",        "ch"),
    ("1 maccabees kahana",  "The Book of Maccabees I (Kahana Translation)", "瑪加伯上(Kahana校勘版)", "ch"),
    ("2 maccabees",         "The Book of Maccabees II",   "瑪加伯下",        "ch"),
    ("wisdom of solomon",   "The Wisdom of Solomon",      "智慧篇",          "ch"),
    ("wisdom",              "The Wisdom of Solomon",      "智慧篇",          "ch"),
    ("susanna",             "The Book of Susanna",        "蘇撒拿傳",        "ch"),
    ("letter of aristeas",  "Letter of Aristeas",         "亞里斯提亞書信",   "ch"),
    ("prayer of manasseh",  "Prayer of Manasseh",         "瑪拿西禱詞",      "ch"),
    ("psalm 151",           "Psalm 151",                  "詩篇 151",        "ch"),
    ("psalm 154",           "Psalm 154",                  "詩篇 154",        "ch"),
    ("testaments reuben",    "The Testaments of the Twelve Patriarchs, The Testament of Reuben the First born Son of Jacob and Leah", "十二族長遺訓：流便", "ch"),
    ("testaments simeon",    "The Testaments of the Twelve Patriarchs, The Testament of Simeon the Second of Jacob and Leah", "十二族長遺訓：西緬", "ch"),
    ("testaments levi",      "The Testaments of the Twelve Patriarchs, The Testament of Levi the Third Son of Jacob and Leah", "十二族長遺訓：利未", "ch"),
    ("testaments judah",     "The Testaments of the Twelve Patriarchs, The Testament of Judah the Fourth Son of Jacob and Leah", "十二族長遺訓：猶大", "ch"),
    ("testaments issachar",  "The Testaments of the Twelve Patriarchs, The Testament of Issachar the Fifth Son of Jacob and Leah", "十二族長遺訓：以薩迦", "ch"),
    ("testaments zebulun",   "The Testaments of the Twelve Patriarchs, The Testament of Zebulun the Sixth Son of Jacob and Leah", "十二族長遺訓：西布倫", "ch"),
    ("testaments dan",       "The Testaments of the Twelve Patriarchs, The Testament of Dan the Seventh Son of Jacob and Bilhah", "十二族長遺訓：但", "ch"),
    ("testaments naphtali",  "The Testaments of the Twelve Patriarchs, The Testament of Naphtali the Eighth Son of Jacob and Bilhah", "十二族長遺訓：拿弗他利", "ch"),
    ("testaments gad",       "The Testaments of the Twelve Patriarchs, The Testament of Gad the Ninth Son of Jacob and Zilpah", "十二族長遺訓：迦得", "ch"),
    ("testaments asher",     "The Testaments of the Twelve Patriarchs, The Testament of Asher the Tenth Son of Jacob and Zilpah", "十二族長遺訓：亞設", "ch"),
    ("testaments joseph",    "The Testaments of the Twelve Patriarchs, The Testament of Joseph the Eleventh Son of Jacob and Rachel", "十二族長遺訓：約瑟", "ch"),
    ("testaments benjamin",  "The Testaments of the Twelve Patriarchs, The Testament of Benjamin the Twelfth Son of Jacob and Rachel", "十二族長遺訓：便雅憫", "ch"),
    # Josephus
    ("josephus antiquities", "The Antiquities of the Jews", "約瑟夫斯《猶太古史》", "ch.sec"),
    ("josephus war",         "The War of the Jews",         "約瑟夫斯《猶太戰記》", "ch.sec"),
    ("against apion",        "Against Apion",               "約瑟夫斯《駁阿比安》", "ch.sec"),
    # Philo
    ("philo creation",       "On the Account of the World's Creation", "斐羅《論創世》", "ch"),
    ("philo moses",          "On the Life of Moses, Book I", "斐羅《摩西傳》",       "ch"),
    ("philo moses 2",        "On the Life of Moses, Book II","斐羅《摩西傳》卷二",   "ch"),
    ("philo abraham",        "On Abraham",                  "斐羅《論亞伯拉罕》",   "ch"),
    ("philo joseph",         "On Joseph",                   "斐羅《論約瑟》",       "ch"),
    ("philo decalogue",      "On the Decalogue",            "斐羅《論十誡》",       "ch"),
    ("philo special laws",   "On the Special Laws, Book I",  "斐羅《論特別律法》",   "ch"),
    ("philo special laws 2", "On the Special Laws, Book II", "斐羅《論特別律法》卷二","ch"),
    ("philo special laws 3", "On the Special Laws, Book III","斐羅《論特別律法》卷三","ch"),
    ("philo special laws 4", "On the Special Laws, Book IV", "斐羅《論特別律法》卷四","ch"),
    ("philo virtues",        "On the Virtues",              "斐羅《論美德》",       "ch"),
    ("philo contemplative",  "On the Contemplative Life or Suppliants", "斐羅《論靜觀生活》", "ch"),
    ("philo flaccus",        "Against Flaccus",             "斐羅《駁弗拉庫斯》",   "ch"),
    ("philo dreams",         "On Dreams, Book I",            "斐羅《論夢》",         "ch"),
    ("philo dreams 2",       "On Dreams, Book II",           "斐羅《論夢》卷二",     "ch"),
    ("philo giants",         "On the Giants",               "斐羅《論巨人》",       "ch"),
    ("philo drunkenness",    "On Drunkenness",              "斐羅《論醉》",         "ch"),
    ("philo migration",      "On the Migration of Abraham", "斐羅《論亞伯拉罕遷徙》","ch"),
    ("philo heir",           "Who is the Heir of Divine Things", "斐羅《論神聖繼承》", "ch"),
    ("philo cherubim",       "On the Cherubim",             "斐羅《論基路伯》",     "ch"),
    ("philo confusion",      "On the Confusion of Tongues", "斐羅《論混亂語言》",   "ch"),
    ("philo allegory",       "Allegorical Interpretation of Genesis, Book I", "斐羅《創世記寓意解經》", "ch"),
    ("philo allegory 2",     "Allegorical Interpretation of Genesis, Book II","斐羅《創世記寓意解經》卷二", "ch"),
    ("philo allegory 3",     "Allegorical Interpretation of Genesis, Book III","斐羅《創世記寓意解經》卷三", "ch"),
    ("philo every good man", "Every Good Man is Free",      "斐羅《論善人自由》",   "ch"),
    ("philo husbandry",      "On Husbandry",                "斐羅《論農耕》",       "ch"),
    ("philo rewards",        "On Rewards and Punishments",  "斐羅《論賞罰》",       "ch"),
    ("philo posterity",      "On the Posterity of Cain and his Exile", "斐羅《論該隱後裔》", "ch"),
    ("philo unchangeableness","On the Unchangeableness of God", "斐羅《論上帝不變》", "ch"),
    ("philo worse attacks",  "That the Worse is wont to Attack the Better", "斐羅《論惡攻善》", "ch"),
    ("philo noah planter",   "Concerning Noah's Work as a Planter", "斐羅《論挪亞為農》", "ch"),
    ("philo flight",         "On Flight and Finding",       "斐羅《論逃亡與尋找》", "ch"),
    ("philo change names",   "On the Change of Names",      "斐羅《論更名》",       "ch"),
    ("philo sacrifices",     "On the Birth of Abel and the Sacrifices Offered by him and by his Brother Cain", "斐羅《論亞伯獻祭》", "ch"),
    ("philo preliminary",    "On Mating with the Preliminary Studies", "斐羅《論預備學科》", "ch"),
    ("philo hypothetica",    "Hypothetica",                 "斐羅《假設》",         "ch"),
    ("philo eternity",       "On the Eternity of the World","斐羅《論世界永恆》",   "ch"),
    ("philo providence",     "On Providence",               "斐羅《論天命》",       "ch"),
    ("philo noah curses",    "On the Prayers and Curses Uttered by Noah when he Became Sober", "斐羅《論挪亞醒後禱咒》", "ch"),
    # Other
    ("megillat antiochus",   "Megillat Antiochus",          "安提約古卷",       "ch"),
    # Megillat Ta'anit omitted: complex schema with month-based refs (Nisan, Iyyar, etc.)
]

# Chinese aliases for extra-canonical
_EXTRA_ALIASES = {
    "禧年書": "jubilees",
    "多俾亞傳": "tobit", "友弟德傳": "judith",
    "德訓篇": "ben sira", "智慧篇": "wisdom of solomon",
    "瑪加伯上": "1 maccabees", "瑪加伯下": "2 maccabees",
    "蘇撒拿傳": "susanna", "瑪拿西禱詞": "prayer of manasseh",
    "十二族長遺訓": "testaments of the twelve patriarchs",
    "亞里斯提亞書信": "letter of aristeas",
    "約瑟夫斯古史": "josephus antiquities", "猶太古史": "josephus antiquities",
    "約瑟夫斯戰記": "josephus war", "猶太戰記": "josephus war",
    "駁阿比安": "against apion",
}

# Build lookups
_extra_by_key = {}
_extra_by_sefaria = {}  # Sefaria title → row
for row in EXTRA_CANON:
    _extra_by_key[row[0]] = row
    _extra_by_sefaria[row[1].lower()] = row


def _lookup_extra(name: str):
    """Look up extra-canonical text. Returns (sefaria_title, display_name, ref_style) or None."""
    key = name.lower().strip()
    # Direct match on lookup key
    if key in _extra_by_key:
        _, sefaria, display, style = _extra_by_key[key]
        return sefaria, display, style
    # Direct match on Sefaria title
    if key in _extra_by_sefaria:
        _, sefaria, display, style = _extra_by_sefaria[key]
        return sefaria, display, style
    # Chinese alias
    alias = _EXTRA_ALIASES.get(name.strip())
    if alias and alias in _extra_by_key:
        _, sefaria, display, style = _extra_by_key[alias]
        return sefaria, display, style
    # Partial match on key
    for k, row in _extra_by_key.items():
        if key in k or k in key:
            return row[1], row[2], row[3]
    # Partial match on Sefaria title
    for st, row in _extra_by_sefaria.items():
        if key in st or st in key:
            return row[1], row[2], row[3]
    return None


def fetch(book: str, chapter: int | str, start_verse: int = None, end_verse: int = None) -> dict:
    info = lookup(book)
    extra = None

    if info:
        chinese_name, sefaria_name, osis, _ = info
    else:
        # Try extra-canonical catalog
        extra = _lookup_extra(book)
        if not extra:
            # Passthrough: treat the book name as a direct Sefaria ref
            # This enables access to Mishnah, Talmud, Midrash, etc. without
            # enumerating thousands of texts in the catalog.
            extra = (book, book, "ch")
        sefaria_name, chinese_name, ref_style = extra

    # Build Sefaria ref
    if extra and extra[2] == "ch.sec":
        # Josephus/Philo: Title.Book.Chapter (chapter=book, start_verse=chapter)
        if start_verse and end_verse:
            ref = f"{sefaria_name}.{chapter}.{start_verse}-{end_verse}"
        elif start_verse:
            ref = f"{sefaria_name}.{chapter}.{start_verse}"
        else:
            ref = f"{sefaria_name}.{chapter}"
    else:
        if start_verse and end_verse:
            ref = f"{sefaria_name}.{chapter}.{start_verse}-{end_verse}"
        elif start_verse:
            ref = f"{sefaria_name}.{chapter}.{start_verse}"
        else:
            ref = f"{sefaria_name}.{chapter}"

    # Use v1 API for extra-canonical (more reliable for English), v3 for canon
    if extra:
        url = f"https://www.sefaria.org/api/texts/{urllib.parse.quote(ref)}?lang=en"
    else:
        url = f"https://www.sefaria.org/api/v3/texts/{urllib.parse.quote(ref)}?version=source&version=all"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "torah-first-century-skill/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": f"Passage not found in Sefaria (no NT). Ref: {ref}", "url": url}
        return {"error": f"Sefaria API error: {e.code} {e.reason}", "url": url}
    except urllib.error.URLError as e:
        return {"error": f"Cannot reach Sefaria (network issue). Try fetch_fhl.py instead. Detail: {e.reason}", "url": url}
    except Exception as e:
        return {"error": f"Request failed: {e}", "url": url}

    # Check for API-level errors (e.g., invalid title via passthrough)
    if data.get("error"):
        return {"error": f"Sefaria: {data['error']}", "url": url}

    if extra:
        # v1 API response: data["text"] = English, data["he"] = Hebrew
        english_text = data.get("text")
        hebrew_text = data.get("he")
        # Flatten nested lists (some texts return [[v1, v2], [v3]] structure)
        english_text = _flatten(english_text)
        hebrew_text = _flatten(hebrew_text)
    else:
        # v3 API response: data["versions"] array
        hebrew_versions = data.get("versions", [])
        hebrew_text = None
        for v in hebrew_versions:
            if v.get("language") == "he":
                hebrew_text = v.get("text")
                break
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


def _flatten(text):
    """Flatten nested list from Sefaria API into a flat list of strings."""
    if not text:
        return text
    if isinstance(text, str):
        return text
    if isinstance(text, list):
        flat = []
        for item in text:
            if isinstance(item, list):
                flat.extend(item)
            elif isinstance(item, str):
                flat.append(item)
        return flat if flat else text
    return text


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


def list_extra() -> str:
    """List all extra-canonical texts available on Sefaria."""
    seen = set()
    apoc, josephus, philo, other = [], [], [], []
    for key, sefaria, display, style in EXTRA_CANON:
        if sefaria in seen:
            continue
        seen.add(sefaria)
        entry = f"  • {display}  ({sefaria})"
        if "josephus" in key or "apion" in key:
            josephus.append(entry)
        elif "philo" in key:
            philo.append(entry)
        elif any(x in key for x in ["megillat"]):
            other.append(entry)
        else:
            apoc.append(entry)
    lines = ["═══ Apocrypha / Deuterocanon ═══"] + sorted(apoc)
    lines += ["", "═══ Josephus ═══"] + josephus
    lines += ["", "═══ Philo of Alexandria ═══"] + sorted(philo)
    if other:
        lines += ["", "═══ Other ═══"] + sorted(other)
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list-extra":
        print(list_extra())
        sys.exit(0)

    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    # Handle multi-word book names (e.g., I Chronicles 21 1 → book="I Chronicles")
    # Also handle Talmud daf format (e.g., Berakhot 2a)
    args = sys.argv[1:]
    # Find first arg that looks numeric (integer or daf like "2a")
    chapter_idx = next(
        (i for i, a in enumerate(args) if a[0].isdigit()),
        None,
    )
    if chapter_idx is not None and chapter_idx > 0:
        book = " ".join(args[:chapter_idx])
        nums = args[chapter_idx:]
    else:
        book = args[0]
        nums = args[1:]

    # Chapter: integer for biblical, string for daf (e.g. "2a")
    chapter = int(nums[0]) if nums[0].isdigit() else nums[0]
    start_v = int(nums[1]) if len(nums) > 1 and nums[1].isdigit() else None
    end_v = int(nums[2]) if len(nums) > 2 and nums[2].isdigit() else None

    result = fetch(book, chapter, start_v, end_v)
    print(format_output(result))
