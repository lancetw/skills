#!/usr/bin/env python3
"""Convert a Markdown file into a styled, readable HTML page.

Turns any Markdown document into a "好讀版" (easy-to-read) HTML file with an
editorial, book-like look (書卷感) tuned for long-form Traditional Chinese
reading. The Markdown is the single source of truth; this script is a pure,
deterministic convert-and-wrap layer over it.

Usage:
    python3 md_to_html.py input.md            # -> input.html
    python3 md_to_html.py input.md out.html   # explicit output path

Design notes:
- We reuse the `markdown` library with the `tables`, `fenced_code`, and `toc`
  extensions. `toc` both injects
  heading anchors and gives us `md.toc` for the sidebar.
- The "好讀版" look is editorial: a warm-paper palette, a 朱紅 (seal-red) accent,
  and a sepia dark mode. The Chinese font is reader-selectable via a top-left
  switcher — 明體 (Noto Serif TC) / 楷體 (Iansui, default) / 文楷 (LXGW WenKai TC) /
  楷體＋注音 (Bpmf Iansui) / 黑體 (Noto Sans TC) / 圓體 (Huninn) — each loaded lazily
  from Google Fonts, with system fonts in each stack as the offline fallback.
- Reading aids are page-level chrome injected on every doc: a sticky table of
  contents that highlights the section you are reading (scroll-spy), a thin
  reading-progress bar, and CSS-counter section numbers. Clicking a TOC link
  locks the highlight to the target so the smooth scroll does not flicker it
  through the intervening sections.
- ASCII flow charts only stay aligned in a monospace, non-wrapping block, so
  `pre` uses `white-space: pre` + horizontal scroll rather than wrapping.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import markdown
except ImportError:  # pragma: no cover - environment guard
    sys.stderr.write(
        "需要 markdown 套件才能產生 HTML 好讀版。請用 uv 取得相依：\n"
        "    uv sync                                      # 在此技能目錄安裝相依\n"
        "或直接用 uv 執行（會自動帶入相依）：\n"
        "    uv run python scripts/md_to_html.py <input.md>\n"
    )
    raise SystemExit(1)


# Editorial "書卷感" typography tuned for Traditional Chinese: a warm-paper
# palette, a reader-selectable Chinese web font (top-left switcher), a 朱紅 accent,
# a sepia dark theme, a scroll-spy TOC, a reading-progress bar, CSS-counter section
# numbers, and a print layout. Kept as a module constant so the Python logic stays
# a thin convert-and-wrap layer. The active font is applied through the --font-stack
# CSS variable, which the data-font attribute (set by the pre-paint script) swaps;
# each stack ends in system fonts so an offline page still shows the right style.
CSS = """
:root {
  /* Tell the browser the page is light so native UA scrollbars, form controls
     and the font <select> render in the matching scheme. The dark theme is
     toggle-driven (data-theme), so without this the native scrollbar stays light
     on the dark page. */
  color-scheme: light;
  --bg: #f7f3ea;
  --surface: #fffdf8;
  --text: #2e2a23;
  --heading: #1d1a13;
  --muted: #6f6657;
  --faint: #9a917e;
  --border: #e4ddcc;
  --border-strong: #d2c8b1;
  --code-bg: #f1ebdc;
  --code-border: #e2dac6;
  --link: #b5402f;
  --accent: #b5402f;
  --accent-strong: #97331f;
  --accent-soft: #f3e7e1;
  --shadow: 0 1px 2px rgba(60,45,20,.06), 0 2px 8px rgba(60,45,20,.05);
  --font-stack: "Iansui", "Klee One", "Kaiti TC", "DFKai-SB", "BiauKai", Georgia, serif;
}
/* Dark palette is attribute-driven (not a media query) so the toggle button can
   flip it. The pre-paint script in <head> sets data-theme from the saved choice
   or, on first visit, the system's prefers-color-scheme. It is a warm "sepia
   night" rather than a cool grey, to keep the book feel after dark. */
:root[data-theme="dark"] {
  /* Flip the UA scheme with the theme so the page, code-block and TOC scrollbars
     (and the font <select>) are drawn dark instead of a jarring light grey. */
  color-scheme: dark;
  --bg: #1b1712;
  --surface: #221d17;
  --text: #e7dfd0;
  --heading: #f5efe1;
  --muted: #a89c86;
  --faint: #7c715e;
  --border: #322b21;
  --border-strong: #43392c;
  --code-bg: #221d17;
  --code-border: #322b21;
  --link: #e69478;
  --accent: #e69478;
  --accent-strong: #efae97;
  --accent-soft: rgba(230,148,120,.14);
  --shadow: 0 1px 2px rgba(0,0,0,.5);
}
/* Reader-selectable Chinese font (data-font on <html>, set by the pre-paint
   script). Applied via --font-stack; trailing system fonts are the offline
   fallback when the chosen Google web font has not loaded. */
:root[data-font="serif"]  { --font-stack: Georgia, "Noto Serif TC", "Source Han Serif TC", "Songti TC", "Songti SC", serif; }
:root[data-font="kai"]    { --font-stack: "Iansui", "Klee One", "Kaiti TC", "DFKai-SB", "BiauKai", Georgia, serif; }
:root[data-font="wenkai"] { --font-stack: "LXGW WenKai TC", "Kaiti TC", "DFKai-SB", "BiauKai", Georgia, serif; }
:root[data-font="bpmf"]   { --font-stack: "Bpmf Iansui", "Iansui", "Kaiti TC", "DFKai-SB", Georgia, serif; }
:root[data-font="sans"]   { --font-stack: -apple-system, BlinkMacSystemFont, "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", "Helvetica Neue", Arial, sans-serif; }
:root[data-font="round"]  { --font-stack: "Huninn", "Varela Round", "PingFang TC", "Microsoft JhengHei", sans-serif; }
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-stack);
  font-size: 18px;
  line-height: 1.9;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
  /* Long Latin words / URLs / inline code wrap instead of overflowing. CJK wraps
     by character as usual; this only kicks in for otherwise-unbreakable runs. */
  overflow-wrap: break-word;
}

/* Reading-progress bar pinned to the very top, filled as you scroll. */
#reading-progress {
  position: fixed; top: 0; left: 0; height: 3px; width: 0;
  background: var(--accent); z-index: 40; transition: width .08s linear;
}

.layout {
  display: flex;
  gap: 4rem;
  max-width: 1060px;
  margin: 0 auto;
  padding: 4.5rem 2rem 7rem;
}
main {
  flex: 1 1 auto;
  min-width: 0;
  max-width: 42rem;
  counter-reset: section;
}
.meta { display: block; color: var(--faint); font-size: .82rem; letter-spacing: .03em; margin: 0 0 2rem; }

/* text-wrap: balance evens multi-line headings (no orphan last word). */
h1, h2, h3, h4 { color: var(--heading); font-weight: 700; text-wrap: balance; overflow-wrap: break-word; }
h1 {
  font-size: clamp(2.1rem, 4.5vw, 2.6rem);
  line-height: 1.25;
  letter-spacing: .01em;
  margin: 0 0 1.6rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-strong);
}
h2 {
  font-size: 1.55rem;
  line-height: 1.35;
  margin: 3.2rem 0 1.15rem;
  padding-bottom: .45rem;
  border-bottom: 1px solid var(--border);
  counter-reset: subsection;  /* restart H3 numbering (1.1, 1.2) under each section */
}
/* Section numbers come from a CSS counter, not the Markdown, so the source stays
   clean and numbers renumber themselves if sections move. */
