"""The corpus, answered from recorded FHL responses instead of the network.

None of this could be tested before: the five callers each reached FHL themselves, so there was
nowhere to stand between the caller and the wire. corpus.SOURCE is that place — this file puts a
second adapter in it, which is what makes the seam real rather than hypothetical.
"""
import asyncio

import pytest

import corpus


class Recorded:
    """FHL, as recorded. Every call is logged, so a test can prove the network was never reached."""

    def __init__(self, passage=None, get=None, raises=None):
        self._passage, self._get, self._raises = passage, get or {}, raises
        self.calls = []

    def passage(self, book, chapter, start, end, version):
        self.calls.append(("passage", book, chapter, start, end, version))
        if self._raises:
            raise self._raises
        return {k: (list(v) if isinstance(v, list) else v) for k, v in self._passage.items()}

    def get(self, url, params):
        self.calls.append((url, params))
        if self._raises:
            raise self._raises
        return self._get[url](params) if callable(self._get[url]) else self._get[url]


@pytest.fixture
def source(monkeypatch):
    def use(**kw):
        s = Recorded(**kw)
        monkeypatch.setattr(corpus, "SOURCE", s)
        return s
    return use


def run(coro):
    return asyncio.run(coro)


# ── search ────────────────────────────────────────────────────────────────────
# se.php answers with a numeric book id and an abbreviation; the reader wants the full name, and
# some versions are indexed in their Strong's edition, so the hit arrives full of markup.

SE_HIT = {"bid": 23, "chap": 7, "sec": 14, "chineses": "賽",
          "bible_text": "<h2>以馬內利的預兆</h2>必有<WH5959>童女<WH2029>懷孕生子([7.1]或譯…)"}


def test_a_hit_gets_the_full_book_name_and_a_reference(source):
    source(get={corpus.SE_API: lambda p: ({"record_count": 42} if p.get("count_only") else {"record": [SE_HIT]})})
    r = run(corpus.search("童女", "rcuv", 40))
    hit = r["records"][0]
    assert hit["book"] == "以賽亞書" and hit["ref"] == "以賽亞書 7:14"
    assert r["total"] == 42, "the total comes from the count_only call, not from the page of hits"


def test_a_hit_is_cleaned_of_headings_strongs_numbers_and_translator_notes(source):
    source(get={corpus.SE_API: lambda p: ({"record_count": 1} if p.get("count_only") else {"record": [SE_HIT]})})
    assert run(corpus.search("童女", "rcuv", 40))["records"][0]["text"] == "必有童女懷孕生子"


def test_a_book_id_no_version_knows_falls_back_to_the_abbreviation(source):
    odd = {**SE_HIT, "bid": 999, "bible_text": "經文"}
    source(get={corpus.SE_API: lambda p: ({"record_count": 1} if p.get("count_only") else {"record": [odd]})})
    assert run(corpus.search("x", "rcuv", 40))["records"][0]["book"] == "賽"


def test_a_runaway_limit_is_capped_before_it_reaches_fhl(source):
    s = source(get={corpus.SE_API: lambda p: ({"record_count": 0} if p.get("count_only") else {"record": []})})
    run(corpus.search("x", "rcuv", 9999))
    assert [c[1]["limit"] for c in s.calls if "limit" in c[1]] == [200]


# ── interlinear ───────────────────────────────────────────────────────────────

QP = {"N": 1, "record": [
    {"wid": 0, "word": "  לָכֵן  יִתֵּן  ", "exp": " 因此  祂必賜 "},
    {"wid": 1, "word": "עַלְמָה", "sn": "5959", "pro": "名詞", "wform": "陰性單數", "orig": "almah", "exp": "年輕女子", "remark": None},
]}


def test_the_whole_verse_and_its_literal_rendering_come_off_record_zero(source):
    source(get={corpus.QP_API: QP})
    r = run(corpus.interlinear("以賽亞書", 7, 14))
    assert r["text"] == "לָכֵן יִתֵּן" and r["literal"] == "因此 祂必賜"
    assert [w["orig"] for w in r["words"]] == ["almah"], "record 0 is the header, not a word"


def test_a_hebrew_verse_is_flagged_so_the_page_can_set_its_direction(source):
    source(get={corpus.QP_API: QP})
    assert run(corpus.interlinear("以賽亞書", 7, 14))["ot"] is True
    source(get={corpus.QP_API: {**QP, "N": 0}})
    assert run(corpus.interlinear("以賽亞書", 7, 14))["ot"] is False


def test_a_null_field_becomes_an_empty_string_not_a_crash(source):
    source(get={corpus.QP_API: QP})
    assert run(corpus.interlinear("以賽亞書", 7, 14))["words"][0]["remark"] == ""


