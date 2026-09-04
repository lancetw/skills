"""FHL marks a verse folded into an earlier one with a bare "a" (和合本2010 路 1:2-3, 太 19:5)."""
import corpus
import server


def test_merged_marker_is_not_text():
    v = corpus.normalize({"verse": "2", "text": "a"})
    assert v == {"verse": "2", "text": "", "footnotes": [], "cuts": [], "merged": True}


def test_real_verse_untouched():
    v = corpus.normalize({"verse": "4", "text": "要讓你知道所學的道都是確實的。([1.4]註)"})
    assert v["text"] == "要讓你知道所學的道都是確實的。" and not v.get("merged")
    assert [f["text"] for f in v["footnotes"]] == ["註"]


def test_verse_starting_with_a_is_kept():
    assert corpus.normalize({"verse": "1", "text": "a man"})["text"] == "a man"


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
    text, heading = corpus.split_heading(RAW_EXOD_3_1)
    assert heading == "上帝呼召摩西"
    assert "上帝呼召摩西" not in text and text.startswith("<u>摩西</u>牧放")


def test_verse_without_a_heading_is_untouched():
    assert corpus.split_heading("<u>摩西</u>說：「我在這裏。」") == ("<u>摩西</u>說：「我在這裏。」", "")


def test_search_hit_drops_the_heading():
    assert corpus.clean_hit(RAW_EXOD_3_1) == "摩西牧放他岳父米甸祭司的羊羣。"


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
    server._passes.clear()
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


# ── anchors across the footnote cuts ──────────────────────────────────────────
# Notes saved before the inline "([1.1]…)" footnotes were stripped point into the old text. A wrong
# shift underlines the wrong words, so each position relative to a cut is pinned.

def test_an_offset_before_every_cut_does_not_move():
    assert server._shift(3, [(10, 5)]) == 3


def test_an_offset_after_a_cut_moves_back_by_its_length():
    assert server._shift(20, [(10, 5)]) == 15


def test_an_offset_inside_a_cut_collapses_to_where_the_cut_started():
    assert server._shift(12, [(10, 5)]) == 10


def test_every_earlier_cut_counts():
    assert server._shift(30, [(2, 3), (10, 5)]) == 22


# ── the model pass ────────────────────────────────────────────────────────────
# None of this could be tested before: the pass reached the model itself, so there was nowhere to
# stand between the caller and the API. server.MODEL is that place — this section puts a second
# adapter in it, which is what makes the seam real rather than hypothetical.

from claude_agent_sdk import ResultMessage, SystemMessage  # noqa: E402


class RecordedModel:
    """The model, answered from recorded SDK messages. Every call is logged, so a test can prove the
    API was asked once — or never. `watch` runs after each message, which is where a test can look at
    a pass that is still in flight."""

    def __init__(self, *runs, watch=None):
        self._runs, self._watch, self.calls = list(runs), watch, []

    def __call__(self, prompt, schema):
        self.calls.append(prompt)
        msgs = self._runs.pop(0) if len(self._runs) > 1 else self._runs[0]

        async def gen():
            for m in msgs:
                await asyncio.sleep(0)   # a real call yields to the loop, so a second caller can arrive mid-pass
                yield m
                if self._watch:
                    self._watch()
        return gen()


@pytest.fixture
def model(monkeypatch):
    def use(*runs, watch=None):
        m = RecordedModel(*runs, watch=watch)
        monkeypatch.setattr(server, "MODEL", m)
        return m
    return use


def done(structured, cost=0.5):
    return ResultMessage(subtype="success", duration_ms=1, duration_api_ms=1, is_error=False, num_turns=1,
                         session_id="t", total_cost_usd=cost, structured_output=structured)


def failed(text="API Error: 529 Overloaded"):
    return ResultMessage(subtype="error_during_execution", duration_ms=1, duration_api_ms=1, is_error=True,
                         num_turns=1, session_id="t", result=text, api_error_status=529)