h2::before {
  counter-increment: section;
  content: counter(section) "\\2009\\2009";
  color: var(--accent);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
/* When the author already numbers the headings ('## 1. 介紹', '## 一、背景'),
   convert() flags the document and we switch this counter off so the number is
   not shown twice. */
body.manual-numbering h2::before { content: none; counter-increment: none; }
h3 { font-size: 1.22rem; line-height: 1.45; margin: 2.2rem 0 .6rem; }
/* Subsections read as part of the section's number ('1.1', '1.2'), again from a
   CSS counter so the Markdown source stays clean. Stops at H3. */
h3::before {
  counter-increment: subsection;
  content: counter(section) "." counter(subsection) "\\2009\\2009";
  color: var(--accent);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
body.manual-numbering h3::before { content: none; counter-increment: none; }
/* Anchored headings land just below the scroll-spy activation line on click. */
h1[id], h2[id], h3[id] { scroll-margin-top: 6.5rem; }
/* text-wrap: pretty improves the body rag and avoids single-word last lines. */
/* justify: flush both edges — reads well for predominantly-CJK prose; the last
   line stays naturally aligned, so no stretched orphan line. */
p { margin: 1.1rem 0; text-wrap: pretty; text-align: justify; }
a { color: var(--link); text-decoration: none; border-bottom: 1px solid transparent; }
a:hover { border-bottom-color: currentColor; }
strong { color: var(--heading); font-weight: 700; }

ul, ol { padding-left: 1.5rem; }
li { margin: .45rem 0; text-wrap: pretty; }
li::marker { color: var(--accent); }

hr { border: none; border-top: 1px solid var(--border-strong); margin: 3rem 0; }

/* Blockquote -> a quietly elegant pull-quote on warm paper. */
blockquote {
  margin: 1.8rem 0;
  padding: .4rem 0 .4rem 1.4rem;
  border-left: 3px solid var(--accent);
  color: var(--muted);
  font-size: 1.08rem;
}
/* A multi-line metadata blockquote (source / link / author on separate `>` lines)
   is folded by Markdown into one paragraph whose soft newlines would collapse to
   spaces, running the lines together. pre-line renders those preserved source
   newlines as real breaks while still wrapping long lines normally. */
blockquote p { margin: .35rem 0; white-space: pre-line; }

/* "★ Insight" callout the model writes — rendered as a styled 重點 box (the
   "★ 重點" label comes from CSS, so the source block stays clean). */
.insight {
  margin: 1.8rem 0;
  padding: .9rem 1.2rem;
  background: var(--accent-soft);
  border: 1px solid var(--border-strong);
  border-left: 3px solid var(--accent);
  border-radius: 0 10px 10px 0;
}
.insight::before {
  content: "★ 重點";
  display: block;
  margin-bottom: .5rem;
  color: var(--accent);
  font-weight: 700;
  font-size: .85rem;
  letter-spacing: .05em;
}
.insight > :first-child { margin-top: 0; }
.insight > :last-child { margin-bottom: 0; }
.insight ul, .insight ol { margin: .3rem 0; padding-left: 1.3rem; }

/* "自我檢核" retrieval-practice question: the model writes it as a
   <details class="self-check"> disclosure — a prompt the reader answers from
   memory, then expands to check. Retrieval beats re-reading for retention, so a
   learning doc earns its name by asking, not just telling. Styled to match the
   editorial look (not a bare native triangle); on GitHub/GitLab the .md degrades
   to a plain native disclosure. */
details.self-check {
  margin: 1.8rem 0;
  padding: 0 1.2rem;
  background: var(--surface);
  border: 1px solid var(--border-strong);
  border-left: 3px solid var(--accent);
  border-radius: 0 10px 10px 0;
}
details.self-check > summary {
  cursor: pointer;
  padding: .75rem 0;
  color: var(--accent);
  font-weight: 700;
  list-style: none;  /* replace the native disclosure triangle with our own marker */
  /* A quick/double click to toggle must not select the question text. */
  -webkit-user-select: none;
  user-select: none;
}
details.self-check > summary::-webkit-details-marker { display: none; }
/* A status badge before the question: a ringed "?" while unanswered, a ringed "✓"
   once revealed. The ring is drawn in CSS (currentColor = the seal-red accent) so it
   matches the editorial palette instead of pulling in a clashing colour-emoji glyph. */
details.self-check > summary::before {
  content: "?";
  display: inline-block;
  width: 1.3em;
  height: 1.3em;
  line-height: 1.3em;          /* == height, so the glyph sits centred in the ring */
  margin-right: .45rem;
  border: 1.5px solid currentColor;
  border-radius: 50%;
  font-size: .8em;
  font-weight: 700;
  text-align: center;
  vertical-align: 0.1em;       /* nudge up: CJK optical centre sits above the x-height
                                  midline that `middle` would use, so middle reads low */
}
details.self-check[open] > summary::before { content: "✓"; }   /* revealed: same ring, checked */
details.self-check[open] > summary { margin-bottom: .4rem; border-bottom: 1px solid var(--border); }
details.self-check > :last-child { margin-bottom: .9rem; }
/* The "> 先自己想，再展開對照。" nudge is lifted out of the hidden body into the
   always-visible <summary> (see _lift_self_check_hint), because its whole job is to
   be read BEFORE expanding. Render it as a quiet sub-line under the question, and
   drop it once the card is open, when "think first, then expand" is moot. */
details.self-check > summary .self-check-hint {
  display: block;
  margin-top: .4rem;
  font-weight: 400;
  font-style: italic;
  font-size: .9rem;
  color: var(--muted);
}
details.self-check[open] > summary .self-check-hint { display: none; }

/* Code/diagrams keep a monospace "machine voice" against the serif prose. */
code {
  background: var(--code-bg);
  border: 1px solid var(--code-border);
  padding: .1em .38em;
  border-radius: 5px;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: .82em;
}
/* ASCII flow charts must stay aligned: monospace, no wrapping, scroll if wide. */
pre {
  background: var(--code-bg);
  border: 1px solid var(--code-border);
  padding: 1rem 1.2rem;
  border-radius: 8px;
  overflow-x: auto;
  white-space: pre;
  line-height: 1.55;
  box-shadow: var(--shadow);
}
pre code { background: none; border: none; padding: 0; font-size: .84rem; }
/* Mermaid diagrams: a centered figure. Before the script runs (or offline) this
   shows the raw diagram source in a monospace card, which is still readable. */
pre.mermaid {
  text-align: center;
  background: var(--code-bg);
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}
/* Reserve a clear top band so the corner zoom button sits well clear of the chart. */
pre.mermaid[data-processed] {
  position: relative;
  white-space: normal; background: transparent; border: none; box-shadow: none;
  padding: 3.5rem 0 .5rem;
}
pre.mermaid svg { max-width: 100%; height: auto; display: block; margin: 0 auto; }
/* Small icon-only "open enlarged" button, top-right, in the reserved band. */
.mermaid-zoom {
  position: absolute; top: .5rem; right: .5rem;
  display: inline-flex; align-items: center; justify-content: center;
  width: 1.9rem; height: 1.9rem; padding: 0; cursor: pointer;
  color: var(--muted); background: var(--surface);
  border: 1px solid var(--border-strong); border-radius: 7px; box-shadow: var(--shadow);
  transition: color .15s ease, border-color .15s ease, transform .15s ease;
}
.mermaid-zoom:hover { color: var(--accent); border-color: var(--accent); transform: translateY(-1px); }
.mermaid-zoom:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.mermaid-zoom svg { width: 1.1rem; height: 1.1rem; display: block; }

/* In-page zoom & pan viewer opened by the zoom button. Hidden until .open.
   Lets a dense diagram be read at full size without leaving the page. */
.mermaid-lightbox { position: fixed; inset: 0; z-index: 60; display: none; background: var(--bg); }
.mermaid-lightbox.open { display: block; }
.mermaid-lightbox .stage {
  position: absolute; inset: 0; overflow: hidden; cursor: grab; touch-action: none;
}
.mermaid-lightbox .stage.grabbing { cursor: grabbing; }
.mermaid-lightbox .content {
  position: absolute; top: 0; left: 0; transform-origin: 0 0; will-change: transform;
}
.mermaid-lightbox .content svg { display: block; max-width: none; height: auto; }
.mermaid-lightbox .lb-controls { position: absolute; top: 1rem; right: 1rem; z-index: 1; display: flex; gap: .4rem; }
.mermaid-lightbox .lb-controls button {
  width: 2.3rem; height: 2.3rem; padding: 0;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 1.15rem; line-height: 1; cursor: pointer;
  color: var(--text); background: var(--surface);
  border: 1px solid var(--border-strong); border-radius: 8px; box-shadow: var(--shadow);
  transition: color .15s ease, border-color .15s ease;
}
.mermaid-lightbox .lb-controls button:hover { color: var(--accent); border-color: var(--accent); }
.mermaid-lightbox .lb-hint {
  position: absolute; bottom: 1rem; left: 50%; transform: translateX(-50%);
  font-size: .8rem; color: var(--muted); background: var(--surface);
  padding: .35rem .8rem; border-radius: 999px; border: 1px solid var(--border);
  box-shadow: var(--shadow); pointer-events: none;
}

/* Clean hairline tables: horizontal rules only, firm header, row hover. */
/* min-width (not width) lets the table fill normally but GROW past the container
   when its columns need room, instead of squashing CJK into narrow columns. */
table { border-collapse: collapse; min-width: 100%; margin: 1.7rem 0; font-size: .95rem; }
/* Headers stay on one line; every cell keeps a readable minimum width so text is
   not crammed. When the columns' widths exceed the page the wrapper scrolls. */
thead th { border-bottom: 2px solid var(--border-strong); color: var(--muted); font-weight: 700; white-space: nowrap; }
th, td { border: none; border-bottom: 1px solid var(--border); padding: .6rem .9rem; text-align: left; min-width: 7em; vertical-align: top; }
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover td { background: var(--accent-soft); }
/* A wide table scrolls horizontally inside its own box (the converter wraps each
   <table>), so it never overflows the page or squashes the prose column. */
.table-wrap { overflow-x: auto; max-width: 100%; margin: 1.7rem 0; }
.table-wrap > table { margin: 0; }
/* One unified scrollbar for EVERY scroll area — the page, code blocks, the TOC
   and wide tables — so the doc never mixes a warm custom bar with the grey UA
   overlay. (macOS otherwise auto-hides the overlay, so a clipped wide table even
   shows no hint it scrolls.) A styled ::-webkit-scrollbar opts every box into a
   persistent, always-visible classic bar on Chrome/Safari; color-scheme (set on
   :root) keeps Firefox's native bar in the matching palette. We intentionally
   avoid the standard scrollbar-width/scrollbar-color props: on Chrome 121+ they
   suppress ::-webkit-scrollbar and revert to the invisible overlay. */
::-webkit-scrollbar { width: 11px; height: 11px; }
/* Transparent track: the bar sits on different backgrounds (page --bg, code block
   --code-bg, table --surface), so a fixed track colour clashes with two of the
   three. Transparent lets it blend into whatever is behind it — the harmonious
   choice — while the always-styled thumb still signals that the area scrolls. */
::-webkit-scrollbar-track { background: transparent; }
/* Thumb in the layout's own border tone, slimmed to a soft pill by a transparent
   padding-box border so it has breathing room on each side instead of a heavy slab. */
::-webkit-scrollbar-thumb {
  background-color: var(--border-strong);
  border-radius: 6px;
  border: 3px solid transparent;
  background-clip: padding-box;
}
::-webkit-scrollbar-thumb:hover { background-color: var(--muted); }
::-webkit-scrollbar-corner { background: transparent; }
/* The TOC is a tall, narrow column where the default --border-strong thumb on a
   transparent track is almost invisible ("沒有捲軸"). Give the TOC its own darker
   thumb + a faint track so the scrollable area reads as scrollable. */
nav.toc::-webkit-scrollbar-track { background: var(--accent-soft); border-radius: 6px; }
nav.toc::-webkit-scrollbar-thumb { background-color: var(--muted); }
nav.toc::-webkit-scrollbar-thumb:hover { background-color: var(--faint); }

/* Menu (theme toggle + font switcher) as the header of the TOC sidebar — so on a
   centred wide layout it sits WITH the TOC column instead of orphaned in the far
   top-left corner. Aligns to the TOC title's left padding. */
.toc-controls {
  display: flex; align-items: center; gap: .55rem;
  margin: 0 0 1.2rem; padding-left: .85rem;
}
/* Fallback cluster for a doc with NO TOC (nothing to host the menu): a small fixed
   chip in the top-left. Solid background so scrolling content passes behind it
   cleanly rather than bleeding through the gaps. */
.controls {
  position: fixed; top: 1.1rem; left: 1.2rem; z-index: 30;
  display: flex; align-items: center; gap: .55rem;
  padding: .4rem .55rem; background: var(--bg); border-radius: 9px;
}
/* Font switcher — a compact native <select> so the OS draws the caret and it
   stays accessible; the choice is applied through the --font-stack variable. */
.font-select {
  font-family: inherit; font-size: .82rem; line-height: 1;
  padding: .32rem .5rem; cursor: pointer;
  color: var(--text); background: var(--surface);
  border: 1px solid var(--border-strong); border-radius: 7px;
}
.font-select:hover { border-color: var(--accent); }
.font-select:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
/* Theme toggle — minimal monochrome glyph, no box. The glyph shows the mode you
   would switch TO: a moon while light, a sun while dark. */
.theme-toggle {
  display: inline-flex; align-items: center; justify-content: center;
  width: 1.9rem; height: 1.9rem; padding: 0;
  font-size: 1.15rem; line-height: 1; cursor: pointer;
  color: var(--faint); background: none; border: none; box-shadow: none;
  transition: color .15s ease, transform .15s ease;
}
.theme-toggle:hover { color: var(--accent); transform: scale(1.08); }
.theme-toggle:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 4px; }
.theme-toggle .theme-toggle__icon::before { content: "\\263E\\FE0E"; }            /* ☾ while light */
:root[data-theme="dark"] .theme-toggle .theme-toggle__icon::before { content: "\\2600\\FE0E"; }  /* ☀ while dark */

/* 目錄 opener — a standalone FIXED, icon-only button (a hamburger), only shown
   ≤880px (the sidebar TOC is a drawer there). Pinned top-left with a solid
   background so scrolling content passes cleanly behind it; z-index below the
   backdrop (44) so the open drawer covers it. A fixed square so the icon centres. */
.toc-toggle {
  display: none;
  position: fixed; top: 1.1rem; left: 1.2rem; z-index: 43;
  align-items: center; justify-content: center;
  width: 2.2rem; height: 2.2rem; padding: 0; cursor: pointer;
  color: var(--text); background: var(--surface);
  border: 1px solid var(--border-strong); border-radius: 8px;
}
.toc-toggle:hover { border-color: var(--accent); color: var(--accent); }
.toc-toggle:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
/* Hamburger drawn in CSS, not a text glyph — a glyph inherits the reading font and
   each of the 6 fonts centres it differently inside the line box (it looked too high).
   The span is the middle bar; ::before/::after are the top/bottom bars at ±.34rem, so
   the three are symmetric about the centred middle bar — perfectly centred any font. */
.toc-toggle__bars, .toc-toggle__bars::before, .toc-toggle__bars::after {
  content: ""; display: block;
  width: 1.15rem; height: 2px; border-radius: 2px; background: currentColor;
}
.toc-toggle__bars { position: relative; }
.toc-toggle__bars::before { position: absolute; top: -.34rem; }
.toc-toggle__bars::after  { position: absolute; bottom: -.34rem; }
/* Dimmed backdrop behind the open mobile TOC drawer; inert (no pointer events)
   until body.toc-open makes it visible, so it never blocks taps when closed. */
.toc-backdrop {
  position: fixed; inset: 0; z-index: 44;
  background: rgba(0,0,0,.4);
  opacity: 0; visibility: hidden;
  transition: opacity .22s ease, visibility .22s ease;
}
body.toc-open .toc-backdrop { opacity: 1; visibility: visible; }

/* Floating, scroll-spy table of contents — set in serif to match the page. */
nav.toc {
  flex: 0 0 13.5rem;
  align-self: flex-start;
  position: sticky;
  top: 4.5rem;
  max-height: calc(100vh - 6rem);
  /* Only ever scroll vertically. Setting overflow-y alone would make the spec
     compute overflow-x to `auto` (the "one axis non-visible promotes the other"
     rule), and the forced-visible ::-webkit-scrollbar then paints a stray
     horizontal bar for a sub-pixel overflow (e.g. a long Latin word like a name in
     a CJK heading). Pin overflow-x to hidden so long entries wrap instead. */
  overflow-x: hidden;
  overflow-y: auto;
  font-size: .9rem;
}
nav.toc .toc-title {
  font-weight: 700; color: var(--faint);
  font-size: .8rem; letter-spacing: .14em;
  margin-bottom: .9rem; padding-left: 1rem;
}
nav.toc ul { list-style: none; padding-left: 0; margin: 0; }
nav.toc > div > ul { counter-reset: tnum; border-left: 1px solid var(--border-strong); }
nav.toc ul ul { padding-left: .8rem; border-left: none; }
nav.toc li { margin: 0; }
nav.toc > div > ul > li { counter-reset: tsub; }  /* restart H3 TOC numbering per section */
nav.toc a {
  position: relative; display: block; color: var(--muted);
  padding: .33rem 0 .33rem 1rem; transition: color .12s ease;
}
nav.toc > div > ul > li > a::before {
  counter-increment: tnum; content: counter(tnum) "\\2002";
  color: var(--faint); font-variant-numeric: tabular-nums;
}
/* Nested H3 entries mirror the heading numbering: '1.1', '1.2'. */
nav.toc > div > ul > li > ul > li > a::before {
  counter-increment: tsub; content: counter(tnum) "." counter(tsub) "\\2002";
  color: var(--faint); font-variant-numeric: tabular-nums;
}
/* Same opt-out for the sidebar's own counters (both levels), so a manually
   numbered doc is not double-numbered in the TOC either. */
body.manual-numbering nav.toc > div > ul > li > a::before { content: none; counter-increment: none; }
body.manual-numbering nav.toc > div > ul > li > ul > li > a::before { content: none; counter-increment: none; }
nav.toc a:hover { color: var(--text); }
nav.toc a.active { color: var(--accent); font-weight: 700; }
nav.toc a.active::after {
  content: ""; position: absolute; left: -1px; top: .4rem; bottom: .4rem;
  width: 2px; background: var(--accent);
}

@media (max-width: 880px) {
  /* Top padding clears the fixed 目錄 opener (the only floating control on phones);
     its bottom edge is ~3rem, so start content below it. */
  .layout { padding: 3.7rem 1.4rem 4rem; gap: 0; }
  main { max-width: none; }
  .toc-toggle { display: inline-flex; }
  /* The sidebar TOC becomes a left slide-in drawer, opened by the 目錄 button and
     closed by the backdrop, a TOC tap, or Esc (toc-drawer runtime). The menu rides
     at the drawer's top (.toc-controls), so theme/font are reachable once it opens. */
  nav.toc {
    position: fixed; top: 0; left: 0;
    /* Definite height = viewport, so a TOC taller than the screen scrolls INSIDE the
       drawer (with a vertical scrollbar) instead of growing the drawer past the
       bottom edge. `top:0;bottom:0` did not constrain the height here; 100dvh does,
       and dvh tracks the mobile browser's collapsing toolbar. */
    height: 100dvh;
    width: min(80vw, 17rem);
    max-height: none; margin: 0;
    padding: 1.5rem 1.2rem 2rem;
    background: var(--surface);
    border-right: 1px solid var(--border-strong);
    box-shadow: var(--shadow);
    z-index: 46;
    overflow-y: auto;
    transform: translateX(-100%);
    transition: transform .22s ease;
  }
  body.toc-open nav.toc { transform: translateX(0); }
}
/* Glossary term: a dashed underline marks a word defined in the 詞彙表; clicking it
   pops the definition (and any 避免混用 note) in a floating card. The control inherits
   the surrounding font/colour and only adds the dashed rule, so prose stays calm. */
.gloss {
  font: inherit;
  color: inherit;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  vertical-align: baseline;
  border-bottom: 1px dashed var(--accent);
}
.gloss:hover { color: var(--accent); }
.gloss:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 2px; }
.gloss-pop {
  position: absolute;
  z-index: 50;
  display: none;
  max-width: 300px;
  padding: .85rem 1.1rem;
  background: var(--surface);
  border: 1.5px solid var(--accent);      /* full seal-red outline: clearly a distinct card */
  border-radius: 10px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, .22), 0 3px 10px rgba(0, 0, 0, .14);  /* clear elevation above the prose */
  font-size: .9rem;
  line-height: 1.7;
  font-weight: 400;
  color: var(--text);
}
.gloss-pop.show { display: block; }
.gloss-pop .gloss-pop-term { font-weight: 700; color: var(--accent); margin-bottom: .35rem; }
.gloss-pop .gloss-pop-avoid { margin-top: .55rem; font-size: .82rem; color: var(--muted); }
/* Caret: a rotated square whose two accent sides form an even 1.5px arrow. It sits
   BEHIND the card (z-index:-1), so the card's opaque background hides its lower half
   and any corner artifacts — only a clean "^" tab pokes above the top border, its
   legs meeting the border exactly at the card edge. The integer left edge (from JS,
   no fractional translate) keeps the rotated square on whole pixels so its sides stay
   crisp. Centred on --caret-left so it tracks the term; .below / .above edges it. */
