"""Book name mapping: Chinese ↔ English ↔ OSIS codes for Bible references."""

# (Chinese name, English name for Sefaria, OSIS code, Bible Gateway English)
BOOKS = [
    # Torah
    ("創世記", "Genesis", "Gen", "Genesis"),
    ("出埃及記", "Exodus", "Exod", "Exodus"),
    ("利未記", "Leviticus", "Lev", "Leviticus"),
    ("民數記", "Numbers", "Num", "Numbers"),
    ("申命記", "Deuteronomy", "Deut", "Deuteronomy"),
    # Nevi'im - Former Prophets
    ("約書亞記", "Joshua", "Josh", "Joshua"),
    ("士師記", "Judges", "Judg", "Judges"),
    ("撒母耳記上", "I Samuel", "1Sam", "1+Samuel"),
    ("撒母耳記下", "II Samuel", "2Sam", "2+Samuel"),
    ("列王紀上", "I Kings", "1Kgs", "1+Kings"),
    ("列王紀下", "II Kings", "2Kgs", "2+Kings"),
    # Nevi'im - Latter Prophets
    ("以賽亞書", "Isaiah", "Isa", "Isaiah"),
    ("耶利米書", "Jeremiah", "Jer", "Jeremiah"),
    ("以西結書", "Ezekiel", "Ezek", "Ezekiel"),
    ("何西阿書", "Hosea", "Hos", "Hosea"),
    ("約珥書", "Joel", "Joel", "Joel"),
    ("阿摩司書", "Amos", "Amos", "Amos"),
    ("俄巴底亞書", "Obadiah", "Obad", "Obadiah"),
    ("約拿書", "Jonah", "Jonah", "Jonah"),
    ("彌迦書", "Micah", "Mic", "Micah"),
    ("那鴻書", "Nahum", "Nah", "Nahum"),
    ("哈巴谷書", "Habakkuk", "Hab", "Habakkuk"),
    ("西番雅書", "Zephaniah", "Zeph", "Zephaniah"),
    ("哈該書", "Haggai", "Hag", "Haggai"),
    ("撒迦利亞書", "Zechariah", "Zech", "Zechariah"),
    ("瑪拉基書", "Malachi", "Mal", "Malachi"),
    # Ketuvim
    ("詩篇", "Psalms", "Ps", "Psalms"),
    ("箴言", "Proverbs", "Prov", "Proverbs"),
    ("約伯記", "Job", "Job", "Job"),
    ("雅歌", "Song of Songs", "Song", "Song+of+Solomon"),
    ("路得記", "Ruth", "Ruth", "Ruth"),
    ("耶利米哀歌", "Lamentations", "Lam", "Lamentations"),
    ("傳道書", "Ecclesiastes", "Eccl", "Ecclesiastes"),
    ("以斯帖記", "Esther", "Esth", "Esther"),
    ("但以理書", "Daniel", "Dan", "Daniel"),
    ("以斯拉記", "Ezra", "Ezra", "Ezra"),
    ("尼希米記", "Nehemiah", "Neh", "Nehemiah"),
    ("歷代志上", "I Chronicles", "1Chr", "1+Chronicles"),
    ("歷代志下", "II Chronicles", "2Chr", "2+Chronicles"),
    # New Testament
    ("馬太福音", "Matthew", "Matt", "Matthew"),
    ("馬可福音", "Mark", "Mark", "Mark"),
    ("路加福音", "Luke", "Luke", "Luke"),
    ("約翰福音", "John", "John", "John"),
    ("使徒行傳", "Acts", "Acts", "Acts"),
    ("羅馬書", "Romans", "Rom", "Romans"),
    ("哥林多前書", "I Corinthians", "1Cor", "1+Corinthians"),
    ("哥林多後書", "II Corinthians", "2Cor", "2+Corinthians"),
    ("加拉太書", "Galatians", "Gal", "Galatians"),
    ("以弗所書", "Ephesians", "Eph", "Ephesians"),
    ("腓立比書", "Philippians", "Phil", "Philippians"),
    ("歌羅西書", "Colossians", "Col", "Colossians"),
    ("帖撒羅尼迦前書", "I Thessalonians", "1Thess", "1+Thessalonians"),
    ("帖撒羅尼迦後書", "II Thessalonians", "2Thess", "2+Thessalonians"),
    ("提摩太前書", "I Timothy", "1Tim", "1+Timothy"),
    ("提摩太後書", "II Timothy", "2Tim", "2+Timothy"),
    ("提多書", "Titus", "Titus", "Titus"),
    ("腓利門書", "Philemon", "Phlm", "Philemon"),
    ("希伯來書", "Hebrews", "Heb", "Hebrews"),
    ("雅各書", "James", "Jas", "James"),
    ("彼得前書", "I Peter", "1Pet", "1+Peter"),
    ("彼得後書", "II Peter", "2Pet", "2+Peter"),
    ("約翰一書", "I John", "1John", "1+John"),
    ("約翰二書", "II John", "2John", "2+John"),
    ("約翰三書", "III John", "3John", "3+John"),
    ("猶大書", "Jude", "Jude", "Jude"),
    ("啟示錄", "Revelation", "Rev", "Revelation"),
]

# Build lookup dictionaries
_by_chinese = {b[0]: b for b in BOOKS}
_by_english = {b[1].lower(): b for b in BOOKS}
_by_osis = {b[2].lower(): b for b in BOOKS}


def lookup(name: str):
    """Look up a book by Chinese name, English name, or OSIS code.
    Returns (chinese, sefaria_name, osis, biblegateway_name) or None."""
    name = name.strip()
    if name in _by_chinese:
        return _by_chinese[name]
    if name.lower() in _by_english:
        return _by_english[name.lower()]
    if name.lower() in _by_osis:
        return _by_osis[name.lower()]
    # Fuzzy: try partial match on Chinese
    for zh, *rest in BOOKS:
        if name in zh or zh in name:
            return (zh, *rest)
    return None
