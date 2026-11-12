"""Tests for the markdown-to-html Markdown -> readable-HTML converter.

These encode WHY the conversion matters for a learning document:
- ASCII flow charts only help if they stay aligned (verbatim, no wrapping).
- The tech-selection / terminology tables only help if they become real tables.
- It is a Traditional Chinese doc, so the page must declare zh-TW + UTF-8.
- The 7 sections only stay navigable if the TOC is built from the headings.
"""

import re

from md_to_html import _derive_title, _term_key, convert, main

SAMPLE_MD = """# FORlancetw.md

## 專案概述

這是一個說明專案。

## 技術選型

| 技術 | 用途 | 為何選它 |
|------|------|----------|
| Python | 後端 | 生態成熟 |

## 技術架構

```
+--------+     +--------+
| Explore| --> |  Read  |
+--------+     +--------+
```
"""


def test_tables_become_html_tables():
    # The tech-selection table is core content; it must render as a real table.
    html = convert(SAMPLE_MD, timestamp="2026-06-11 12:00")
    assert "<table>" in html
    assert "<th>技術</th>" in html


def test_ascii_diagram_preserved_verbatim_in_pre():
    # If the diagram's spacing is mangled or wrapped, the chart is useless.
    html = convert(SAMPLE_MD, timestamp="2026-06-11 12:00")
    assert "<pre>" in html
    assert "+--------+     +--------+" in html


def test_declares_traditional_chinese_and_utf8():
    html = convert(SAMPLE_MD, timestamp="2026-06-11 12:00")
    assert 'lang="zh-TW"' in html
    assert 'charset="UTF-8"' in html


def test_toc_built_from_section_headings():
    # The "好讀版" navigation aid: the 7 sections should appear in the TOC.
    html = convert(SAMPLE_MD, timestamp="2026-06-11 12:00")
    assert 'class="toc"' in html
    assert "專案概述" in html
    assert "技術選型" in html


def test_mobile_toc_opens_as_a_drawer():
    # On phones the sidebar TOC is hidden (no room); it must instead be reachable
    # via a 目錄 toggle that slides it in as a drawer over a dimmed backdrop. The
    # markers: the button, the open/close global, the slide-in rule, the backdrop,
    # and the anchored id the button controls.
    html = convert(SAMPLE_MD, timestamp="t")
    assert '<button class="toc-toggle"' in html  # the 目錄 button element
    assert "toggleToc" in html  # the open/close global it calls
    assert 'id="toc-nav"' in html  # the nav the button controls (aria-controls)
    assert "body.toc-open nav.toc" in html  # the drawer slides in when open
    assert '<div class="toc-backdrop"' in html  # dimmed backdrop behind the open drawer


def test_no_toc_drawer_when_doc_has_no_sections():
    # A heading-only doc has no TOC to open, so none of the drawer machinery (and no
    # dead 目錄 button) should be emitted. The .toc-* CSS rules still live in the
    # stylesheet — harmless without the elements — so assert on the elements/runtime.
    html = convert("# 標題\n\n只有一段內文，沒有章節標題。\n", timestamp="t")
    assert '<button class="toc-toggle"' not in html
    assert '<div class="toc-backdrop"' not in html
    assert "toggleToc" not in html


def test_toc_opener_is_a_centered_css_hamburger():
    # The mobile 目錄 opener is an icon-only button. The hamburger is drawn in CSS
    # (an empty span + ::before/::after bars), NOT a ☰ glyph — a glyph inherits the
    # reading font and sits off-centre differently in each font. aria-label gives the
    # accessible name since there is no text.
    html = convert(SAMPLE_MD, timestamp="t")
    assert 'aria-label="開啟目錄"' in html  # accessible name (no visible text)
    assert (
        '<span class="toc-toggle__bars" aria-hidden="true"></span></button>' in html
    )  # empty span
    assert "☰" not in html  # no font glyph anywhere
    assert ".toc-toggle__bars::before" in html  # the CSS-drawn bars
    assert ".toc-toggle__bars::after" in html


def test_self_check_summary_disables_text_selection():
    # Toggling a self-check by clicking/double-clicking the summary must not select
    # the question text, so the summary opts out of user selection.
    html = convert(SAMPLE_MD, timestamp="t")
    summary = html.split("details.self-check > summary {", 1)[1].split("}", 1)[0]
    assert "user-select: none" in summary