.gloss-pop::before {
  content: "";
  position: absolute;
  z-index: -1;
  left: var(--caret-left, 16px);
  width: 14px;
  height: 14px;
  background: var(--surface);
  transform: rotate(45deg);
}
.gloss-pop.below::before { top: -9px; border-top: 1.5px solid var(--accent); border-left: 1.5px solid var(--accent); }
.gloss-pop.above::before { bottom: -9px; border-bottom: 1.5px solid var(--accent); border-right: 1.5px solid var(--accent); }

@media print {
  /* Force a light, paper-toned palette on paper regardless of the on-screen
     theme, so a reader who toggled to dark does not print dark blocks. */
  :root, :root[data-theme="dark"] {
    --bg: #fff; --surface: #fff; --text: #1a1a1a; --heading: #000; --muted: #444;
    --border: #ccc; --border-strong: #999; --code-bg: #f4f1ea; --code-border: #ddd;
    --link: #000; --accent: #000; --accent-soft: #f4f1ea;
  }
  nav.toc, .controls, .toc-toggle, .toc-backdrop, #reading-progress, .mermaid-zoom, .mermaid-lightbox { display: none; }
  body { background: #fff; font-size: 12pt; }
  main { max-width: none; }
  pre { box-shadow: none; }
  a { color: #000; border-bottom: none; }
  /* Reveal every self-check answer on paper: a collapsed <details> would print
     with the answers hidden, making the printed reference useless. */
  details.self-check:not([open]) > * { display: block; }
  /* On paper the dashed glossary underline is noise and popovers cannot open. */
  .gloss { border-bottom: none; }
  .gloss-pop { display: none !important; }
}
"""


# Runs in <head> BEFORE the body paints, so a dark-mode reader never sees a white
# flash (FOUC): it resolves the theme from the saved choice, else the system
# preference, and writes it onto <html data-theme>. It also defines the global
# toggleTheme() the button calls, and keeps following the system while the reader
# has not made an explicit choice. Kept tiny and dependency-free.
THEME_INIT = """
<script>
(function () {
  var KEY = 'markdown-to-html-theme';
  var root = document.documentElement;
  function systemDark() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  function saved() {
    try { var v = localStorage.getItem(KEY); return (v === 'dark' || v === 'light') ? v : null; }
    catch (e) { return null; }
  }
  root.dataset.theme = saved() || (systemDark() ? 'dark' : 'light');
  window.toggleTheme = function () {
    var next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem(KEY, next); } catch (e) {}
    window.dispatchEvent(new CustomEvent('themechange', { detail: next }));
  };
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
      if (saved()) return;
      root.dataset.theme = e.matches ? 'dark' : 'light';
      window.dispatchEvent(new CustomEvent('themechange', { detail: root.dataset.theme }));
    });
  }
})();
</script>
"""

# Fixed-position control. The icon is drawn purely in CSS from data-theme, so the
# markup is static; aria-label/title make it usable by keyboard and screen reader.
THEME_TOGGLE = (
    '<button class="theme-toggle" type="button" onclick="toggleTheme()"'
    ' aria-label="切換深色與淺色主題" title="切換深色／淺色主題">'
    '<span class="theme-toggle__icon" aria-hidden="true"></span></button>'
)

# Theme toggle + the Chinese-font switcher. The <select> values match the FONT_INIT
# registry keys; setFont() applies and persists each choice. 楷體 (Iansui) is the
# default, marked selected for the no-JS / pre-script moment; FONT_INIT then syncs
# the control to the saved choice on DOMContentLoaded.
MENU_ITEMS = (
    THEME_TOGGLE
    + '<select class="font-select" onchange="setFont(this.value)" aria-label="選擇中文字型">'
    '<option value="serif">思源宋體</option>'
    '<option value="kai" selected>芫荽</option>'
    '<option value="wenkai">霞鶩文楷</option>'
    '<option value="bpmf">芫荽注音</option>'
    '<option value="sans">思源黑體</option>'
    '<option value="round">粉圓</option>'
    "</select>"
)
# Where the menu lives:
#   - TOC_CONTROLS: the normal case — the menu rides at the top of the left TOC
#     sidebar (desktop) / inside the drawer (mobile), so it never floats over content.
#   - CONTROLS: fallback for a doc with NO TOC (nothing to host the menu), a small
#     fixed cluster in the top-left corner. Solid background so scrolling content
#     passes cleanly behind it instead of bleeding through.
TOC_CONTROLS = '<div class="toc-controls">' + MENU_ITEMS + "</div>"
CONTROLS = '<div class="controls">' + MENU_ITEMS + "</div>"

# 目錄 drawer opener — a standalone fixed, icon-only button shown only ≤880px (the
# sidebar TOC is hidden there). It must sit OUTSIDE the drawer to open it, so it is
# separate from TOC_CONTROLS. Solid background, so scrolling content does not bleed
# through it. aria-label gives its accessible name (no visible text); aria-controls
# points at the nav's id so it is announced as the nav's opener.
TOC_TOGGLE = (
    '<button class="toc-toggle" type="button" onclick="toggleToc()"'
    ' aria-label="開啟目錄" aria-expanded="false" aria-controls="toc-nav">'
    '<span class="toc-toggle__bars" aria-hidden="true"></span></button>'
)

# Opens/closes the mobile TOC drawer by toggling body.toc-open. The 目錄 button and
# the backdrop both call the global toggleToc(); tapping a TOC entry or pressing Esc
# closes it. Only emitted when a TOC exists, so toggleToc is defined exactly when
# something can call it. aria-expanded is kept in sync for screen readers.
TOC_DRAWER_RUNTIME = """
<script>
(function () {
  var body = document.body;
  var btn = document.querySelector('.toc-toggle');
  function set(open) {
    body.classList.toggle('toc-open', open);
    if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  window.toggleToc = function () { set(!body.classList.contains('toc-open')); };
  var nav = document.querySelector('nav.toc');
  if (nav) nav.addEventListener('click', function (e) {
    if (e.target.closest('a')) set(false);   // tapped an entry -> navigate and close
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') set(false);
  });
})();
</script>
"""


# Google Fonts preconnect — the actual font stylesheet is injected lazily by
# FONT_INIT, so only the chosen font loads (not all six).
FONT_PRECONNECT = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
)

# Reader-selectable Chinese font. Runs in <head> BEFORE paint (like THEME_INIT):
# restores the saved choice from localStorage, writes it to <html data-font> so the
# right --font-stack applies from the first paint, and injects ONLY that font's
# Google Fonts stylesheet (lazy — the others load on first switch). setFont() is the
# global the <select> calls; it persists the choice and emits 'fontchange' so the
# diagram runtime can re-render in the new font. display=swap + the system fonts in
# each --font-stack mean an offline page still shows text (in a system font).
FONT_INIT = """
<script>
(function () {
  var KEY = 'markdown-to-html-font';
  var DEFAULT = 'kai';
  var CSS = {
    serif: 'https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;700&display=swap',
    kai: 'https://fonts.googleapis.com/css2?family=Iansui&display=swap',
    wenkai: 'https://fonts.googleapis.com/css2?family=LXGW+WenKai+TC&display=swap',
    bpmf: 'https://fonts.googleapis.com/css2?family=Bpmf+Iansui&display=swap',
    sans: 'https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap',
    round: 'https://fonts.googleapis.com/css2?family=Huninn&display=swap'
  };
  var root = document.documentElement;
  function saved() {
    try { var v = localStorage.getItem(KEY); return CSS[v] ? v : null; } catch (e) { return null; }
  }
  function ensure(key) {
    if (!CSS[key]) return;
    if (document.querySelector('link[data-font-css="' + key + '"]')) return;
    var l = document.createElement('link');
    l.rel = 'stylesheet'; l.href = CSS[key];
    l.setAttribute('data-font-css', key);
    document.head.appendChild(l);
  }
  var cur = saved() || DEFAULT;
  root.dataset.font = cur;
  ensure(cur);
  window.setFont = function (key) {
    if (!CSS[key]) return;
    root.dataset.font = key;
    try { localStorage.setItem(KEY, key); } catch (e) {}
    ensure(key);
    window.dispatchEvent(new CustomEvent('fontchange', { detail: key }));
  };
  window.addEventListener('DOMContentLoaded', function () {
    var sel = document.querySelector('.font-select');
    if (sel) sel.value = root.dataset.font;
  });
})();
</script>
"""


# Page-level reading aids, injected on EVERY document (the TOC highlight and the
# progress bar exist whether or not a doc has a diagram). Deliberately contains
# no Mermaid reference, so a diagram-free doc never pulls in that library.
#
# Scroll-spy uses a real-position activation rule: the active section is the last
# heading (in document order) whose top edge has crossed an activation line near
# the top of the viewport. That line is tied to the headings' own scroll-margin-top
# (6.5rem), so a heading that is clicked and smooth-scrolled to its landing spot is
# exactly the one detected as active — the highlight lands on the clicked section
# instead of drifting to a neighbour (the previous even-share trigger model used
# synthetic positions that disagreed with where clicks actually land). When scrolled
# to the very bottom the last heading is forced active (a short final section may
# never reach the line). Clicking a TOC link locks the highlight to that target and
# releases it only when the scroll has actually arrived there (the position rule
# agrees), so it never flashes through the sections the scroll passes on the way.
SCROLLSPY_RUNTIME = """
<script>
(function () {
  var bar = document.createElement('div');
  bar.id = 'reading-progress';
  document.body.appendChild(bar);

  var links = Array.prototype.slice.call(document.querySelectorAll('nav.toc a[href^="#"]'));
  var map = {};
  links.forEach(function (a) { map[decodeURIComponent(a.getAttribute('href').slice(1))] = a; });
  var heads = Array.prototype.slice
    .call(document.querySelectorAll('main h2[id], main h3[id]'))
    .filter(function (h) { return map[h.id]; });

  var current = null;
  function setActive(id) {
    if (current === id) return;
    current = id;
    links.forEach(function (a) { a.classList.toggle('active', map[id] === a); });
  }

  // Clicking a TOC link smooth-scrolls the heading to its landing spot, which can
  // take many frames. Lock the highlight to that target and release it only when
  // the scroll has ACTUALLY arrived (the position rule below agrees) — not on a
  // timer or a stray wheel/scrollend event, which fire mid-flight and would flash
  // the highlight through every section the scroll passes ('亂跳') and then snap
  // back. scrollend and a safety timeout also release the lock, so a click that
  // cannot reach the line (e.g. a short final section) never stays stuck.
  var lockTarget = null, lockTimer = null;
  function releaseLock() {
    lockTarget = null;
    if (lockTimer) { clearTimeout(lockTimer); lockTimer = null; }
  }
  links.forEach(function (a) {
    a.addEventListener('click', function () {
      var id = decodeURIComponent(a.getAttribute('href').slice(1));
      if (!map[id]) return;
      lockTarget = id;
      setActive(id);
      if (lockTimer) clearTimeout(lockTimer);
      lockTimer = setTimeout(function () { releaseLock(); update(); }, 2500);
    });
  });
  // A finished scroll is a safe point to resume position-based highlighting:
  // motion has stopped, so update() reads a resting position, never an
  // intermediate one the scroll was passing through.
  window.addEventListener('scrollend', function () {
    if (lockTarget !== null) { releaseLock(); update(); }
  });

  function update() {
    var doc = document.documentElement;
    var scrollTop = window.scrollY || doc.scrollTop;
    var maxScroll = doc.scrollHeight - doc.clientHeight;
    bar.style.width = (maxScroll > 0 ? (scrollTop / maxScroll) * 100 : 0) + '%';
    var n = heads.length;
    if (!n) return;

    // The section the current scroll position points at (real-position rule): the
    // last heading whose top edge has crossed the activation line. The line is read
    // from the headings' actual scroll-margin-top (6.5rem) plus a little headroom,
    // so a heading clicked-and-scrolled to its landing spot — which lands at exactly
    // that margin — counts as crossed, at any root font size.
    var id;
    if (maxScroll <= 0) {
      id = heads[0].id;
    } else if (scrollTop >= maxScroll - 1) {
      // At the very bottom, the last heading wins even if a short final section
      // could not scroll its heading up to the line.
      id = heads[n - 1].id;
    } else {
      var LINE = (parseFloat(getComputedStyle(heads[0]).scrollMarginTop) || 104) + 8;
      id = heads[0].id;
      for (var i = 0; i < n; i++) {
        if (heads[i].getBoundingClientRect().top <= LINE) id = heads[i].id;
      }
    }

    // While locked to a clicked target, keep showing it until the scroll arrives
    // (the position rule agrees) — never the intermediate sections in between.
    if (lockTarget !== null) {
      if (id === lockTarget) releaseLock();
      else { setActive(lockTarget); return; }
    }
    setActive(id);
  }

  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update, { passive: true });
  window.addEventListener('load', update);
  update();
})();
</script>
"""


# The `markdown` library turns ```mermaid into <pre><code class="language-mermaid">,
# but mermaid.js renders elements with class="mermaid". Rewriting the wrapper to
# <pre class="mermaid"> both activates rendering and leaves a readable monospace
# source fallback when the script can't load (offline / JS disabled).
_MERMAID_BLOCK = re.compile(
    r'<pre><code class="language-mermaid">(.*?)</code></pre>',
    re.DOTALL,
)

# Loaded only when a document actually contains a diagram. The diagram text is
# rendered locally in the browser — only the library is fetched, the content is
# never sent anywhere. Pinned to a major version for reproducibility.
#
# The themeVariables palette mirrors the page's warm-paper / sepia-dark CSS for
# each mode (nodes, borders, arrows, text) and uses the same serif font, so a
# chart reads as part of the document and keeps contrast either way. Because
# Mermaid replaces each block with an SVG it cannot recolour in place, we keep the
# original source and fully re-render on every 'themechange' the toggle emits.
MERMAID_RUNTIME = """
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';