RETRY = SystemMessage(subtype="api_retry", data={"error_status": 529, "attempt": 2, "max_retries": 3,
                                                 "retry_delay_ms": 5000})

TWO_NOTES = {"notes": [
    {"verse": 4, "quote": "光和暗", "label": "分開", "body": "b", "kind": "lexical", "doodle": "lamp"},
    {"verse": 5, "quote": "稱光為晝", "label": "命名", "body": "b", "kind": "history", "doodle": "star"},
]}


def test_a_pass_asks_the_model_once_and_hands_its_notes_to_the_page(desk, model):
    m = model([done(TWO_NOTES)])
    r = run(server.auto_notes_quick())
    assert len(m.calls) == 1
    assert [n["label"] for n in r["notes"]] == ["分開", "命名"]
    assert r["cost"] == 0.5 and r["cached"] is False
    assert {n["pass_cost"] for n in r["notes"]} == {0.5}   # the whole pass's USD rides on each of its notes


def test_asking_again_is_served_from_the_pass_and_does_not_spend_again(desk, model):
    m = model([done(TWO_NOTES)])
    run(server.auto_notes_quick())
    r = run(server.auto_notes_quick())
    assert len(m.calls) == 1
    assert r["cached"] is True
    assert r["notes"] == []            # they are already on the passage; the pass does not offer them twice
    assert len(server.notes) == 2


def test_a_failed_pass_is_not_cached_so_the_button_doubles_as_retry(desk, model):
    m = model([failed()], [done(TWO_NOTES)])
    r = run(server.auto_notes_quick())
    assert "529" in r["error"] and server.notes == []
    assert len(run(server.auto_notes_quick())["notes"]) == 2
    assert len(m.calls) == 2


def test_two_readers_waiting_on_the_same_passage_share_one_pass(desk, model):
    m = model([done(TWO_NOTES)])

    async def both():
        return await asyncio.gather(server.auto_notes_quick(), server.auto_notes_quick())

    a, b = run(both())
    assert len(m.calls) == 1           # a refreshed page must not start a second paid pass
    assert a["cost"] == b["cost"] == 0.5
    assert len(server.notes) == 2


def test_a_retry_shows_on_the_progress_line_and_the_line_clears_when_the_pass_ends(desk, model):
    seen = []
    model([RETRY, done(TWO_NOTES)], watch=lambda: seen.append(server._passes[server._key()].status))
    run(server.auto_notes_quick())
    assert seen[0] == "API 529，重試 2/3（5s 後）"
    assert server._passes[server._key()].status == ""


def test_an_api_error_reaches_the_page_as_an_error_not_a_crash(desk, model):
    model([failed("API Error: 500 Internal")])
    assert "500" in run(server.auto_notes_quick())["error"]


def test_a_one_off_note_leaves_no_record_behind(desk, model):
    model([done({"label": "分開", "body": "b", "kind": "lexical", "doodle": "lamp"})])
    n = run(server.auto_note_one({"verse": "4", "quote": "光和暗"}))
    assert n["label"] == "分開" and n["anchor"] is not None
    assert server._passes == {}        # one key per selected phrase would grow without bound


def test_clearing_automatic_notes_forgets_the_whole_pass(desk, model):
    m = model([done(TWO_NOTES)], [done(TWO_NOTES)])
    run(server.auto_notes_quick())
    run(server.delete_quick_notes())
    assert server._key() not in server._passes
    r = run(server.auto_notes_quick())  # nothing left to serve from, and no id left hidden
    assert len(m.calls) == 2 and len(r["notes"]) == 2


def test_a_pass_that_lands_after_the_reader_moved_on_stays_off_the_new_passage(desk, model):
    old = server._key()
    model([RETRY, done(TWO_NOTES)], watch=lambda: server.passage.update(reference="創世記 1:6-7"))
    assert run(server.auto_notes_quick()) == []
    assert server.notes == []                       # the notes belong to the other passage's file
    assert server._passes[old].notes is not None    # and they stay cached under the key that paid for them
