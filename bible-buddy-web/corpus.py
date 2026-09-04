"""Everything this reader asks 信望愛 (FHL) for: a passage, a keyword search, one verse of word
analysis, one Strong's entry.

Two things used to reach FHL side by side — bible-buddy's own fetcher for passages, a local urllib
helper for the other three — and each of the five callers repeated the thread hop, its own
try/except and its own error sentence. None of it could be tested, because there was nowhere to
stand between the caller and the network.

There is now. Every call out goes through SOURCE, and a test swaps that one object for recorded
answers. bible-buddy's fetcher is wrapped, never forked: it owns the version table and the book
names, and it is a seam this repo does not own.
"""
import asyncio
import html as html_mod
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

_SCRIPTS = str(Path(__file__).parent / ".claude/skills/bible-buddy/scripts")
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)  # append, not insert(0): position 0 would let scripts/ shadow a stdlib module
from book_names import lookup  # noqa: E402
from fetch_fhl import BOOK_BID, fetch, split_heading  # noqa: E402  bible-buddy's own fetcher, stdlib only

SE_API = "https://bible.fhl.net/api/se.php"   # keyword search across all 66 books
QP_API = "https://bible.fhl.net/api/qp.php"   # word-by-word analysis, one verse at a time
SD_API = "https://bible.fhl.net/api/sd.php"   # Strong's dictionary


class CorpusError(Exception):
    """FHL did not answer, or answered with something unreadable. The message is written for the
    reader on the page, not for a log."""


