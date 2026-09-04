"""FHL marks a verse folded into an earlier one with a bare "a" (和合本2010 路 1:2-3, 太 19:5)."""
import server


def test_merged_marker_is_not_text():
    v = server._normalize({"verse": "2", "text": "a"})
    assert v == {"verse": "2", "text": "", "footnotes": [], "cuts": [], "merged": True}


def test_real_verse_untouched():
    v = server._normalize({"verse": "4", "text": "要讓你知道所學的道都是確實的。([1.4]註)"})
    assert v["text"] == "要讓你知道所學的道都是確實的。" and not v.get("merged")
    assert [f["text"] for f in v["footnotes"]] == ["註"]


def test_verse_starting_with_a_is_kept():
    assert server._normalize({"verse": "1", "text": "a man"})["text"] == "a man"


if __name__ == "__main__":
    test_merged_marker_is_not_text(); test_real_verse_untouched(); test_verse_starting_with_a_is_kept()
    print("ok")


# ── label width ───────────────────────────────────────────────────────────────
# Labels mix Chinese with Latin transliterations; the budget is display width, not characters.

def test_mixed_label_fits_where_a_character_slice_would_amputate():
    assert server._short_label("誤讀 · kecharitomene 蒙恩") == "誤讀 · kecharitomene 蒙恩"


def test_twenty_chinese_characters_is_the_ceiling():
    assert server._short_label("誤" * 20) == "誤" * 20
    assert server._short_label("誤" * 21) == "誤" * 19 + "…"


def test_overlong_label_never_cuts_a_latin_word_in_half():
    out = server._short_label("誤讀 · " + "word " * 10)
    assert out.endswith("…") and "wor…" not in out and " wo…" not in out
