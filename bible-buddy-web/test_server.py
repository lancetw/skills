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


# ── section headings ──────────────────────────────────────────────────────────
# FHL prefixes the verse a version prints a heading above with "<h2>…</h2>" (出 3:1).

RAW_EXOD_3_1 = "<h2>上帝呼召摩西</h2><u>摩西</u>牧放他岳父<u>米甸</u>祭司的羊羣。"


def test_heading_is_split_off_the_verse():
    text, heading = server.split_heading(RAW_EXOD_3_1)
    assert heading == "上帝呼召摩西"
    assert "上帝呼召摩西" not in text and text.startswith("<u>摩西</u>牧放")


def test_verse_without_a_heading_is_untouched():
    assert server.split_heading("<u>摩西</u>說：「我在這裏。」") == ("<u>摩西</u>說：「我在這裏。」", "")


def test_search_hit_drops_the_heading():
    assert server._clean_hit(RAW_EXOD_3_1) == "摩西牧放他岳父米甸祭司的羊羣。"


# ── the note ledger ───────────────────────────────────────────────────────────
# Minting a note is four chores in the right order — anchor the quote, clip the label, check the
# enums, land on disk — and every note source used to repeat all four. These pin the behaviour so
# the chores can move behind one interface without anyone noticing.

import asyncio
import json

import pytest

VERSES = [
    {"verse": "4", "text": "上帝看光是好的，於是上帝就把光和暗分開。", "footnotes": [], "cuts": []},
    {"verse": "5", "text": "上帝稱光為晝，稱暗為夜。", "footnotes": [], "cuts": []},
]


@pytest.fixture
def desk(tmp_path, monkeypatch):
    """A passage on screen and an empty notes directory, with nothing left over between tests."""
    monkeypatch.setattr(server, "NOTES_DIR", tmp_path / "notes")
    server.passage.update(reference="創世記 1:4-5", version="rcuv", book="創世記",
                          verses=[dict(v) for v in VERSES])
    server.notes.clear()
    server.hidden.clear()
    server._quick_cache.clear()
    server._quick_cost.clear()
    yield tmp_path / "notes"
    server.notes.clear()
    server.hidden.clear()


def run(coro):
    return asyncio.run(coro)


def test_a_quote_anchors_on_the_words_it_names(desk):
    run(server.add_annotation.handler({"verse": 4, "quote": "光和暗", "label": "分開", "body": "", "kind": "lexical"}))
    n = server.notes[-1]
    assert n["anchor"] is not None
    text = VERSES[0]["text"]
    assert text[n["anchor"]["start"]:n["anchor"]["end"]] == "光和暗"


def test_a_quote_the_verse_does_not_contain_becomes_a_verse_level_note(desk):
    r = run(server.add_annotation.handler({"verse": 4, "quote": "不在經文裡", "label": "x", "body": "", "kind": "lexical"}))
    assert server.notes[-1]["anchor"] is None, "a wrong anchor is worse than none"
    assert "對不上" in r["content"][0]["text"], "the agent is told, not left guessing"


def test_a_long_label_is_clipped_wherever_the_note_came_from(desk):
    long = "誤" * 40
    run(server.add_annotation.handler({"verse": 4, "quote": "光", "label": long, "body": "", "kind": "lexical"}))
    assert server.notes[-1]["label"] == server._short_label(long)


def test_a_kind_outside_the_vocabulary_falls_back(desk):
    run(server.add_annotation.handler({"verse": 4, "quote": "光", "label": "x", "body": "", "kind": "lexical"}))
    nid = server.notes[-1]["id"]
    run(server.update_annotation.handler({"id": nid, "label": "y", "body": "b", "kind": "nonsense"}))
    assert server.notes[-1]["kind"] in server.KINDS


def test_every_mint_lands_on_disk_at_once(desk):
    run(server.add_annotation.handler({"verse": 4, "quote": "光", "label": "x", "body": "", "kind": "lexical"}))
    saved = json.loads(server._notes_file().read_text())
    assert [n["id"] for n in saved["notes"]] == [n["id"] for n in server.notes]


def test_a_deleted_note_stays_deleted_when_a_cached_pass_offers_it_again(desk):
    run(server.add_user_note({"verse": "4", "label": "手寫", "body": ""}))
    nid = server.notes[-1]["id"]
    run(server.delete_note(nid))
    assert nid in server.hidden
    assert server._add({"id": nid, "verse": "4", "label": "again"}) is None


def test_the_same_note_is_not_added_twice(desk):
    note = {"id": "abc12345", "verse": "4", "label": "x"}
    assert server._add(dict(note)) is not None
    assert server._add(dict(note)) is None


def test_clearing_automatic_notes_spares_the_ones_the_reader_wrote(desk):
    run(server.add_user_note({"verse": "4", "label": "我的筆記", "body": ""}))
    run(server.add_annotation.handler({"verse": 4, "quote": "光", "label": "agent 的", "body": "", "kind": "lexical"}))
    r = run(server.delete_quick_notes())
    assert r["removed"] == 1
    assert [n["author"] for n in server.notes] == ["user"]


def test_notes_survive_a_round_trip_through_the_file(desk):
    run(server.add_annotation.handler({"verse": 4, "quote": "光和暗", "label": "分開", "body": "b", "kind": "lexical"}))
    run(server.add_user_note({"verse": "5", "label": "手寫", "body": ""}))
    before = [dict(n) for n in server.notes]
    server.notes.clear()
    server.hidden.clear()
    server._load()
    assert server.notes == before


def test_a_hidden_id_survives_a_round_trip_too(desk):
    run(server.add_user_note({"verse": "4", "label": "x", "body": ""}))
    nid = server.notes[-1]["id"]
    run(server.delete_note(nid))
    server.notes.clear()
    server.hidden.clear()
    server._load()
    assert nid in server.hidden


def test_editing_a_note_keeps_its_anchor_and_clips_the_new_label(desk):
    run(server.add_annotation.handler({"verse": 4, "quote": "光和暗", "label": "x", "body": "", "kind": "lexical"}))
    n = server.notes[-1]
    anchor = dict(n["anchor"])
    run(server.edit_note(n["id"], {"label": "誤" * 40, "body": "new"}))
    assert server.notes[-1]["anchor"] == anchor
    assert server.notes[-1]["label"] == server._short_label("誤" * 40)
    assert server.notes[-1]["edited"] is True