def test_menu_rides_at_the_top_of_the_toc_not_floating():
    # The theme/font menu should sit at the top of the left TOC column (so on a
    # centred wide layout it is not orphaned in the far top-left corner). With a TOC
    # present, the menu lives in .toc-controls INSIDE nav.toc, and the floating
    # .controls fallback cluster is not emitted at all.
    html = convert(SAMPLE_MD, timestamp="t")
    assert '<div class="toc-controls">' in html
    assert '<div class="controls">' not in html  # no orphaned floating cluster
    nav = html.split('<nav class="toc"', 1)[1].split("</nav>", 1)[0]
    assert 'class="font-select"' in nav  # the font switcher is within the TOC


def test_doc_without_toc_keeps_a_floating_menu():
    # A doc with no headings has no TOC to host the menu, so it falls back to the
    # small fixed .controls cluster — theme/font must still be available.
    html = convert("# 標題\n\n只有一段內文，沒有章節標題。\n", timestamp="t")
    assert '<div class="controls">' in html
    assert 'class="font-select"' in html
    assert '<div class="toc-controls">' not in html  # element absent (CSS rule stays)


def test_timestamp_is_injectable_for_determinism():
    html = convert(SAMPLE_MD, timestamp="2026-06-11 12:00")
    assert "2026-06-11 12:00" in html


def test_title_derived_from_first_h1():
    assert _derive_title(SAMPLE_MD, "fallback") == "FORlancetw.md"
    assert _derive_title("no heading here", "fallback") == "fallback"


# --- Mermaid diagram rendering -------------------------------------------------

MERMAID_MD = """# FORlancetw.md

## 技術架構

```mermaid
flowchart LR
    A[讀取 FCS] --> B[解析]
    B --> C[分析]
    C --> D[產生報告]
```
"""


def test_mermaid_block_becomes_mermaid_element():
    # mermaid.js scans for class="mermaid"; a raw highlighted code block won't render.
    html = convert(MERMAID_MD, timestamp="t")
    assert '<pre class="mermaid">' in html
    assert 'class="language-mermaid"' not in html


def test_mermaid_chinese_labels_preserved():
    # The whole point of Mermaid over ASCII: Chinese labels render directly.
    html = convert(MERMAID_MD, timestamp="t")
    assert "讀取 FCS" in html
    assert "產生報告" in html


def test_mermaid_runtime_injected_only_when_needed():
    # Don't pull a JS library into docs that have no diagrams.
    with_diagram = convert(MERMAID_MD, timestamp="t")
    no_diagram = convert("# Title\n\n## 概述\n\n純文字，沒有圖。\n", timestamp="t")
    assert "cdn.jsdelivr.net/npm/mermaid" in with_diagram
    assert "cdn.jsdelivr.net/npm/mermaid" not in no_diagram


def test_plain_code_block_not_treated_as_mermaid():
    # Regression: a plain ``` fence (e.g. an ASCII fallback) stays a normal <pre>.
    html = convert(SAMPLE_MD, timestamp="t")
    assert '<pre class="mermaid">' not in html
    assert "cdn.jsdelivr.net/npm/mermaid" not in html


# --- Dark / light theme toggle -------------------------------------------------


def test_theme_toggle_button_is_present_and_labelled():
    # A reader must be able to flip the theme manually; the control needs an
    # accessible label so screen-reader / keyboard users can find it.
    html = convert(SAMPLE_MD, timestamp="t")
    assert 'class="theme-toggle"' in html
    assert "toggleTheme()" in html
    assert "aria-label" in html


def test_dark_theme_is_attribute_driven_not_only_media_query():
    # A button can flip an attribute but cannot flip prefers-color-scheme, so the
    # dark palette must hang off [data-theme="dark"] for the toggle to do anything.
    html = convert(SAMPLE_MD, timestamp="t")
    assert '[data-theme="dark"]' in html


def test_initial_theme_resolves_before_paint_and_persists():
    # No flash of the wrong theme on load: an early script resolves the theme from
    # the saved choice, falling back to the system preference, and remembers it.
    html = convert(SAMPLE_MD, timestamp="t")
    assert "localStorage" in html
    assert "prefers-color-scheme" in html
    assert "data-theme" in html


def test_mermaid_uses_tuned_palette_and_rerenders_on_toggle():
    # Charts must look native in BOTH modes: a custom themeVariables palette (not
    # Mermaid's generic themes), and a re-render when the theme changes so toggling
    # never leaves a diagram painted in the previous mode's colors.
    html = convert(MERMAID_MD, timestamp="t")
    assert "themeVariables" in html
    assert "themechange" in html


def test_theme_toggle_works_without_pulling_in_mermaid():
    # The toggle is page-level chrome; a diagram-free doc still gets it, but must
    # not pay for the Mermaid runtime just to support theming.
    html = convert(SAMPLE_MD, timestamp="t")
    assert 'class="theme-toggle"' in html
    assert "themechange" in html
    assert "cdn.jsdelivr.net/npm/mermaid" not in html


