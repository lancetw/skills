#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Fetch Rabbinic literature from Sefaria.org API.

Supports: Mishnah (63 tractates), Talmud Bavli (37 tractates), Tosefta (63 tractates).

Usage:
    uv run scripts/fetch_rabbinic.py mishnah <tractate> <chapter> [halakhah] [end_halakhah]
    uv run scripts/fetch_rabbinic.py talmud <tractate> <daf>
    uv run scripts/fetch_rabbinic.py tosefta <tractate> <chapter> [halakhah] [end_halakhah]
    uv run scripts/fetch_rabbinic.py list [mishnah|talmud|tosefta]

Examples:
    uv run scripts/fetch_rabbinic.py mishnah Berakhot 1 1 3
    uv run scripts/fetch_rabbinic.py mishnah 祝禱篇 1
    uv run scripts/fetch_rabbinic.py talmud Berakhot 2a
    uv run scripts/fetch_rabbinic.py talmud 安息日篇 31a
    uv run scripts/fetch_rabbinic.py tosefta Shabbat 1 1 5
    uv run scripts/fetch_rabbinic.py list
    uv run scripts/fetch_rabbinic.py list talmud
"""

import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.parse
import urllib.request
import urllib.error


# ── Tractate registry ────────────────────────────────────────────────
# (english, sefaria_key, chinese, seder, has_bavli)

TRACTATES = [
    # ── Zeraim 種子篇 ──
    ("Berakhot",       "Berakhot",       "祝禱篇",     "Zeraim",   True),
    ("Peah",           "Peah",           "田角篇",     "Zeraim",   False),
    ("Demai",          "Demai",          "存疑篇",     "Zeraim",   False),
    ("Kilayim",        "Kilayim",        "混種篇",     "Zeraim",   False),
    ("Sheviit",        "Sheviit",        "安息年篇",   "Zeraim",   False),
    ("Terumot",        "Terumot",        "舉祭篇",     "Zeraim",   False),
    ("Maaserot",       "Maaserot",       "什一篇",     "Zeraim",   False),
    ("Maaser Sheni",   "Maaser Sheni",   "第二什一篇", "Zeraim",   False),
    ("Challah",        "Challah",        "麵餅篇",     "Zeraim",   False),
    ("Orlah",          "Orlah",          "未熟果篇",   "Zeraim",   False),
    ("Bikkurim",       "Bikkurim",       "初熟篇",     "Zeraim",   False),
    # ── Moed 節期篇 ──
    ("Shabbat",        "Shabbat",        "安息日篇",   "Moed",     True),
    ("Eruvin",         "Eruvin",         "合域篇",     "Moed",     True),
    ("Pesachim",       "Pesachim",       "逾越節篇",   "Moed",     True),
    ("Shekalim",       "Shekalim",       "舍客勒篇",   "Moed",     True),
    ("Yoma",           "Yoma",           "贖罪日篇",   "Moed",     True),
    ("Sukkah",         "Sukkah",         "住棚節篇",   "Moed",     True),
    ("Beitzah",        "Beitzah",        "節日篇",     "Moed",     True),
    ("Rosh Hashanah",  "Rosh Hashanah",  "新年篇",     "Moed",     True),
    ("Taanit",         "Taanit",         "禁食篇",     "Moed",     True),
    ("Megillah",       "Megillah",       "書卷篇",     "Moed",     True),
    ("Moed Katan",     "Moed Katan",     "小節期篇",   "Moed",     True),
    ("Chagigah",       "Chagigah",       "節期獻祭篇", "Moed",     True),
    # ── Nashim 婦女篇 ──
    ("Yevamot",        "Yevamot",        "叔嫂婚篇",   "Nashim",   True),
    ("Ketubot",        "Ketubot",        "婚約篇",     "Nashim",   True),
    ("Nedarim",        "Nedarim",        "許願篇",     "Nashim",   True),
    ("Nazir",          "Nazir",          "拿細耳篇",   "Nashim",   True),
    ("Sotah",          "Sotah",          "疑妻篇",     "Nashim",   True),
    ("Gittin",         "Gittin",         "休書篇",     "Nashim",   True),
    ("Kiddushin",      "Kiddushin",      "婚姻篇",     "Nashim",   True),
    # ── Nezikin 損害篇 ──
    ("Bava Kamma",     "Bava Kamma",     "首門篇",     "Nezikin",  True),
    ("Bava Metzia",    "Bava Metzia",    "中門篇",     "Nezikin",  True),
    ("Bava Batra",     "Bava Batra",     "末門篇",     "Nezikin",  True),
    ("Sanhedrin",      "Sanhedrin",      "公議會篇",   "Nezikin",  True),
    ("Makkot",         "Makkot",         "鞭刑篇",     "Nezikin",  True),
    ("Shevuot",        "Shevuot",        "誓言篇",     "Nezikin",  True),
    ("Eduyot",         "Eduyot",         "見證篇",     "Nezikin",  False),
    ("Avodah Zarah",   "Avodah Zarah",   "偶像崇拜篇", "Nezikin",  True),
    ("Avot",           "Avot",           "先賢篇",     "Nezikin",  False),
    ("Horayot",        "Horayot",        "裁決篇",     "Nezikin",  True),
    # ── Kodashim 聖物篇 ──
    ("Zevachim",       "Zevachim",       "祭牲篇",     "Kodashim", True),
    ("Menachot",       "Menachot",       "素祭篇",     "Kodashim", True),
    ("Chullin",        "Chullin",        "俗物篇",     "Kodashim", True),
    ("Bekhorot",       "Bekhorot",       "頭生篇",     "Kodashim", True),
    ("Arakhin",        "Arakhin",        "估價篇",     "Kodashim", True),
    ("Temurah",        "Temurah",        "替換篇",     "Kodashim", True),
    ("Keritot",        "Keritot",        "切斷篇",     "Kodashim", True),
    ("Meilah",         "Meilah",         "褻瀆篇",     "Kodashim", True),
    ("Tamid",          "Tamid",          "常獻篇",     "Kodashim", True),
    ("Middot",         "Middot",         "度量篇",     "Kodashim", False),
    ("Kinnim",         "Kinnim",         "鳥巢篇",     "Kodashim", False),
    # ── Tohorot 潔淨篇 ──
    ("Kelim",          "Kelim",          "器皿篇",     "Tohorot",  False),
    ("Ohalot",         "Ohalot",         "帳幕篇",     "Tohorot",  False),
    ("Negaim",         "Negaim",         "病症篇",     "Tohorot",  False),
    ("Parah",          "Parah",          "紅母牛篇",   "Tohorot",  False),
    ("Tohorot",        "Tohorot",        "潔淨物篇",   "Tohorot",  False),
    ("Mikvaot",        "Mikvaot",        "浸禮池篇",   "Tohorot",  False),
    ("Niddah",         "Niddah",         "經期篇",     "Tohorot",  True),
    ("Makhshirin",     "Makhshirin",     "預備篇",     "Tohorot",  False),
    ("Zavim",          "Zavim",          "漏症篇",     "Tohorot",  False),
    ("Tevul Yom",      "Tevul Yom",      "當日浸者篇", "Tohorot",  False),
    ("Yadayim",        "Yadayim",        "洗手篇",     "Tohorot",  False),
    ("Uktzin",         "Uktzin",         "果柄篇",     "Tohorot",  False),
]

SEDER_NAMES = {
    "Zeraim":   "種子篇",
    "Moed":     "節期篇",
    "Nashim":   "婦女篇",
    "Nezikin":  "損害篇",
    "Kodashim": "聖物篇",
    "Tohorot":  "潔淨篇",
}

# Build lookup: lowercase english / chinese → (english, sefaria_key, chinese, seder, has_bavli)
_LOOKUP: dict[str, tuple] = {}
for row in TRACTATES:
    _LOOKUP[row[0].lower()] = row
    _LOOKUP[row[2]] = row
    # Alias without spaces
    _LOOKUP[row[0].lower().replace(" ", "")] = row

# Extra aliases
_EXTRA_ALIASES = {
    "pirkei avot": "avot", "pirke avot": "avot", "先賢語錄": "avot",
    "baba kama": "bava kamma", "baba metzia": "bava metzia", "baba batra": "bava batra",
    "shabbos": "shabbat", "berachos": "berakhot", "berachot": "berakhot",
    "yevamos": "yevamot", "kesubos": "ketubot", "gitin": "gittin",
    "kidushin": "kiddushin", "arachin": "arakhin", "chulin": "chullin",
    "megilah": "megillah", "taanis": "taanit", "makos": "makkot",
}
for alias, target in _EXTRA_ALIASES.items():
    if target in _LOOKUP:
        _LOOKUP[alias] = _LOOKUP[target]


def _resolve_tractate(name: str) -> tuple | None:
    key = name.strip()
    if key in _LOOKUP:
        return _LOOKUP[key]
    low = key.lower()
    if low in _LOOKUP:
        return _LOOKUP[low]
    # Partial match
    for k, v in _LOOKUP.items():
        if low in k.lower() or k.lower() in low:
            return v
    return None


# ── API helpers ──────────────────────────────────────────────────────


def _fetch_sefaria(ref: str) -> dict:
    url = f"https://www.sefaria.org/api/texts/{urllib.parse.quote(ref)}?lang=en"
    req = urllib.request.Request(url, headers={"User-Agent": "bible-buddy/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"Sefaria {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def _flatten(text):
    if not text:
        return []
    if isinstance(text, str):
        return [text]
    result = []
    for item in text:
        if isinstance(item, list):
            result.extend(_flatten(item))
        elif isinstance(item, str):
            result.append(item)
    return result


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


# ── Fetch functions ──────────────────────────────────────────────────


def fetch_mishnah(tractate: str, chapter: int,
                  start: int = None, end: int = None) -> dict:
    info = _resolve_tractate(tractate)
    if not info:
        return {"error": f"Unknown tractate: {tractate}"}
    en_name, sefaria_key, zh_name, seder, _ = info

    if start and end:
        ref = f"Mishnah_{sefaria_key}.{chapter}.{start}-{end}"
    elif start:
        ref = f"Mishnah_{sefaria_key}.{chapter}.{start}"
    else:
        ref = f"Mishnah_{sefaria_key}.{chapter}"

    data = _fetch_sefaria(ref.replace(" ", "_"))
    if data.get("error"):
        return {"error": data["error"]}

    hebrew = _flatten(data.get("he"))
    english = _flatten(data.get("text"))

    ref_str = f"Mishnah {en_name} ({zh_name}) {chapter}"
    if start and end:
        ref_str += f":{start}-{end}"
    elif start:
        ref_str += f":{start}"

    return {
        "source": "Sefaria.org — Mishnah",
        "reference": ref_str,
        "seder": f"{seder} ({SEDER_NAMES[seder]})",
        "hebrew": [_strip_html(h) for h in hebrew] if hebrew else [],
        "english": [_strip_html(e) for e in english] if english else [],
    }


def fetch_talmud(tractate: str, daf: str) -> dict:
    info = _resolve_tractate(tractate)
    if not info:
        return {"error": f"Unknown tractate: {tractate}"}
    en_name, sefaria_key, zh_name, seder, has_bavli = info
    if not has_bavli:
        return {"error": f"{en_name} ({zh_name}) has no Bavli Gemara"}

    # Validate daf format: number + a/b
    if not re.match(r"^\d+[ab]$", daf):
        return {"error": f"Invalid daf format: {daf}. Use e.g. 2a, 31b"}

    ref = f"{sefaria_key}.{daf}".replace(" ", "_")
    data = _fetch_sefaria(ref)
    if data.get("error"):
        return {"error": data["error"]}

    hebrew = _flatten(data.get("he"))
    english = _flatten(data.get("text"))

    return {
        "source": "Sefaria.org — Talmud Bavli",
        "reference": f"{en_name} ({zh_name}) {daf}",
        "seder": f"{seder} ({SEDER_NAMES[seder]})",
        "hebrew": [_strip_html(h) for h in hebrew] if hebrew else [],
        "english": [_strip_html(e) for e in english] if english else [],
    }


def fetch_tosefta(tractate: str, chapter: int,
                  start: int = None, end: int = None) -> dict:
    info = _resolve_tractate(tractate)
    if not info:
        return {"error": f"Unknown tractate: {tractate}"}
    en_name, sefaria_key, zh_name, seder, _ = info

    if start and end:
        ref = f"Tosefta_{sefaria_key}.{chapter}.{start}-{end}"
    elif start:
        ref = f"Tosefta_{sefaria_key}.{chapter}.{start}"
    else:
        ref = f"Tosefta_{sefaria_key}.{chapter}"

    data = _fetch_sefaria(ref.replace(" ", "_"))
    if data.get("error"):
        return {"error": data["error"]}

    hebrew = _flatten(data.get("he"))
    english = _flatten(data.get("text"))

    ref_str = f"Tosefta {en_name} ({zh_name}) {chapter}"
    if start and end:
        ref_str += f":{start}-{end}"
    elif start:
        ref_str += f":{start}"

    return {
        "source": "Sefaria.org — Tosefta",
        "reference": ref_str,
        "seder": f"{seder} ({SEDER_NAMES[seder]})",
        "hebrew": [_strip_html(h) for h in hebrew] if hebrew else [],
        "english": [_strip_html(e) for e in english] if english else [],
    }


# ── Output formatting ────────────────────────────────────────────────


def format_output(result: dict) -> str:
    if result.get("error"):
        return f"Error: {result['error']}"

    lines = [
        f"{result['reference']}",
        f"Source: {result['source']}",
        f"Seder: {result['seder']}",
        "",
    ]

    he = result.get("hebrew", [])
    en = result.get("english", [])

    if he:
        for i, h in enumerate(he, 1):
            lines.append(f"  [{i}] {h}")
    else:
        lines.append("  (no Hebrew text)")

    if en:
        lines.append("")
        lines.append("English:")
        for i, e in enumerate(en, 1):
            # Truncate long Talmud commentary for readability
            if len(e) > 300:
                e = e[:300] + "..."
            lines.append(f"  [{i}] {e}")

    return "\n".join(lines)


# ── List command ─────────────────────────────────────────────────────


def cmd_list(filter_type: str = None):
    print("=== Rabbinic Literature ===\n")

    for seder, zh_seder in SEDER_NAMES.items():
        tractates = [t for t in TRACTATES if t[3] == seder]
        print(f"── {seder} ({zh_seder}) ──")
        for en, _, zh, _, has_bavli in tractates:
            markers = []
            markers.append("M")  # All have Mishnah
            if has_bavli:
                markers.append("B")
            markers.append("T")  # All have Tosefta
            flag = "/".join(markers)
            if filter_type == "talmud" and not has_bavli:
                continue
            print(f"  {en:<20} {zh:<10} [{flag}]")
        print()

    print("Legend: M=Mishnah, B=Bavli, T=Tosefta")
    print()
    print("Usage:")
    print("  fetch_rabbinic.py mishnah <tractate> <chapter> [start] [end]")
    print("  fetch_rabbinic.py talmud  <tractate> <daf>  (e.g. 2a, 31b)")
    print("  fetch_rabbinic.py tosefta <tractate> <chapter> [start] [end]")


# ── CLI ──────────────────────────────────────────────────────────────


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0)

    if args[0] == "list":
        cmd_list(args[1] if len(args) > 1 else None)
        return

    corpus = args[0].lower()
    if corpus not in ("mishnah", "talmud", "tosefta"):
        print(f"Error: unknown corpus '{corpus}'. Use: mishnah, talmud, tosefta",
              file=sys.stderr)
        sys.exit(1)

    if len(args) < 3:
        print(f"Usage: fetch_rabbinic.py {corpus} <tractate> <chapter|daf> [start] [end]",
              file=sys.stderr)
        sys.exit(1)

    # Handle multi-word tractate names
    remaining = args[1:]
    if corpus == "talmud":
        # Last arg is daf (e.g. "2a")
        daf = remaining[-1]
        tractate = " ".join(remaining[:-1])
        result = fetch_talmud(tractate, daf)
    else:
        # Find first numeric arg = chapter
        ch_idx = next((i for i, a in enumerate(remaining) if a.isdigit()), None)
        if ch_idx is None:
            print(f"Error: missing chapter number", file=sys.stderr)
            sys.exit(1)
        tractate = " ".join(remaining[:ch_idx])
        chapter = int(remaining[ch_idx])
        start = int(remaining[ch_idx + 1]) if len(remaining) > ch_idx + 1 else None
        end = int(remaining[ch_idx + 2]) if len(remaining) > ch_idx + 2 else None

        if corpus == "mishnah":
            result = fetch_mishnah(tractate, chapter, start, end)
        else:
            result = fetch_tosefta(tractate, chapter, start, end)

    print(format_output(result))


if __name__ == "__main__":
    main()