const FONT = 'Georgia, "Noto Serif TC", "Source Han Serif TC", "Songti TC", "Songti SC", serif';
const PALETTE = {
  light: {
    background: '#f7f3ea',
    primaryColor: '#fbf6ec', mainBkg: '#fbf6ec',
    primaryBorderColor: '#b5402f', nodeBorder: '#b5402f',
    primaryTextColor: '#2e2a23', nodeTextColor: '#2e2a23', textColor: '#2e2a23',
    secondaryColor: '#f1ebdc', tertiaryColor: '#f7f3ea',
    clusterBkg: '#f1ebdc', clusterBorder: '#d2c8b1',
    lineColor: '#9c8d72', edgeLabelBackground: '#f3eddf',
    titleColor: '#1d1a13', fontFamily: FONT,
  },
  dark: {
    background: '#1b1712',
    primaryColor: '#2a231b', mainBkg: '#2a231b',
    primaryBorderColor: '#e69478', nodeBorder: '#e69478',
    primaryTextColor: '#e7dfd0', nodeTextColor: '#e7dfd0', textColor: '#e7dfd0',
    secondaryColor: '#271f18', tertiaryColor: '#2f261c',
    clusterBkg: '#271f18', clusterBorder: '#43392c',
    lineColor: '#a89880', edgeLabelBackground: '#241e17',
    titleColor: '#f5efe1', fontFamily: FONT,
  },
};