# --- Editorial "好讀版" reading aids ---------------------------------------------

NO_DIAGRAM_MD = "# Title\n\n## 概述\n\n純文字，沒有圖。\n\n## 細節\n\n更多內容。\n"


def test_reading_progress_bar_injected():
    # A long learning doc needs a sense of "how far in am I"; the readable version
    # ships a scroll-progress bar (built by the page script, hence the id string).
    html = convert(SAMPLE_MD, timestamp="t")
    assert "reading-progress" in html


def test_sections_auto_numbered_via_css_counter():
    # The 7 sections read as a numbered sequence, but the numbers must come from a
    # CSS counter — NOT the Markdown — so the source stays clean and the numbers
    # renumber themselves if a section moves.
    html = convert(SAMPLE_MD, timestamp="t")
    assert "counter-increment: section" in html
    assert "content: counter(section)" in html


def test_toc_tracks_the_section_being_read():
    # The "好讀版" navigation: the sidebar must highlight the section you are
    # reading (scroll-spy), and that highlight is applied by the page script.
    html = convert(SAMPLE_MD, timestamp="t")
    assert "nav.toc a.active" in html  # the active style exists
    assert "classList.toggle('active'" in html  # ...and the script applies it


def test_toc_click_locks_highlight_so_it_does_not_flicker():
    # Clicking a TOC link triggers a smooth scroll past intermediate sections; the
    # highlight locks to the clicked target and is released only when the scroll
    # arrives (or on scrollend), so it never sweeps through them ('亂跳'). Headings
    # also get scroll-margin so they land at the spy line.
    html = convert(SAMPLE_MD, timestamp="t")
    assert "scrollend" in html
    assert "lockTarget" in html
    assert "scroll-margin-top" in html


def test_reading_aids_present_even_without_diagrams():
    # The progress bar and scroll-spy are page-level chrome: a diagram-free doc
    # still gets them, but must not pull in the Mermaid runtime to do so.
    html = convert(NO_DIAGRAM_MD, timestamp="t")
    assert "reading-progress" in html
    assert "nav.toc a.active" in html
    assert "cdn.jsdelivr.net/npm/mermaid" not in html


def test_mermaid_palette_matches_both_page_themes():
    # A diagram must read as part of the document in BOTH modes, so the runtime
    # carries a per-theme palette tuned to the page (the 朱紅 accent in light, its
    # softer dark variant) and uses the page's serif font.
    html = convert(MERMAID_MD, timestamp="t")
    assert "PALETTE" in html
    assert "primaryBorderColor: '#b5402f'" in html  # light: seal-red border
    assert "primaryBorderColor: '#e69478'" in html  # dark: softened variant
    assert "fontFamily" in html


def test_readable_version_uses_serif_for_chinese():
    # The 好讀版 targets comfortable long-form Chinese reading (書卷感): the body
    # is set in a serif stack that includes a CJK serif, not a sans-serif.
    html = convert(SAMPLE_MD, timestamp="t")
    assert "Noto Serif TC" in html or "Songti TC" in html
    assert "serif" in html


# --- Refinements: table scroll, natural wrapping, enlargeable diagrams ----------


def test_tables_wrapped_for_horizontal_scroll():
    # A wide table must scroll on its own instead of overflowing the page, so the
    # converter wraps each <table> in a scroll container styled overflow-x:auto.
    html = convert(SAMPLE_MD, timestamp="t")
    assert '<div class="table-wrap">' in html
    assert "<table>" in html  # the table itself is still there, just wrapped
    assert ".table-wrap { overflow-x: auto" in html
    # Headers must not wrap, and every cell keeps a readable minimum width, so a
    # wide table grows and the wrapper scrolls instead of squashing CJK columns.
    assert "white-space: nowrap" in html
    assert "min-width: 7em" in html


def test_overflowing_table_shows_an_always_visible_scrollbar():
    # The reported bug: a wrapped wide table is clipped at the page edge with NO
    # horizontal scrollbar to drag. On macOS the default scrollbar is an
    # auto-hiding overlay, so overflow-x:auto alone leaves the bar invisible at
    # rest — the reader sees a cut-off table and no hint it scrolls. A single
    # global ::-webkit-scrollbar rule (shared by the page, code blocks, the TOC
    # and wide tables) opts every scroll box into a persistent, always-visible
    # classic bar that reserves layout height. The rule must declare a height so
    # the bar shows, and must NOT declare scrollbar-width, which on Chrome 121+
    # suppresses ::-webkit-scrollbar and reverts to the overlay.
    html = convert(SAMPLE_MD, timestamp="t")
    assert ".table-wrap { overflow-x: auto" in html  # the wide table is a scroll box
    assert re.search(r"::-webkit-scrollbar\s*\{[^}]*height:\s*\d", html), (
        "the scrollbar must declare a height so it stays visible, not overlay"
    )
    assert "::-webkit-scrollbar-thumb" in html  # a themed draggable thumb
    assert "scrollbar-width:" not in html  # declaring it would disable the webkit bar in Chrome


