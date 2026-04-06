"""Fetch Dead Sea Scrolls text from ETCBC/dss via Text-Fabric.

Covers: All biblical and non-biblical scrolls (~1001 scrolls, ~500K words).
Source: Martin Abegg's transcriptions (CC-BY-NC 4.0) via ETCBC/dss.

Usage:
    python fetch_dss.py <scroll> [fragment] [start_line] [end_line]
    python fetch_dss.py biblical <book> [chapter] [start_verse] [end_verse]
    python fetch_dss.py list
    python fetch_dss.py list-biblical
    python fetch_dss.py info <scroll>

Examples:
    python fetch_dss.py list
    python fetch_dss.py list-biblical
    python fetch_dss.py 1QS
    python fetch_dss.py 1QS 1
    python fetch_dss.py 1QS 1 1 5
    python fetch_dss.py 社群規章
    python fetch_dss.py biblical Isaiah
    python fetch_dss.py biblical Isaiah 1
    python fetch_dss.py biblical Isaiah 1 1 5
    python fetch_dss.py biblical 以賽亞書
    python fetch_dss.py info 1QS
"""

import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ── Chinese aliases for major scrolls ────────────────────────────────
SCROLL_ALIASES = {
    # Major sectarian texts
    "社群規章": "1QS",
    "附則": "1QSa",
    "祝福文": "1QSb",
    "戰爭卷軸": "1QM",
    "感恩詩篇": "1QHa",
    "哈巴谷書注釋": "1QpHab",
    "大馬色文件": "CD",
    "聖殿卷軸": "11Q19",
    "銅卷軸": "3Q15",
    "那鴻書注釋": "4Q169",
    "光暗之子": "1QM",
    "大以賽亞卷軸": "1Qisaa",
    "小以賽亞卷軸": "1Q8",
    # Common English aliases
    "community rule": "1QS",
    "war scroll": "1QM",
    "thanksgiving hymns": "1QHa",
    "temple scroll": "11Q19",
    "copper scroll": "3Q15",
    "damascus document": "CD",
    "habakkuk pesher": "1QpHab",
    "great isaiah scroll": "1Qisaa",
}

# Chinese aliases for biblical books (DSS use abbreviated names)
BOOK_ALIASES = {
    "創世記": "Gen", "出埃及記": "Ex", "利未記": "Lev",
    "民數記": "Num", "申命記": "Deut", "約書亞記": "Josh",
    "士師記": "Judg", "路得記": "Ruth",
    "撒母耳記上": "1Sam", "撒母耳記下": "2Sam",
    "列王紀上": "1Kgs", "列王紀下": "2Kgs",
    "以賽亞書": "Is", "耶利米書": "Jer", "以西結書": "Ezek",
    "但以理書": "Dan", "何西阿書": "Hos", "約珥書": "Joel",
    "阿摩司書": "Amos", "俄巴底亞書": "Obad", "約拿書": "Jonah",
    "彌迦書": "Mic", "那鴻書": "Nah", "哈巴谷書": "Hab",
    "西番雅書": "Zeph", "哈該書": "Hag", "撒迦利亞書": "Zech",
    "瑪拉基書": "Mal",
    "詩篇": "Ps", "箴言": "Prov", "約伯記": "Job",
    "雅歌": "Song", "傳道書": "Qoh", "哀歌": "Lam",
    "以斯帖記": "Esth", "以斯拉記": "Ezra", "尼希米記": "Neh",
    "歷代志上": "1Chr", "歷代志下": "2Chr",
    # English full names → DSS abbreviations
    "genesis": "Gen", "exodus": "Ex", "leviticus": "Lev",
    "numbers": "Num", "deuteronomy": "Deut", "joshua": "Josh",
    "judges": "Judg", "ruth": "Ruth",
    "1 samuel": "1Sam", "2 samuel": "2Sam",
    "1 kings": "1Kgs", "2 kings": "2Kgs",
    "isaiah": "Is", "jeremiah": "Jer", "ezekiel": "Ezek",
    "daniel": "Dan", "hosea": "Hos", "joel": "Joel",
    "amos": "Amos", "obadiah": "Obad", "jonah": "Jonah",
    "micah": "Mic", "nahum": "Nah", "habakkuk": "Hab",
    "zephaniah": "Zeph", "haggai": "Hag", "zechariah": "Zech",
    "malachi": "Mal",
    "psalms": "Ps", "proverbs": "Prov", "job": "Job",
    "song of songs": "Song", "ecclesiastes": "Eccl", "lamentations": "Lam",
    "esther": "Esth", "ezra": "Ezra", "nehemiah": "Neh",
    "1 chronicles": "1Chr", "2 chronicles": "2Chr",
}


def _load_dss():
    """Load ETCBC/dss dataset. Downloads on first run (~50MB)."""
    from tf.app import use

    return use("ETCBC/dss", silent="deep")