const nodes = Array.from(document.querySelectorAll('pre.mermaid'));
nodes.forEach(function (el) { el.dataset.src = el.textContent; });

// Open one diagram in an in-page zoom & pan viewer. Built once and reused; each
// open clones the freshly-rendered SVG so its colours match the current theme.
// Wheel / trackpad-pinch zooms toward the cursor, drag pans, buttons + Esc round
// it out — so a dense diagram can be read at full size without leaving the page.
var lb = null;
var lbState = { scale: 1, tx: 0, ty: 0, min: 0.1, max: 12 };
function buildLightbox() {
  var box = document.createElement('div');
  box.className = 'mermaid-lightbox';
  box.setAttribute('role', 'dialog');
  box.setAttribute('aria-modal', 'true');
  box.setAttribute('aria-label', '圖表放大檢視');
  box.innerHTML =
      '<div class="lb-controls">'
    +   '<button type="button" data-act="out" aria-label="縮小" title="縮小">\\u2212</button>'
    +   '<button type="button" data-act="reset" aria-label="重設縮放" title="重設檢視">\\u2922</button>'
    +   '<button type="button" data-act="in" aria-label="放大" title="放大">\\uFF0B</button>'
    +   '<button type="button" data-act="close" aria-label="關閉" title="關閉 (Esc)">\\u2715</button>'
    + '</div>'
    + '<div class="stage"><div class="content"></div></div>'
    + '<div class="lb-hint">滾輪／觸控板縮放 · 拖曳平移 · 雙擊放大 · Esc 關閉</div>';
  document.body.appendChild(box);
  var stage = box.querySelector('.stage');
  var content = box.querySelector('.content');
  function apply() {
    content.style.transform =
      'translate(' + lbState.tx + 'px,' + lbState.ty + 'px) scale(' + lbState.scale + ')';
  }
  // Zoom keeping the point under (clientX, clientY) fixed on screen.
  function zoomAt(factor, clientX, clientY) {
    var r = stage.getBoundingClientRect();
    var mx = clientX - r.left, my = clientY - r.top;
    var ns = Math.min(lbState.max, Math.max(lbState.min, lbState.scale * factor));
    var k = ns / lbState.scale;
    lbState.tx = mx - (mx - lbState.tx) * k;
    lbState.ty = my - (my - lbState.ty) * k;
    lbState.scale = ns;
    apply();
  }
  // Fit the whole diagram with a small margin, then centre it.
  box._fit = function () {
    var r = stage.getBoundingClientRect();
    var w = content._natW, h = content._natH;
    if (!w || !h) return;
    var fit = Math.min(r.width / w, r.height / h) * 0.92;
    lbState.scale = fit;
    lbState.min = Math.min(0.1, fit * 0.5);
    lbState.max = Math.max(12, fit * 12);
    lbState.tx = (r.width - w * fit) / 2;
    lbState.ty = (r.height - h * fit) / 2;
    apply();
  };
  box._show = function (svg) {
    var clone = svg.cloneNode(true);
    clone.removeAttribute('style');
    var w = 0, h = 0;
    if (svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width) {
      w = svg.viewBox.baseVal.width; h = svg.viewBox.baseVal.height;
    } else {
      var bb = svg.getBoundingClientRect(); w = bb.width; h = bb.height;
    }
    clone.setAttribute('width', w); clone.setAttribute('height', h);
    content._natW = w; content._natH = h;
    content.innerHTML = ''; content.appendChild(clone);
    box.classList.add('open');
    box._fit();
  };
  stage.addEventListener('wheel', function (e) {
    e.preventDefault();
    zoomAt(e.deltaY < 0 ? 1.15 : 1 / 1.15, e.clientX, e.clientY);
  }, { passive: false });
  // ponytail: pointer-event drag covers mouse + single-finger touch; trackpad
  // pinch arrives as a ctrl+wheel event so the wheel handler already gets it.
  // Two-finger touch pinch is the only gap — add a pointer-pair handler if asked.
  var dragging = false, px = 0, py = 0;
  stage.addEventListener('pointerdown', function (e) {
    dragging = true; px = e.clientX; py = e.clientY;
    stage.classList.add('grabbing');
    try { stage.setPointerCapture(e.pointerId); } catch (err) {}
  });
  stage.addEventListener('pointermove', function (e) {
    if (!dragging) return;
    lbState.tx += e.clientX - px; lbState.ty += e.clientY - py;
    px = e.clientX; py = e.clientY; apply();
  });
  function endDrag() { dragging = false; stage.classList.remove('grabbing'); }
  stage.addEventListener('pointerup', endDrag);
  stage.addEventListener('pointercancel', endDrag);
  stage.addEventListener('dblclick', function (e) { zoomAt(1.6, e.clientX, e.clientY); });
  box.querySelector('.lb-controls').addEventListener('click', function (e) {
    var btn = e.target.closest('button');
    if (!btn) return;
    var r = stage.getBoundingClientRect();
    var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    var act = btn.dataset.act;
    if (act === 'in') zoomAt(1.3, cx, cy);
    else if (act === 'out') zoomAt(1 / 1.3, cx, cy);
    else if (act === 'reset') box._fit();
    else if (act === 'close') box.classList.remove('open');
  });
  return box;
}
function openEnlarged(svg) {
  if (!lb) lb = buildLightbox();
  lb._show(svg);
}
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape' && lb && lb.classList.contains('open')) lb.classList.remove('open');
});
window.addEventListener('resize', function () {
  if (lb && lb.classList.contains('open')) lb._fit();
});