def test_natural_line_breaking_for_headings_and_body():
    # Headings and body should wrap naturally: balanced heading lines, a tidy body
    # rag, and long unbreakable runs (URLs / code) breaking instead of overflowing.
    html = convert(SAMPLE_MD, timestamp="t")
    assert "text-wrap: balance" in html  # headings
    assert "text-wrap: pretty" in html  # body
    assert "overflow-wrap: break-word" in html


def test_diagram_can_be_opened_enlarged_in_lightbox():
    # An inline diagram can get small; the readable version offers a "放大" control
    # that opens the rendered SVG in an in-page lightbox with zoom and pan.
    # (It once opened a new tab via window.open; the lightbox replaced that —
    # it works offline, on mobile, and is not popup-blocked.)
    html = convert(MERMAID_MD, timestamp="t")
    assert "mermaid-zoom" in html
    assert "openEnlarged" in html
    assert "buildLightbox" in html


def test_zoom_control_not_added_without_a_diagram():
    # The zoom control lives in the Mermaid runtime, so a diagram-free doc (which
    # never loads that runtime) does not get the open-enlarged behaviour.
    html = convert(NO_DIAGRAM_MD, timestamp="t")
    assert "openEnlarged" not in html
    assert "cdn.jsdelivr.net/npm/mermaid" not in html


# --- Reader-selectable Chinese font switcher ------------------------------------


def test_font_switcher_offers_the_six_reading_fonts():
    # The reader can switch the Chinese font; all six are wired into the registry.
    html = convert(SAMPLE_MD, timestamp="t")
    assert 'class="font-select"' in html
    for family in [
        "Noto+Serif+TC",
        "Iansui",
        "LXGW+WenKai+TC",
        "Bpmf+Iansui",
        "Noto+Sans+TC",
        "Huninn",
    ]:
        assert family in html


def test_font_choice_persists_and_lazy_loads_with_kai_default():
    # The choice is remembered (localStorage) and each font loads on demand (a
    # data-font-css marker per injected stylesheet); 楷體 (Iansui) is the default.
    html = convert(SAMPLE_MD, timestamp="t")
    assert "markdown-to-html-font" in html
    assert "setFont" in html
    assert "data-font-css" in html
    assert "var DEFAULT = 'kai'" in html


def test_diagram_follows_the_selected_font():
    # A diagram must match the prose font and re-render when the reader switches.
    html = convert(MERMAID_MD, timestamp="t")
    assert "getComputedStyle(document.body).fontFamily" in html
    assert "window.addEventListener('fontchange', render)" in html


# --- ★ Insight callout ---------------------------------------------------------

INSIGHT_MD = (
    "# T\n\n## 概述\n\n"
    "★ Insight ─────────────────────────────────────\n"
    "- 第一個重點\n"
    "- 第二個重點\n"
    "─────────────────────────────────────────────────\n\n"
    "後續內文。\n"
)


def test_insight_block_becomes_styled_callout():
    # The model writes ★ Insight box-drawing blocks; they must render as a styled
    # callout (not raw box rules), with the inner points kept as real Markdown.
    html = convert(INSIGHT_MD, timestamp="t")
    assert '<div class="insight"' in html
    assert "<li>第一個重點</li>" in html  # inner parsed as a real list
    assert "─────" not in html  # the box-drawing rules are gone


def test_insight_callout_label_and_styling_present():
    html = convert(INSIGHT_MD, timestamp="t")
    assert ".insight" in html
    assert "★ 重點" in html  # the CSS label


# The Explanatory output style (and the memory template) present the Insight block
# with the rule lines wrapped in backticks, so the model writes them that way in
# practice. The converter must recognise that form too — otherwise the backticks
# turn each rule into inline <code> and the callout is never built.
INSIGHT_MD_BACKTICKS = (
    "# T\n\n## 概述\n\n"
    "`★ Insight ─────────────────────────────────────`\n"
    "- 第一個重點\n"
    "- 第二個重點\n"
    "`─────────────────────────────────────────────────`\n\n"
    "後續內文。\n"
)