def _resolve_scroll(name: str) -> str:
    """Resolve Chinese/English alias to scroll ID."""
    key = name.strip()
    if key in SCROLL_ALIASES:
        return SCROLL_ALIASES[key]
    low = key.lower()
    if low in SCROLL_ALIASES:
        return SCROLL_ALIASES[low]
    return key


def _resolve_book(name: str) -> str:
    """Resolve Chinese/English book name to DSS abbreviation."""
    key = name.strip()
    if key in BOOK_ALIASES:
        return BOOK_ALIASES[key]
    low = key.lower()
    if low in BOOK_ALIASES:
        return BOOK_ALIASES[low]
    # Try case-insensitive match on values (abbreviations like "Is", "Gen")
    for v in BOOK_ALIASES.values():
        if low == v.lower():
            return v
    return key


def cmd_list(A):
    """List all scrolls."""
    F = A.api.F
    L = A.api.L
    scrolls = sorted(F.otype.s('scroll'), key=lambda s: F.scroll.v(s))

    biblical = []
    nonbiblical = []

    for s in scrolls:
        name = F.scroll.v(s)
        frags = L.d(s, otype='fragment')
        words = L.d(s, otype='word')
        word_count = len(words)
        book = F.book.v(words[0]) if words else None

        entry = f"  {name:<20} {len(frags):>4} fragments  {word_count:>6} words"
        if book and book != 'NA':
            biblical.append((book, name, entry))
        else:
            nonbiblical.append(entry)

    print(f"=== Dead Sea Scrolls Corpus ===")
    print(f"Total: {len(biblical) + len(nonbiblical)} scrolls\n")

    print(f"── Biblical ({len(biblical)}) ──")
    for _, _, entry in sorted(biblical):
        print(entry)

    print(f"\n── Non-Biblical ({len(nonbiblical)}) ──")
    for entry in nonbiblical:
        print(entry)


def cmd_list_biblical(A):
    """List biblical scrolls grouped by book."""
    F = A.api.F
    L = A.api.L

    books = {}
    for s in F.otype.s('scroll'):
        words = L.d(s, otype='word')
        if not words:
            continue
        book = F.book.v(words[0])
        if not book or book == 'NA':
            continue
        name = F.scroll.v(s)
        books.setdefault(book, []).append((name, len(words)))

    print("=== DSS Biblical Manuscripts by Book ===\n")
    for book in sorted(books):
        items = sorted(books[book], key=lambda x: -x[1])
        witnesses = ', '.join(f"{n}({w}w)" for n, w in items)
        print(f"  {book:<8} [{len(items)} witnesses] {witnesses}")


def cmd_info(A, scroll_id: str):
    """Show scroll metadata."""
    F = A.api.F
    L = A.api.L

    scroll_id = _resolve_scroll(scroll_id)

    for s in F.otype.s('scroll'):
        if F.scroll.v(s) == scroll_id:
            frags = L.d(s, otype='fragment')
            words = L.d(s, otype='word')
            lines = L.d(s, otype='line')
            book = F.book.v(words[0]) if words else None

            print(f"=== {scroll_id} ===")
            print(f"Fragments: {len(frags)}")
            print(f"Lines: {len(lines)}")
            print(f"Words: {len(words)}")
            if book and book != 'NA':
                # Get chapter range
                chapters = set()
                for w in words:
                    ch = F.chapter.v(w)
                    if ch:
                        chapters.add(int(ch))
                if chapters:
                    print(f"Biblical: {book} (chapters {min(chapters)}-{max(chapters)})")
            else:
                print(f"Type: Non-Biblical")

            print(f"\nFragments:")
            for frag in frags:
                fname = F.fragment.v(frag)
                flines = L.d(frag, otype='line')
                fwords = L.d(frag, otype='word')
                print(f"  Fragment {fname}: {len(flines)} lines, {len(fwords)} words")
            return

    print(f"Error: scroll '{scroll_id}' not found.", file=sys.stderr)
    sys.exit(1)


def cmd_fetch_scroll(A, scroll_id: str, frag_filter=None, start_line=None, end_line=None):
    """Fetch scroll text by scroll/fragment/line."""
    F = A.api.F
    L = A.api.L

    scroll_id = _resolve_scroll(scroll_id)

    for s in F.otype.s('scroll'):
        if F.scroll.v(s) == scroll_id:
            frags = L.d(s, otype='fragment')
            words_total = L.d(s, otype='word')
            book = F.book.v(words_total[0]) if words_total else None
            is_biblical = book and book != 'NA'

            print(f"=== {scroll_id} ===")
            if is_biblical:
                print(f"Biblical: {book}")
            print()

            for frag in frags:
                fname = F.fragment.v(frag)
                if frag_filter is not None and str(fname) != str(frag_filter):
                    continue

                line_nodes = L.d(frag, otype='line')

                print(f"── Fragment {fname} ──")
                for ln in line_nodes:
                    line_label = F.line.v(ln)

                    # Line filter
                    if start_line is not None:
                        try:
                            ln_num = int(line_label)
                            if ln_num < int(start_line):
                                continue
                            if end_line is not None and ln_num > int(end_line):
                                continue
                        except ValueError:
                            pass

                    word_nodes = L.d(ln, otype='word')
                    text = ' '.join(F.full.v(w) for w in word_nodes)

                    if is_biblical:
                        # Add chapter:verse reference
                        ch = F.chapter.v(word_nodes[0]) if word_nodes else None
                        vs = F.verse.v(word_nodes[0]) if word_nodes else None
                        ref = f"{book} {ch}:{vs}" if ch and vs else ""
                        print(f"  [{ref:<12}] L{line_label:<4} {text}")
                    else:
                        print(f"  L{line_label:<4} {text}")
                print()
            return

    print(f"Error: scroll '{scroll_id}' not found.", file=sys.stderr)
    _suggest_scroll(A, scroll_id)
    sys.exit(1)