// Re-render replaces each <pre> with a fresh SVG, so the zoom button is wiped
// and must be re-attached after every run (initial load and theme change).
function decorate() {
  nodes.forEach(function (el) {
    if (el.querySelector('.mermaid-zoom')) return;
    var svg = el.querySelector('svg');
    if (!svg) return;
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'mermaid-zoom';
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"'
      + ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
      + '<path d="M15 3h6v6"/><path d="M9 21H3v-6"/><path d="M21 3l-7 7"/><path d="M3 21l7-7"/></svg>';
    btn.setAttribute('aria-label', '放大檢視此圖（可縮放、平移）');
    btn.setAttribute('title', '放大檢視（可縮放、平移）');
    btn.addEventListener('click', function () { openEnlarged(svg); });
    el.appendChild(btn);
  });
}

function render() {
  var dark = document.documentElement.dataset.theme === 'dark';
  var vars = dark ? PALETTE.dark : PALETTE.light;
  // Follow the reader's chosen Chinese font so the diagram matches the prose.
  vars.fontFamily = getComputedStyle(document.body).fontFamily || FONT;
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: 'base',
    themeVariables: vars,
  });
  nodes.forEach(function (el) { el.textContent = el.dataset.src; el.removeAttribute('data-processed'); });
  // One diagram with a syntax error makes mermaid.run() reject; without a catch the
  // .then never fires and decorate is skipped, stripping the zoom control from every
  // diagram (not just the broken one). Log the failure, then always (re-)decorate.
  mermaid.run({ nodes: nodes }).catch(function (e) {
    console.warn('[mermaid] some diagrams failed to render:', e);
  }).then(decorate);
}