def test_insight_block_with_backtick_wrapped_rules_becomes_callout():
    # Regression for the real-world form: the model wraps the ★ Insight rule lines
    # in backticks (per the output-style / memory template), so the converter must
    # still emit the styled callout instead of leaking inline <code> rule lines.
    html = convert(INSIGHT_MD_BACKTICKS, timestamp="t")
    assert '<div class="insight"' in html
    assert "<li>第一個重點</li>" in html  # inner parsed as a real list
    assert "─────" not in html  # the box-drawing rules are gone
    assert "<code>★ Insight" not in html  # the raw backtick line must not survive


def test_horizontal_rule_not_mistaken_for_insight():
    # A real '---' rule (hyphens) must stay an <hr>, never be eaten as an insight
    # block (the matcher only accepts U+2500 rules).
    html = convert("# T\n\n## 概述\n\n一段。\n\n---\n\n另一段。\n", timestamp="t")
    assert "<hr" in html
    assert '<div class="insight"' not in html


# --- Multi-line metadata blockquote keeps its line breaks -----------------------

MULTILINE_QUOTE_MD = (
    "# T\n\n> 影片來源：作者 A\n> 作者技能庫：某處\n> 電子報：另一處\n\n## 概述\n\n內文。\n"
)


def test_multiline_blockquote_lines_break_not_run_together():
    # The model writes a metadata blockquote as separate `>` lines (source / author
    # / newsletter). Standard Markdown folds them into one paragraph whose soft
    # newlines collapse to spaces, so the readable HTML must render the preserved
    # source newlines as real breaks via white-space: pre-line — otherwise the
    # three lines run together on one line ("影片來源… 作者技能庫… 電子報…").
    html = convert(MULTILINE_QUOTE_MD, timestamp="t")
    assert "white-space: pre-line" in html  # the mechanism that shows the breaks
    bq = re.search(r"<blockquote>.*?</blockquote>", html, re.DOTALL).group(0)
    # the author's newlines survive inside the paragraph for pre-line to honour
    assert "作者 A\n" in bq
    assert "某處\n" in bq


# --- main(): report openable file locations -------------------------------------