def test_a_verse_with_no_analysis_says_so_and_keeps_the_header(source):
    source(get={corpus.QP_API: {"N": 0, "record": [{"wid": 0, "word": "x", "exp": "y"}]}})
    r = run(corpus.interlinear("馬太福音", 1, 1))
    assert r["error"] and r["words"] == [] and r["text"] == "x"


def test_an_unknown_book_never_reaches_the_network(source):
    s = source(get={})
    with pytest.raises(corpus.CorpusError, match="未知書卷"):
        run(corpus.interlinear("哈利波特", 1, 1))
    assert s.calls == []


# ── lexicon ───────────────────────────────────────────────────────────────────

def test_a_strongs_entry_is_flattened_to_the_three_fields_the_card_shows(source):
    source(get={corpus.SD_API: {"record": [{"sn": "5959", "orig": "עַלְמָה", "dic_text": "  young woman  "}]}})
    assert run(corpus.lexicon("5959", ot=True)) == {"sn": "5959", "orig": "עַלְמָה", "text": "young woman"}


def test_an_empty_dictionary_answer_still_names_the_number_that_was_asked_for(source):
    source(get={corpus.SD_API: {"record": []}})
    assert run(corpus.lexicon("9999", ot=False)) == {"sn": "9999", "orig": "", "text": ""}


def test_the_testament_decides_which_dictionary_is_asked(source):
    s = source(get={corpus.SD_API: {"record": []}})
    run(corpus.lexicon("5959", ot=True))
    run(corpus.lexicon("3056", ot=False))
    assert [c[1]["N"] for c in s.calls] == [1, 0]


# ── passages ──────────────────────────────────────────────────────────────────

def passage(*verses, reference="路加福音 1:1-6"):
    return {"reference": reference, "version": "和合本2010",
            "verses": [{"verse": str(n), "text": t} for n, t in verses]}


def test_a_passage_comes_back_with_its_footnotes_split_off(source):
    source(passage=passage((4, "要讓你知道所學的道都是確實的。([1.4]註)")))
    v = run(corpus.verses("路加福音", 1, 4, 4, "rcuv"))["verses"][0]
    assert v["text"] == "要讓你知道所學的道都是確實的。"
    assert [f["text"] for f in v["footnotes"]] == ["註"]


def test_a_verse_folded_into_the_previous_one_is_marked_not_rendered(source):
    source(passage=passage((2, "a"), (3, "真經文")))
    vs = run(corpus.verses("路加福音", 1, 2, 3, "rcuv"))["verses"]
    assert vs[0]["merged"] is True and vs[0]["text"] == ""
    assert not vs[1].get("merged")


def test_asking_for_the_whole_chapter_reads_as_the_chapter(source):
    source(passage=passage((1, "a1"), (2, "b"), reference="約翰福音 1:1-2"))
    assert run(corpus.verses("約翰福音", 1, 1, 200, "rcuv"))["reference"] == "約翰福音 1"


def test_verse_one_to_past_the_end_is_the_whole_chapter_however_it_was_asked(source):
    source(passage=passage((1, "a1"), (2, "b"), reference="約翰福音 1:1-2"))
    assert run(corpus.verses("約翰福音", 1, 1, 99, "rcuv"))["reference"] == "約翰福音 1"


def test_a_range_that_does_not_start_at_one_is_clamped_to_the_last_verse(source):
    source(passage=passage((2, "b"), reference="約翰福音 1:2-2"))
    assert run(corpus.verses("約翰福音", 1, 2, 99, "rcuv"))["reference"] == "約翰福音 1:2-2"


def test_a_single_verse_reads_as_one_verse(source):
    source(passage=passage((14, "必有童女懷孕生子"), reference="以賽亞書 7:14"))
    assert run(corpus.verses("以賽亞書", 7, 14, 14, "rcuv"))["reference"] == "以賽亞書 7:14"


# ── failure ───────────────────────────────────────────────────────────────────
# Every caller used to write its own sentence for this. There is one place for it now, and it is
# the reader's language, not a traceback.

@pytest.mark.parametrize("call, doing", [
    (lambda: corpus.verses("路加福音", 1, 1, 5, "rcuv"), "經文載入"),
    (lambda: corpus.search("x", "rcuv", 10), "搜尋"),
    (lambda: corpus.interlinear("以賽亞書", 7, 14), "原文分析"),
    (lambda: corpus.lexicon("5959", ot=True), "字典"),
])
def test_a_dead_network_reaches_the_reader_as_a_sentence(source, call, doing):
    source(raises=OSError("connection refused"))
    with pytest.raises(corpus.CorpusError) as e:
        run(call())
    assert doing in str(e.value) and "connection refused" in str(e.value)


def test_the_original_language_column_follows_the_testament():
    assert corpus.original_language_version("以賽亞書") == "bhs"
    assert corpus.original_language_version("馬太福音") == "fhlwh"
