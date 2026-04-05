"""Tests for fetch_biblegateway.py — specifically the chapternum verse 1 bug."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from fetch_biblegateway import extract_verses


# Minimal HTML reproducing BibleGateway's structure for Micah 6:1-3
# Verse 1 uses <span class="chapternum">, verses 2+ use <sup class="versenum">
SAMPLE_HTML_MULTI_VERSE = """
<div class="passage-text">
<div class="version-RCU17TS result-text-style-normal text-html">
<h3><span class="passage-display-bcv">彌迦書 6:1-3</span></h3>
<div class="poetry top-1"><p class="line">
<span class="text Mic-6-1"><span class="chapternum">6\xa0</span>當聽耶和華說的話：</span><br />
<span class="text Mic-6-1">起來，向山嶺爭辯，</span><br />
<span class="text Mic-6-1">使岡陵聽見你的聲音。</span></p></div>
<div class="poetry top-1"><p class="line">
<span class="text Mic-6-2"><sup class="versenum">2\xa0</sup>山嶺啊，要聽耶和華的指控！</span><br />
<span class="text Mic-6-2">大地永久的根基啊，要聽！</span></p></div>
<div class="poetry top-1"><p class="line">
<span class="text Mic-6-3"><sup class="versenum">3\xa0</sup>「我的百姓啊，我向你做了甚麼呢？</span><br />
<span class="text Mic-6-3">我在甚麼事上使你厭煩？你回答我吧！」</span></p></div>
</div></div></div>
"""

# Single verse: only chapternum, no versenum at all
SAMPLE_HTML_SINGLE_VERSE = """
<div class="passage-text">
<div class="version-RCU17TS result-text-style-normal text-html">
<h3><span class="passage-display-bcv">創世記 1:1</span></h3>
<p><span class="text Gen-1-1"><span class="chapternum">1\xa0</span>起初，　神創造天地。</span></p>
</div></div></div>
"""

# No chapternum — mid-chapter request (e.g., Micah 6:3-5)
SAMPLE_HTML_NO_CHAPTERNUM = """
<div class="passage-text">
<div class="version-RCU17TS result-text-style-normal text-html">
<h3><span class="passage-display-bcv">彌迦書 6:3-4</span></h3>
<div class="poetry top-1"><p class="line">
<span class="text Mic-6-3"><sup class="versenum">3\xa0</sup>「我的百姓啊，我向你做了甚麼呢？」</span></p></div>
<div class="poetry top-1"><p class="line">
<span class="text Mic-6-4"><sup class="versenum">4\xa0</sup>我曾將你從埃及地領出來。</span></p></div>
</div></div></div>
"""


def test_verse1_not_dropped_when_multi_verse():
    """BUG: When requesting a range starting at verse 1, chapternum verse is dropped."""
    verses = extract_verses(SAMPLE_HTML_MULTI_VERSE)
    verse_nums = [v["verse"] for v in verses]
    assert "1" in verse_nums, f"Verse 1 missing! Got verses: {verse_nums}"
    assert verse_nums[0] == "1", f"Verse 1 should be first, got: {verse_nums}"
    assert "當聽耶和華說的話" in verses[0]["text"], f"Verse 1 text wrong: {verses[0]['text']}"


def test_verse1_single_verse_still_works():
    """Existing fallback: single-verse request with only chapternum."""
    verses = extract_verses(SAMPLE_HTML_SINGLE_VERSE)
    assert len(verses) >= 1
    assert verses[0]["verse"] == "1"
    assert "起初" in verses[0]["text"]


def test_mid_chapter_no_chapternum():
    """Mid-chapter request should work without chapternum."""
    verses = extract_verses(SAMPLE_HTML_NO_CHAPTERNUM)
    verse_nums = [v["verse"] for v in verses]
    assert "3" in verse_nums
    assert "4" in verse_nums
    assert "1" not in verse_nums  # No verse 1 in this request


def test_verse_order_preserved():
    """Verses should come out in order: 1, 2, 3."""
    verses = extract_verses(SAMPLE_HTML_MULTI_VERSE)
    verse_nums = [v["verse"] for v in verses]
    assert verse_nums == ["1", "2", "3"], f"Wrong order: {verse_nums}"


if __name__ == "__main__":
    failed = 0
    for name, func in list(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print(f"  ✓ {name}")
            except AssertionError as e:
                print(f"  ✗ {name}: {e}")
                failed += 1
    sys.exit(1 if failed else 0)