render();
window.addEventListener('themechange', render);
window.addEventListener('fontchange', render);
</script>
"""


def _activate_mermaid(html_body: str) -> tuple[str, bool]:
    """Rewrite mermaid code blocks to mermaid elements; report if any were found."""
    new_body, count = _MERMAID_BLOCK.subn(r'<pre class="mermaid">\1</pre>', html_body)
    return new_body, count > 0


# The `markdown` tables extension emits a bare <table>; wrapping each one lets a
# wide table scroll horizontally inside its own box instead of overflowing.
_TABLE_BLOCK = re.compile(r"<table>.*?</table>", re.DOTALL)


def _wrap_tables(html_body: str) -> str:
    """Wrap each table in a horizontally scrollable container."""
    return _TABLE_BLOCK.sub(r'<div class="table-wrap">\g<0></div>', html_body)


# A self-check opens with a "> 先自己想，再展開對照。" nudge written as a Markdown
# blockquote right after the <summary>. Inside a <details> that blockquote is hidden
# until the card is expanded — but the nudge's whole job is to be read BEFORE
# expanding ("think first, then expand to compare"). Lift that leading hint into the
# always-visible <summary> as a quiet sub-line; CSS then drops it once the card opens.
_SELF_CHECK_HINT = re.compile(
    r'(<details class="self-check">\s*<summary>)(.*?)(</summary>)\s*'
    r"<blockquote>\s*<p>(.*?)</p>\s*</blockquote>",
    re.DOTALL,
)


def _lift_self_check_hint(html_body: str) -> str:
    """Move a self-check's leading blockquote hint into its summary so it shows
    while the card is collapsed (its purpose is to be read before expanding)."""
    return _SELF_CHECK_HINT.sub(r'\1\2<span class="self-check-hint">\4</span>\3', html_body)


# --- Glossary term tooltips ----------------------------------------------------
# A doc may end with a 詞彙表 (term | definition | 避免混用) table. Where each term
# appears in the prose, turn it into a dashed-underlined control that pops its
# definition in a floating card — so a reader meets an unfamiliar term and checks it
# in place instead of scrolling to the appendix. The table is detected by its "詞彙"
# header, so a doc without a glossary pays nothing: no markup, no runtime injected.
_GLOSSARY_HEADER = re.compile(r"^\s*\|\s*詞彙\s*\|")

# CJK Unified Ideographs (incl. Ext-A) — used to tell a term apart from a
# translation written in the other script.
_CJK_CHAR = re.compile(r"[㐀-鿿]")


def _term_key(cell: str) -> str:
    """Derive the bare term to match in the prose from a glossary's first cell.

    A term cell often pairs the term with a translation in the OTHER script, in
    either of two common styles:
      - parenthetical:   '複雜度（Complexity）', '深類別 (deep class)'
      - space-separated: '複雜度 Complexity', 'Classitis 類別炎'
    The prose only ever uses the term itself, never the translation, so strip the
    translation off: first drop a parenthetical tail, then — if a single space
    splits a CJK run from a Latin run — keep only the leading (term) run. A title
    that is a single script throughout (e.g. 'classitis', '戰術 vs 戰略') is left
    whole, so this never truncates a genuine multi-word term.
    """
    title = re.split(r"\s*[（(]", cell.strip("`").strip(), maxsplit=1)[0].strip()
    m = re.match(r"^(\S+)\s+(\S.*)$", title)
    if m:
        head, tail = m.group(1), m.group(2)
        if bool(_CJK_CHAR.search(head)) != bool(_CJK_CHAR.search(tail)):
            return head  # term and translation are in different scripts
    return title


def _md_inline(text: str) -> str:
    """Render a one-line glossary cell's Markdown to inline HTML (no <p> wrapper).

    A glossary cell can carry inline markup (**bold**, *italic*, `code`). The rendered
    詞彙表 table converts it, and the popover injects its definition as innerHTML — so
    the popover must convert it too, otherwise the asterisks show literally and the
    floating card disagrees with the table for the very same cell. markdown wraps its
    output in <p>…</p>; a table cell is a single line, so strip that one wrapper.
    """
    html = markdown.markdown(text.strip())
    m = re.fullmatch(r"<p>(.*)</p>", html, flags=re.DOTALL)
    return m.group(1) if m else html


def _extract_glossary(md_text: str) -> list[dict]:
    """Parse the 詞彙表 table from the raw Markdown into term records.

    Each record carries: key (the bare term matched in the prose, with any
    parenthetical English stripped), title (the full first-cell text, shown as the
    card heading), def (the definition), and avoid (the 避免混用 note, may be empty).
    """
    lines = md_text.splitlines()
    for i, line in enumerate(lines):
        if not _GLOSSARY_HEADER.match(line):
            continue
        terms: list[dict] = []
        for row in lines[i + 2 :]:  # skip the header and its |---| separator
            if not row.lstrip().startswith("|"):
                break
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            if len(cells) < 2 or not cells[0]:
                continue
            key = _term_key(cells[0])
            if not key:
                continue
            # title/def/avoid are rendered to inline HTML so the popover matches the
            # 詞彙表 table (both convert **bold** / `code`); key stays the raw term.
            terms.append(
                {
                    "key": key,
                    "title": _md_inline(cells[0].strip("`").strip()),
                    "def": _md_inline(cells[1]),
                    "avoid": _md_inline(cells[2]) if len(cells) > 2 else "",
                }
            )
        return terms
    return []


_TAG = re.compile(r"<[^>]+>")
# Inside these elements the text is not prose — never linkify there. The glossary
# table itself is a <table>, so it is skipped automatically and never self-links.
_GLOSS_SKIP = {
    "pre",
    "code",
    "script",
    "style",
    "table",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "summary",
    "a",
    "button",
}


def _linkify_glossary(html_body: str, terms: list[dict]) -> str:
    """Wrap every prose occurrence of a glossary term in a clickable .gloss control."""
    if not terms:
        return html_body
    idx_of: dict[str, int] = {}
    for i, t in enumerate(terms):
        idx_of.setdefault(t["key"], i)
    keys = sorted(idx_of, key=len, reverse=True)  # longest first: 戰術龍捲風 before 戰術型
    # Case-insensitive lookup so a headword cased one way in the 詞彙表 (a Title-cased
    # "Harness") still tags its lowercase prose occurrences ("harness") — the common
    # slip when prose uses a loanword in lower case. The button keeps the prose casing
    # via m.group(0); only the term->index lookup folds case.
    idx_ci: dict[str, int] = {}
    for term_key, i in idx_of.items():
        idx_ci.setdefault(term_key.lower(), i)

    def _pat(k: str) -> str:
        e = re.escape(k)
        # ASCII terms (classitis, kluge) need boundaries so they don't match inside a
        # larger Latin word; CJK terms break anywhere, so they need none.
        if re.fullmatch(r"[A-Za-z0-9]+", k):
            return r"(?<![A-Za-z0-9])" + e + r"(?![A-Za-z0-9])"
        return e

    term_re = re.compile("|".join(_pat(k) for k in keys), re.IGNORECASE)
    matched: set[int] = set()

    def _wrap(text: str) -> str:
        def _repl(m: re.Match[str]) -> str:
            word = m.group(0)
            i = idx_of.get(word)
            if i is None:
                i = idx_ci[word.lower()]
            matched.add(i)
            return f'<button type="button" class="gloss" data-gloss="{i}">{word}</button>'

        return term_re.sub(_repl, text)

    out: list[str] = []
    pos = 0
    skip = 0
    for m in _TAG.finditer(html_body):
        seg = html_body[pos : m.start()]
        out.append(_wrap(seg) if skip == 0 and seg else seg)
        tag = m.group(0)
        out.append(tag)
        name = re.match(r"</?([a-zA-Z0-9]+)", tag)
        nm = name.group(1).lower() if name else ""
        if nm in _GLOSS_SKIP and not tag.endswith("/>"):
            skip = max(0, skip - 1) if tag.startswith("</") else skip + 1
        pos = m.end()
    tail = html_body[pos:]
    out.append(_wrap(tail) if skip == 0 and tail else tail)
    result = "".join(out)
    # Fail loud: a headword that never appears in the prose underlines nothing, which
    # otherwise fails silently (a wrong script or casing in the 詞彙表 cell). Warn so the
    # author fixes the cell instead of shipping an inert glossary entry.
    unmatched = sorted(term_key for term_key, i in idx_of.items() if i not in matched)
    if unmatched:
        print(
            "warning: glossary term(s) never matched the prose (no underline): "
            + ", ".join(unmatched),
            file=sys.stderr,
        )
    return result


def _glossary_runtime(terms: list[dict]) -> str:
    """Embed the glossary data + the click-to-toggle popover script (empty if none).

    title/def/avoid are already inline HTML (rendered from the cell Markdown by
    _md_inline), so they are embedded as-is and the popover injects them as innerHTML —
    matching how the 詞彙表 table renders the same cells. Re-escaping here would show
    literal <strong> tags; the trust model is the same as the document body, which is
    author Markdown rendered to HTML. The '</' -> '<\\/' guard still stops a stray
    '</script>' inside the data from closing the tag early.
    """
    if not terms:
        return ""

    data = json.dumps(
        [{"t": t["title"], "d": t["def"], "a": t["avoid"]} for t in terms],
        ensure_ascii=False,
    ).replace("</", "<\\/")
    return GLOSSARY_RUNTIME.replace("__GLOSSARY_DATA__", data)


GLOSSARY_RUNTIME = """<script>
/* glossary popover */
(function () {
  var G = __GLOSSARY_DATA__;
  var pop = null;
  function ensure() {
    if (pop) return pop;
    pop = document.createElement('div');
    pop.className = 'gloss-pop';
    pop.setAttribute('role', 'dialog');
    document.body.appendChild(pop);
    return pop;
  }
  function close() { if (pop) { pop.classList.remove('show'); pop._anchor = null; } }
  function open(btn) {
    var g = G[+btn.getAttribute('data-gloss')];
    if (!g) return;
    var p = ensure();
    var html = '<div class="gloss-pop-term">' + g.t + '</div>'
             + '<div class="gloss-pop-def">' + g.d + '</div>';
    if (g.a) html += '<div class="gloss-pop-avoid"><b>避免混用：</b>' + g.a + '</div>';
    p.innerHTML = html;
    p.classList.add('show');
    p._anchor = btn;
    var r = btn.getBoundingClientRect();
    var doc = document.documentElement;
    var gap = 10;
    var pw = p.offsetWidth, ph = p.offsetHeight;
    // horizontal: line the card up under the term, then clamp to the viewport
    var left = r.left;
    var maxLeft = doc.clientWidth - pw - 12;
    if (left > maxLeft) left = maxLeft;
    if (left < 12) left = 12;
    // vertical: prefer below the term; flip above only if it would overflow the
    // viewport AND there is more room above
    var below = !(r.bottom + gap + ph > doc.clientHeight && r.top - gap - ph > 0);
    var top = below ? (r.bottom + gap) : (r.top - gap - ph);
    p.classList.toggle('below', below);
    p.classList.toggle('above', !below);
    p.style.left = (left + window.scrollX) + 'px';
    p.style.top = (top + window.scrollY) + 'px';
    // caret: integer LEFT edge so the 14px square lands on whole pixels (a fractional
    // translate blurred its edges and let the card border show through). Centre it on
    // the term (minus half the square), clamped clear of the rounded corners.
    var caret = Math.round((r.left + r.width / 2) - left - 7);
    caret = Math.max(8, Math.min(pw - 22, caret));
    p.style.setProperty('--caret-left', caret + 'px');
  }
  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('.gloss');
    if (btn) {
      e.preventDefault();
      e.stopPropagation();
      if (pop && pop.classList.contains('show') && pop._anchor === btn) close();
      else open(btn);
      return;
    }
    if (pop && pop.classList.contains('show') && !pop.contains(e.target)) close();
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
})();
</script>"""


# The model writes educational "★ Insight ─────" callouts (box-drawing rules)
# into the document; detect them and re-emit as a styled <div> callout. Runs
# on the RAW Markdown (before conversion) and uses md_in_html so the inner points
# are still parsed as real Markdown inside the box. Only matches U+2500 (─) runs,
# never '-', so it cannot clobber a real '---' rule or a table separator.
#
# The rule lines may be wrapped in backticks (`★ Insight ───` / `───`): the
# Explanatory output-style and memory templates present them that way, so the
# model writes them so in practice. The optional `` ` `` anchors absorb that form;
# without them the backticks would survive as inline <code> and no callout builds.
_INSIGHT_BLOCK = re.compile(
    r"^`?★[ \t]*Insight[ \t]*─{3,}[^\n]*\n"
    r"(.*?)\n"
    r"`?[ \t]*─{3,}[ \t]*`?[ \t]*$",
    re.MULTILINE | re.DOTALL,
)

# A third form: the whole block wrapped in a Markdown blockquote (`> ★ Insight ─…`,
# every line `> `-prefixed, trailing double spaces for hard breaks). The bible-*
# skills mandate this form in their saved documents, so it is what their converter
# input actually contains. Matched as a unit here, then the quote markers are
# stripped so the block falls through to _INSIGHT_BLOCK like the plain form.
_INSIGHT_BLOCKQUOTE = re.compile(
    r"^>[ \t]*`?★[ \t]*Insight[ \t]*─{3,}[^\n]*\n"
    r"(?:>[^\n]*\n)*?"
    r">[ \t]*`?[ \t]*─{3,}[ \t]*`?[ \t]*$",
    re.MULTILINE,
)


def _wrap_insights(md_text: str) -> str:
    """Rewrite ★ Insight box-drawing blocks into a styled callout div."""

    def unquote(match: re.Match) -> str:
        # Strip one `>` and at most one following space per line, preserving
        # the rest (including the hard-break trailing spaces).
        return re.sub(r"^>[ \t]?", "", match.group(0), flags=re.MULTILINE)

    md_text = _INSIGHT_BLOCKQUOTE.sub(unquote, md_text)

    def repl(match: re.Match) -> str:
        inner = match.group(1).strip("\n")
        return '<div class="insight" markdown="1">\n\n' + inner + "\n\n</div>"

    return _INSIGHT_BLOCK.sub(repl, md_text)


# A leading "section number" on a heading: Arabic or Chinese (incl. full-width)
# numerals, parenthesised, or 第N章/節 — but ONLY when a separator follows. The
# separator is what tells a real section number ('1. 介紹', '一、背景') apart from a
# heading that merely starts with a number ('2024 年度回顧', '5 個重點'), which must
# be left alone. Chinese numerals likewise need a separator so words like '十分'
# or '一起' are not mistaken for '十' / '一'.
_CJK_NUM = "一二三四五六七八九十百千零兩壹貳參叁肆伍陸柒捌玖拾佰仟"
_SECTION_NUMBER_PREFIX = re.compile(
    "^(?:"
    "第\\s*[0-9０-９" + _CJK_NUM + "]+\\s*[章節节部篇講讲課课回卷集話话]"  # 第N章/節...
    "|[(（]\\s*[0-9０-９" + _CJK_NUM + "]+\\s*[)）]"  # (1) （一）
    "|[0-9０-９]+[.．、)）:：]"  # 1.  1、  1)
    "|[" + _CJK_NUM + "]+[.．、)）:：]"  # 一、  二.
    ")"
)


def _has_manual_section_numbers(md_text: str) -> bool:
    """True when the H2 OR the H3 headings are mostly numbered by the author.

    Sections (H2) and subsections (H3) both get their numbers from CSS counters; if
    the author numbered the headings themselves the page would show each number
    twice. The whole document opts out of auto-numbering when EITHER level is mostly
    hand-numbered, so neither '## 1. 介紹' nor '### 1.1 範圍' double-numbers. Code
    fences are skipped, and a separator must follow the number so leading CONTENT
    numbers ('2024 年度回顧', '5 個重點') do not count.
    """
    in_fence = False
    counts = {2: [0, 0], 3: [0, 0]}  # heading level -> [total, numbered]
    for raw in md_text.splitlines():
        if raw.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"(#{2,3})[ \t]+(\S.*)", raw)  # H2 / H3 ('####' fails the space)
        if not m:
            continue
        level = len(m.group(1))
        counts[level][0] += 1
        if _SECTION_NUMBER_PREFIX.match(m.group(2)):
            counts[level][1] += 1
    return any(total > 0 and numbered * 2 >= total for total, numbered in counts.values())


def convert(md_text: str, title: str = "文件", timestamp: str | None = None) -> str:
    """Convert Markdown text to a full, self-contained HTML document string.

    `timestamp` is injectable so tests stay deterministic; production calls let
    it default to the current local time.
    """
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "md_in_html"],
        extension_configs={"toc": {"toc_depth": "2-3"}},
    )
    body = md.convert(_wrap_insights(md_text))
    body, has_mermaid = _activate_mermaid(body)
    body = _wrap_tables(body)
    body = _lift_self_check_hint(body)
    glossary = _extract_glossary(md_text)
    body = _linkify_glossary(body, glossary)
    toc = getattr(md, "toc", "") or ""
    stamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M")
    # If the author already numbered the headings, flag the doc so the CSS section
    # counter (heading + TOC) is switched off and the numbers are not shown twice.
    body_class = ' class="manual-numbering"' if _has_manual_section_numbers(md_text) else ""

    has_toc = "<a" in toc
    # Normal case: the menu rides at the top of the TOC (TOC_CONTROLS), the mobile
    # drawer opener + backdrop + runtime are emitted, and no floating cluster is
    # needed. A doc with NO TOC has nowhere to host the menu, so it falls back to the
    # small fixed CONTROLS cluster and gets none of the drawer machinery.
    if has_toc:
        toc_block = (
            f'<nav class="toc" id="toc-nav">{TOC_CONTROLS}'
            f'<div class="toc-title">目錄</div>{toc}</nav>'
        )
        controls = ""
        toc_toggle = TOC_TOGGLE
        toc_backdrop = '<div class="toc-backdrop" onclick="toggleToc()" aria-hidden="true"></div>'
        toc_drawer_runtime = TOC_DRAWER_RUNTIME
    else:
        toc_block = ""
        controls = CONTROLS
        toc_toggle = ""
        toc_backdrop = ""
        toc_drawer_runtime = ""
    mermaid_runtime = MERMAID_RUNTIME if has_mermaid else ""
    glossary_runtime = _glossary_runtime(glossary)

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{FONT_PRECONNECT}
<title>{title}</title>
{FONT_INIT}{THEME_INIT}<style>{CSS}</style>
</head>
<body{body_class}>
{controls}{toc_toggle}
{toc_backdrop}
<div class="layout">
{toc_block}
<main>
<div class="meta">產生時間：{stamp}</div>
{body}
</main>
</div>
{SCROLLSPY_RUNTIME}{toc_drawer_runtime}{mermaid_runtime}{glossary_runtime}
</body>
</html>
"""


def _derive_title(md_text: str, fallback: str) -> str:
    """Use the document's first H1 as the page <title>, else the file stem."""
    for line in md_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def main(argv: list[str]) -> int:
    if not argv:
        sys.stderr.write("用法：python3 md_to_html.py <input.md> [output.html]\n")
        return 2

    src = Path(argv[0])
    if not src.is_file():
        sys.stderr.write(f"找不到檔案：{src}\n")
        return 1

    dst = Path(argv[1]) if len(argv) > 1 else src.with_suffix(".html")
    md_text = src.read_text(encoding="utf-8")
    title = _derive_title(md_text, src.stem)
    dst.write_text(convert(md_text, title=title), encoding="utf-8")

    # Report ABSOLUTE paths for both outputs so the user can open them regardless
    # of the cwd the script ran from (a relative argument would otherwise print a
    # path that only resolves from the original directory). The file:// line is
    # click-to-open in most terminals.
    md_path = src.resolve()
    html_path = dst.resolve()
    print("已產生 HTML 好讀版，完整路徑如下：")
    print(f"  Markdown 原稿：{md_path}")
    print(f"  HTML 好讀版　：{html_path}")
    print(f"  瀏覽器開啟　　：file://{html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