def test_main_prints_absolute_openable_paths(tmp_path, monkeypatch, capsys):
    # The whole point of the run is for the user to open the output. Even when the
    # converter is invoked with a RELATIVE argument (the normal case), it must report
    # COMPLETE paths for BOTH files so the user can click/open them, not a bare
    # relative filename that only resolves from the original cwd.
    md = tmp_path / "FORx.md"
    md.write_text("# T\n\n## 概述\n\n內容。\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    rc = main(["FORx.md"])  # relative input, as a real invocation passes
    assert rc == 0

    out = capsys.readouterr().out
    assert str((tmp_path / "FORx.md").resolve()) in out  # the Markdown source
    assert str((tmp_path / "FORx.html").resolve()) in out  # the HTML 好讀版


# --- Manual section numbering: don't double-number ------------------------------
# Section numbers come from a CSS counter (h2::before, plus the TOC's tnum counter).
# If the author ALSO writes a number in the heading ("## 1. 介紹", "## 一、背景"),
# the reader sees it twice ("1  1. 介紹"). The converter must detect an
# already-numbered document and switch the CSS counter off for it — while leaving
# clean docs auto-numbered, and never mistaking a leading CONTENT number
# ("## 2024 年度回顧", "## 5 個重點") for a section number.

MANUAL_NUMBERED_MD = (
    "# 手冊\n\n## 1. 介紹\n\n內文。\n\n## 2. 安裝\n\n內文。\n\n## 一、附錄\n\n內文。\n"
)

CONTENT_NUMBER_MD = (
    "# 報告\n\n## 2024 年度回顧\n\n內文。\n\n## 5 個重點\n\n內文。\n\n## 心得\n\n內文。\n"
)


def test_manual_numbering_suppresses_the_css_section_counter():
    # Author numbered every section; the CSS counter must be switched off for this
    # document so the number is never rendered a second time — on the heading AND
    # in the sidebar TOC (which has its own counter).
    html = convert(MANUAL_NUMBERED_MD, timestamp="t")
    assert 'class="manual-numbering"' in html
    assert "body.manual-numbering h2::before" in html
    assert "body.manual-numbering h3::before" in html  # subsection counter off too
    assert "body.manual-numbering nav.toc" in html


def test_clean_headings_keep_the_css_auto_numbering():
    # No manual numbers: the advertised auto-numbering must stay on (no opt-out flag,
    # so the existing h2::before counter still applies).
    html = convert(SAMPLE_MD, timestamp="t")
    assert 'class="manual-numbering"' not in html  # <body> is not flagged


def test_leading_content_numbers_are_not_treated_as_section_numbers():
    # "2024" and "5" are content, not section numbers (no ordinal separator follows).
    # Mis-detecting them would wrongly disable the document's auto-numbering.
    html = convert(CONTENT_NUMBER_MD, timestamp="t")
    assert 'class="manual-numbering"' not in html  # <body> is not flagged


def test_detects_arabic_and_chinese_numbering_schemes():
    # The author's number may be Arabic, Chinese, full-width, parenthesised, dotted
    # multi-level, or 第N章/節 — every form must read as a manual section number.
    from md_to_html import _has_manual_section_numbers

    for md in [
        "## 1. 甲\n## 2. 乙\n",  # Arabic + dot
        "## 1、甲\n## 2、乙\n",  # Arabic + 、
        "## 1) 甲\n## 2) 乙\n",  # Arabic + )
        "## （1）甲\n## （2）乙\n",  # full-width parenthesised
        "## １. 甲\n## ２. 乙\n",  # full-width digits
        "## 1.1 甲\n## 1.2 乙\n",  # dotted multi-level
        "## 一、甲\n## 二、乙\n",  # Chinese numeral + 、
        "## （一）甲\n## （二）乙\n",  # parenthesised Chinese
        "## 第一章 甲\n## 第二章 乙\n",  # 第N章
        "## 第3節 甲\n## 第4節 乙\n",  # 第N節 with Arabic
    ]:
        assert _has_manual_section_numbers(md), md


def test_content_and_unnumbered_headings_are_not_flagged():
    # Bare numbers with no separator are content; Chinese numerals used as words
    # ("十分", "一起") are not section numbers either.
    from md_to_html import _has_manual_section_numbers

    for md in [
        "## 概述\n## 安裝\n",  # no numbers at all
        "## 2024 年度回顧\n## 心得\n",  # leading year = content
        "## 5 個重點\n## 結論\n",  # leading count = content
        "## 十分重要\n## 一起努力\n",  # Chinese numeral as a word, no separator
    ]:
        assert not _has_manual_section_numbers(md), md


def test_manually_numbered_h3_also_flags_the_doc():
    # H3 are now auto-numbered hierarchically (1.1, 1.2). So a doc whose H3 already
    # carry manual numbers must ALSO be flagged — otherwise the new H3 counter would
    # render a second number ("1.1  1.1 細節"). Detection therefore looks at H3 too.
    md = "# T\n\n## 概述\n\n### 1.1 細節\n\n### 1.2 範圍\n\n## 結論\n"
    html = convert(md, timestamp="t")
    assert 'class="manual-numbering"' in html


def test_manual_numbering_detected_at_either_heading_level():
    # The whole doc is flagged when EITHER level is mostly manually numbered, so
    # neither "numbered H2 + clean H3" nor "clean H2 + numbered H3" double-numbers.
    from md_to_html import _has_manual_section_numbers

    assert _has_manual_section_numbers("## 1. 甲\n### 工具\n### 流程\n")  # H2 numbered
    assert _has_manual_section_numbers("## 概述\n### 1.1 甲\n### 1.2 乙\n")  # H3 numbered
    assert not _has_manual_section_numbers("## 概述\n### 背景\n### 目標\n")  # all clean


# --- Hierarchical subsection (H3) auto-numbering --------------------------------
# H2 sections are auto-numbered; subsections (H3) should read as part of the same
# scheme — "1.1", "1.2" — from a NESTED CSS counter so the Markdown source stays
# clean. Stops at H3 (no "1.1.1.1" bureaucracy). The sidebar TOC mirrors it.

SECTIONED_MD = (
    "# 報告\n\n## 概述\n\n### 背景\n\n內文\n\n### 目標\n\n內文\n\n## 方法\n\n### 步驟\n\n內文\n"
)


def test_subsections_auto_numbered_hierarchically_via_css_counter():
    # H3 shows "<section>.<subsection>" from a nested counter; H2 restarts the
    # sub-counter so each section's subsections begin again at .1.
    html = convert(SECTIONED_MD, timestamp="t")
    assert "counter-reset: subsection" in html  # h2 restarts the sub-counter
    assert "counter-increment: subsection" in html  # each h3 advances it
    assert 'content: counter(section) "." counter(subsection)' in html


def test_toc_subsections_numbered_hierarchically():
    # The sidebar mirrors the heading numbering: nested H3 entries read "1.1".
    html = convert(SECTIONED_MD, timestamp="t")
    assert "counter-reset: tsub" in html
    assert 'content: counter(tnum) "." counter(tsub)' in html


# --- 自我檢核 hint shows while collapsed ----------------------------------------
# A self-check may open with a "> 先自己想，再展開對照。" nudge (a Markdown blockquote).
SELF_CHECK_WITH_HINT_MD = (
    "# T\n\n## 概述\n\n一段內文。\n\n"
    '<details class="self-check" markdown="1">\n'
    "<summary>自我檢核：資料經過哪幾層？</summary>\n\n"
    "> 先自己想，再展開對照。\n\n"
    "- 讀取層\n- 解析層\n\n"
    "</details>\n\n"
)


def test_self_check_hint_shows_while_collapsed_not_only_when_expanded():
    # The nudge must be read BEFORE expanding, so it cannot live in the hidden body.
    # It is lifted into the always-visible <summary>, and dropped (via CSS) once open.
    html = convert(SELF_CHECK_WITH_HINT_MD, timestamp="t")
    summary = re.search(r"<summary>(.*?)</summary>", html, re.DOTALL).group(1)
    assert "先自己想，再展開對照。" in summary
    assert '<span class="self-check-hint">' in summary
    assert "<blockquote>" not in html  # not left hidden in the body
    m = re.search(r"details\.self-check\[open\] > summary \.self-check-hint\s*\{([^}]*)\}", html)
    assert m and "display: none" in m.group(1)


def test_self_check_collapsed_marker_is_a_circled_question_mark():
    # The unanswered marker is a "?" drawn inside a CSS ring (a help-style badge), not
    # an emoji glyph — so it renders in the seal-red accent and matches the page.
    html = convert(SELF_CHECK_WITH_HINT_MD, timestamp="t")
    m = re.search(r"details\.self-check > summary::before\s*\{([^}]*)\}", html)
    assert m, "the collapsed self-check marker needs a ::before rule"
    rule = m.group(1)
    assert 'content: "?"' in rule
    assert "border-radius: 50%" in rule  # the ring around the ?


# --- Glossary term tooltips ----------------------------------------------------
GLOSSARY_MD = (
    "# T\n\n## 概述\n\n"
    "深類別是好設計;classitis 則相反。複雜度要靠深類別對抗。\n\n"
    "## 詞彙表\n\n"
    "| 詞彙 | 定義 | 避免混用 |\n"
    "|------|------|----------|\n"
    "| 深類別 (deep class) | 介面窄、功能多的類別 | 大類別 |\n"
    "| classitis | 類別切太多太淺 | 過度工程 |\n"
    "| 複雜度 | 讓系統難改的東西 | 行數 |\n"
)


def test_glossary_terms_linked_and_definitions_embedded():
    html = convert(GLOSSARY_MD, timestamp="t")
    para = re.search(r"<p>.*?</p>", html, re.DOTALL).group(0)
    assert para.count(">深類別</button>") == 2  # every occurrence is linked
    assert 'class="gloss"' in para
    assert "/* glossary popover */" in html  # the click-to-toggle runtime
    assert "介面窄、功能多的類別" in html and "避免混用" in html


def test_glossary_table_and_headings_not_linkified():
    html = convert(GLOSSARY_MD, timestamp="t")
    tbody = re.search(r"<tbody>.*?</tbody>", html, re.DOTALL).group(0)
    assert "<td>深類別 (deep class)</td>" in tbody
    assert 'class="gloss"' not in tbody


def test_no_glossary_means_no_runtime_or_markup():
    html = convert(SAMPLE_MD, timestamp="t")
    assert 'class="gloss"' not in html
    assert "/* glossary popover */" not in html


def test_glossary_popover_caret_tracks_the_term():
    # Speech-bubble look: the caret must keep pointing at the term even after the card
    # is clamped to the viewport edge, so its offset is a JS-set CSS var, not fixed.
    html = convert(GLOSSARY_MD, timestamp="t")
    assert ".gloss-pop::before" in html
    assert "--caret-left" in html
    assert "setProperty('--caret-left'" in html
    assert ".gloss-pop.below::before" in html and ".gloss-pop.above::before" in html


def test_term_key_strips_translation_in_both_styles():
    # The key matched against the prose is the bare term, with any translation in the
    # other script removed — whether the cell pairs them parenthetically or with a
    # plain space, and whichever script leads.
    assert _term_key("深類別 (deep class)") == "深類別"  # parenthetical, half-width
    assert _term_key("複雜度（Complexity）") == "複雜度"  # parenthetical, full-width
    assert _term_key("複雜度 Complexity") == "複雜度"  # space-separated, CJK lead
    assert _term_key("把錯誤定義掉 Define errors out of existence") == "把錯誤定義掉"
    assert _term_key("Classitis 類別炎") == "Classitis"  # space-separated, Latin lead
    assert _term_key("classitis") == "classitis"  # no translation
    assert _term_key("紅旗") == "紅旗"
    assert _term_key("戰術 vs 戰略") == "戰術 vs 戰略"  # same-script: never truncated


# A space-separated bilingual term cell ('複雜度 Complexity', 'Classitis 類別炎') is at
# least as common as the parenthetical form; both must yield the bare term so the prose
# still links. Regression: the space-separated form previously kept the translation in
# the key and so matched nothing in the prose (zero dashed terms).
GLOSSARY_BILINGUAL_MD = (
    "# T\n\n## 概述\n\n"
    "深模組打敗複雜度;Classitis 是它的病態版。\n\n"
    "## 詞彙表\n\n"
    "| 詞彙 | 定義 | 避免混用 |\n"
    "|------|------|----------|\n"
    "| 複雜度 Complexity | 難改的東西 | 行數 |\n"
    "| 深模組 Deep module | 介面窄功能多 | 大類別 |\n"
    "| Classitis 類別炎 | 類別切太多 | 模組化 |\n"
)


def test_glossary_space_separated_bilingual_term_is_linked():
    html = convert(GLOSSARY_BILINGUAL_MD, timestamp="t")
    para = re.search(r"<p>.*?</p>", html, re.DOTALL).group(0)
    assert re.search(r'class="gloss"[^>]*>複雜度</button>', para)  # CJK term, Latin gloss
    assert re.search(r'class="gloss"[^>]*>深模組</button>', para)
    assert re.search(r'class="gloss"[^>]*>Classitis</button>', para)  # Latin term, CJK gloss


def test_glossary_term_matches_prose_case_insensitively():
    # A headword cased one way in the 詞彙表 (a Title-cased "Harness") must still tag its
    # lowercase prose occurrences ("harness"); otherwise the dashed underline silently
    # never shows — the common slip when prose uses a loanword in lower case.
    md = (
        "# T\n\n## 概述\n\n"
        "這個 harness 很小但可讀。\n\n"
        "## 詞彙表\n\n"
        "| 詞彙 | 定義 | 避免混用 |\n"
        "|------|------|----------|\n"
        "| Harness | 可重用的大腦 | 引擎 |\n"
    )
    html = convert(md, timestamp="t")
    para = re.search(r"<p>.*?</p>", html, re.DOTALL).group(0)
    assert re.search(r'class="gloss"[^>]*>harness</button>', para)  # prose casing kept


def test_glossary_term_absent_from_prose_warns(capsys):
    # Fail loud: a headword that never appears in the prose underlines nothing, which
    # used to fail silently. The converter must warn so the author fixes the cell.
    md = (
        "# T\n\n## 概述\n\n"
        "內文完全沒提到那個詞。\n\n"
        "## 詞彙表\n\n"
        "| 詞彙 | 定義 | 避免混用 |\n"
        "|------|------|----------|\n"
        "| Nonexistent | 不會出現 | — |\n"
    )
    convert(md, timestamp="t")
    err = capsys.readouterr().err
    assert "Nonexistent" in err
    assert "warning" in err.lower()


def test_zoom_decorate_survives_a_failed_diagram_render():
    # One diagram with a syntax error makes mermaid.run() reject; decorate must still
    # run (via .catch) so the zoom control is not stripped from the diagrams that DID
    # render — and the failure is logged, not swallowed.
    html = convert(MERMAID_MD, timestamp="t")
    assert "mermaid.run({ nodes: nodes }).catch(" in html
    assert "console.warn" in html
    assert ".then(decorate)" in html


# Inline markup in a glossary cell (**bold**, `code`) must reach the popover as real
# HTML, not literal asterisks — the rendered 詞彙表 table converts it, so the
# click-to-view card must agree for the very same cell. Regression: the popover used to
# embed the raw cell text, so a definition with **bold** showed its asterisks.
GLOSSARY_MARKUP_MD = (
    "# T\n\n## 概述\n\n"
    "介面是關鍵。\n\n"
    "## 詞彙表\n\n"
    "| 詞彙 | 定義 | 避免混用 |\n"
    "|------|------|----------|\n"
    "| 介面 | 腦中**必須裝載**的全部 | `函式簽名` |\n"
)


def test_glossary_popover_renders_inline_markdown_not_literal_asterisks():
    html = convert(GLOSSARY_MARKUP_MD, timestamp="t")
    assert "**必須裝載**" not in html  # never the raw markdown, anywhere
    # Assert the POPOVER DATA itself (not just the table) carries the bold as HTML.
    # The closing </ is escaped to <\/ inside the JSON so a stray </script> can't end
    # the tag early; the browser reads <\/strong> back as </strong> when injecting.
    data = re.search(r"var G = (\[.*?\]);", html, re.DOTALL).group(1)
    assert "<strong>必須裝載<\\/strong>" in data
    assert "<code>函式簽名<\\/code>" in data  # avoid-cell `code` rendered too