def cmd_fetch_biblical(A, book_name: str, chapter=None, start_verse=None, end_verse=None):
    """Fetch all DSS witnesses for a biblical book, optionally filtered by chapter/verse."""
    F = A.api.F
    L = A.api.L

    book_abbr = _resolve_book(book_name)

    # Find all scrolls containing this book
    matches = []
    for s in F.otype.s('scroll'):
        words = L.d(s, otype='word')
        if not words:
            continue
        bk = F.book.v(words[0])
        if bk and bk.lower() == book_abbr.lower():
            matches.append(s)

    if not matches:
        print(f"Error: no DSS manuscripts found for '{book_name}' (resolved: {book_abbr})", file=sys.stderr)
        sys.exit(1)

    print(f"=== DSS witnesses for {book_abbr} ({len(matches)} manuscripts) ===\n")

    for s in matches:
        scroll_name = F.scroll.v(s)
        frags = L.d(s, otype='fragment')

        scroll_lines = []
        for frag in frags:
            fname = F.fragment.v(frag)
            line_nodes = L.d(frag, otype='line')

            frag_lines = []
            for ln in line_nodes:
                word_nodes = L.d(ln, otype='word')
                if not word_nodes:
                    continue

                ch = F.chapter.v(word_nodes[0])
                vs = F.verse.v(word_nodes[0])

                # Chapter filter
                if chapter is not None and ch is not None:
                    try:
                        if int(ch) != int(chapter):
                            continue
                    except ValueError:
                        continue

                # Verse filter
                if start_verse is not None and vs is not None:
                    try:
                        vs_num = int(vs)
                        if vs_num < int(start_verse):
                            continue
                        if end_verse is not None and vs_num > int(end_verse):
                            continue
                    except ValueError:
                        pass

                text = ' '.join(F.full.v(w) for w in word_nodes)
                line_label = F.line.v(ln)
                ref = f"{ch}:{vs}" if ch and vs else "?"
                frag_lines.append(f"  [{ref:<8}] F{fname} L{line_label:<4} {text}")

            if not frag_lines and chapter is None:
                # Show fragment preview
                for ln in line_nodes[:3]:
                    word_nodes = L.d(ln, otype='word')
                    text = ' '.join(F.full.v(w) for w in word_nodes)
                    line_label = F.line.v(ln)
                    frag_lines.append(f"  F{fname} L{line_label:<4} {text}")
                if len(line_nodes) > 3:
                    frag_lines.append(f"  ... ({len(line_nodes)} lines total)")

            scroll_lines.extend(frag_lines)

        if scroll_lines:
            print(f"── {scroll_name} ──")
            for line in scroll_lines:
                print(line)
            print()


def _suggest_scroll(A, query: str):
    """Suggest similar scroll names."""
    F = A.api.F
    q = query.lower()
    suggestions = []
    for s in F.otype.s('scroll'):
        name = F.scroll.v(s)
        if q in name.lower() or name.lower() in q:
            suggestions.append(name)
    if suggestions:
        print(f"Did you mean: {', '.join(suggestions[:10])}?", file=sys.stderr)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0]

    if cmd in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0)

    A = _load_dss()

    if cmd == "list":
        cmd_list(A)
    elif cmd == "list-biblical":
        cmd_list_biblical(A)
    elif cmd == "info":
        if len(args) < 2:
            print("Usage: fetch_dss.py info <scroll>", file=sys.stderr)
            sys.exit(1)
        cmd_info(A, args[1])
    elif cmd == "biblical":
        if len(args) < 2:
            print("Usage: fetch_dss.py biblical <book> [chapter] [start_verse] [end_verse]", file=sys.stderr)
            sys.exit(1)
        book = args[1]
        chapter = args[2] if len(args) > 2 else None
        start_v = args[3] if len(args) > 3 else None
        end_v = args[4] if len(args) > 4 else None
        cmd_fetch_biblical(A, book, chapter, start_v, end_v)
    else:
        # Scroll query
        scroll = args[0]
        frag = args[1] if len(args) > 1 else None
        start_l = args[2] if len(args) > 2 else None
        end_l = args[3] if len(args) > 3 else None
        cmd_fetch_scroll(A, scroll, frag, start_l, end_l)


if __name__ == "__main__":
    main()