class LiveFHL:
    """The real corpus. Passages come from bible-buddy's own fetcher; the other three are plain HTTP."""

    def passage(self, book, chapter, start, end, version) -> dict:
        return fetch(book, chapter, start, end, version)

    def get(self, url: str, params: dict) -> dict:
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params),
                                     headers={"User-Agent": "bible-buddy-web/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))


SOURCE = LiveFHL()   # the seam: tests put a recorded corpus here and the network never comes into it


# ── verse text ────────────────────────────────────────────────────────────────
# FHL inlines translator notes "([1.1]本節或譯…)" / "( [ 1.4] …)" and parallel refs "（#太 3:1-12;可 1:1-8|）" into the verse text
FOOTNOTE = re.compile(r"\s*(?:\(\s*\[\s*\d+\.\d+\s*\]\s*(.*?)\s*\)|（#(.*?)\|?）)")

# A verse whose wording a version folded into an earlier verse (和合本2010 路 1:2-3, 太 19:5) comes back
# from FHL as the single letter "a". It is a marker, not text — never render or quote it.
MERGED_MARK = "a"
MERGED_NOTE = "（本節經文併入前一節，此版本無獨立內容）"


def split_footnotes(text: str) -> tuple[str, list[dict], list[tuple[int, int]]]:
    """→ clean text, footnotes [{pos, text}] at their offsets in the clean text, and the cut spans of the original (for re-anchoring)."""
    clean, fns, cuts, last = "", [], [], 0
    for m in FOOTNOTE.finditer(text):
        clean += text[last:m.start()]
        body = m.group(1) if m.group(1) is not None else "參 " + "; ".join(p.strip() for p in m.group(2).split(";"))
        fns.append({"pos": len(clean), "text": body.strip()})
        cuts.append((m.start(), m.end() - m.start()))
        last = m.end()
    return clean + text[last:], fns, cuts


def normalize(v: dict) -> dict:
    if v["text"].strip() == MERGED_MARK:
        v.update(text="", footnotes=[], cuts=[], merged=True)
    else:
        v["text"], v["footnotes"], v["cuts"] = split_footnotes(v["text"])
    return v


def clean_hit(text: str) -> str:
    """A search hit is rawer than a fetched verse: some versions are indexed in their Strong's edition
    (<WH0430>, {<WH0853>}), and section headings and <br/> come along. Strip all of it, then reuse the
    passage cleaner to drop translator notes and parallel refs."""
    text = html_mod.unescape(re.sub(r"<[^>]+>", "", split_heading(text)[0])).replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", split_footnotes(text)[0]).strip()


def bid(book: str) -> int | None:
    """FHL's numeric book id, or None for a name no version knows."""
    info = lookup(book)
    return BOOK_BID.get(info[2]) if info else None


BID_ZH = {b: (lookup(osis) or (osis,))[0] for osis, b in BOOK_BID.items()}  # se.php answers with a bid and an abbreviation; the reader wants the full name


async def _get(url: str, params: dict, doing: str) -> dict:
    try:
        return await asyncio.to_thread(SOURCE.get, url, params)
    except Exception as e:
        raise CorpusError(f"FHL {doing}失敗：{e}") from e


# ── the four things the reader asks for ───────────────────────────────────────

async def verses(book: str, chapter: int, start: int, end: int, version: str) -> dict:
    """A passage, cleaned and with its reference settled. An FHL-reported problem comes back as
    {"error": …} the way the page expects; only a dead transport raises."""
    try:
        r = await asyncio.to_thread(SOURCE.passage, book, chapter, start, end, version)
    except Exception as e:
        raise CorpusError(f"FHL 經文載入失敗：{e}") from e
    for v in r.get("verses", []):
        normalize(v)
    if r.get("verses"):  # the page asks for end=200 to mean "to the end": that reads "約翰福音 1"; an explicit end is clamped
        last = int(r["verses"][-1]["verse"])
        head = r["reference"].split(":")[0]
        r["reference"] = head if start == 1 and end > last else f"{head}:{start}-{min(end, last)}" if end != start else f"{head}:{start}"
    return r


async def search(q: str, version: str, limit: int) -> dict:
    """Keyword hits across all 66 books. Two calls: the total (count_only) and the first `limit`
    verses, because se.php's record_count is the returned count once a limit is set."""
    base = {"q": q, "VERSION": version, "gb": 0}
    total, data = await asyncio.gather(
        _get(SE_API, {**base, "count_only": 1}, "搜尋"),
        _get(SE_API, {**base, "limit": max(1, min(limit, 200))}, "搜尋"),
    )
    records = []
    for r in data.get("record", []):
        book = BID_ZH.get(r.get("bid"), r.get("chineses", ""))
        records.append({"book": book, "chapter": r.get("chap"), "verse": str(r.get("sec")),
                        "ref": f"{book} {r.get('chap')}:{r.get('sec')}", "text": clean_hit(r.get("bible_text", ""))})
    return {"records": records, "total": total.get("record_count", len(records)), "q": q}


async def interlinear(book: str, chapter: int, verse: int) -> dict:
    """One verse of FHL's word analysis. Record wid=0 carries the whole original verse plus a literal
    Chinese rendering; wid>=1 are the words in reading order. Per verse only — a whole chapter errors out."""
    b = bid(book)
    if not b:
        raise CorpusError(f"未知書卷：{book}")
    d = await _get(QP_API, {"bid": b, "chap": chapter, "sec": verse, "gb": 0}, "原文分析")
    head, words = {"text": "", "literal": ""}, []
    for r in d.get("record", []):
        g = lambda k: (r.get(k) or "").strip()  # noqa: E731  every field can be absent or null
        if r.get("wid") == 0:
            head = {"text": re.sub(r"\s+", " ", g("word")), "literal": re.sub(r"\s+", " ", g("exp"))}
        else:
            words.append({k: g(k) for k in ("word", "sn", "pro", "wform", "orig", "exp", "remark")})
    if not words:
        return {"error": "這一節沒有原文分析資料", **head, "words": []}
    return {"ot": d.get("N") == 1, "words": words, **head}  # N: 0 新約 (Greek, LTR), 1 舊約 (Hebrew, RTL)


async def lexicon(sn: str, ot: bool) -> dict:
    """Strong's entry for one word: transliteration, KJV counts, gloss tree. Plain text, not markdown."""
    d = await _get(SD_API, {"N": 1 if ot else 0, "k": sn, "gb": 0}, "字典")
    r = (d.get("record") or [{}])[0]
    return {"sn": r.get("sn") or sn, "orig": r.get("orig") or "", "text": (r.get("dic_text") or "").strip()}


def original_language_version(book: str) -> str:
    """The 對照 column's `auto`: the original language of the testament the book is in."""
    return "bhs" if (bid(book) or 1) <= 39 else "fhlwh"
