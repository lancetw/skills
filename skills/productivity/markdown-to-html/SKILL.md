---
name: markdown-to-html
description: Convert any Markdown file into a styled, readable "好讀版" HTML page tuned for long-form Traditional Chinese reading — warm-paper editorial design, a 6-font Chinese font switcher, a light/dark theme toggle, a scroll-spy table of contents, a reading-progress bar, auto-numbered sections, rendered Mermaid diagrams, ★ Insight callouts, and a print stylesheet. Self-contained single-file output; web fonts and Mermaid load from a CDN at view time and fall back gracefully offline. Use when the user wants to turn a .md into a nicely formatted / 好讀版 / readable / printable HTML version to read or share — triggers include "把這份 markdown 變好看", "markdown 轉 HTML", "好讀版 HTML", "convert markdown to readable html", "make this .md readable".
license: MIT
---

# Markdown → 好讀版 HTML

Turn **any** Markdown file into a single, self-contained HTML page with an
editorial "書卷感" layout tuned for comfortable long-form Traditional Chinese
reading. The Markdown stays the single source of truth — the HTML is a pure,
deterministic transform of it, so the two never drift.

This is a **format-only** tool: it does not write or change content, it only
renders whatever Markdown you give it.

## Quick Start

Given a Markdown file, run the bundled converter with `uv` (it resolves the
`markdown` dependency from this skill's `pyproject.toml`):

```bash
# Sync once so the `markdown` dependency is installed (surfaces any
# dependency/network problem up front instead of mid-conversion).
uv sync --project <skill-dir>

# Default: writes a sibling .html with the same name
uv run --project <skill-dir> python <skill-dir>/scripts/md_to_html.py input.md

# Or specify an explicit output path
uv run --project <skill-dir> python <skill-dir>/scripts/md_to_html.py input.md /path/to/output.html
```

The script prints the **absolute** paths of both the input `.md` and the output
`.html`, plus a `file://` link — relay those verbatim so the user can open the
HTML directly (e.g. `open output.html`).

The page `<title>` is taken from the document's first `# H1`, falling back to the
file stem — so make the first line a descriptive title, not a filename.

## What the readable version gives you

A single self-contained HTML file (web fonts and, only for diagrams, Mermaid load
from a CDN at view time; offline it falls back to system fonts / readable source):

- **Editorial "書卷感" typography** for long-form Chinese: a warm-paper palette,
  generous line-height, an ideal reading width, and a 朱紅 (seal-red) accent
- A **Chinese font switcher** (top-left): 明體 (Noto Serif TC) / 楷體 (Iansui,
  default) / 文楷 (LXGW WenKai TC) / 楷體＋注音 (Bpmf Iansui) / 黑體 (Noto Sans TC) /
  圓體 (Huninn) — loaded lazily from Google Fonts, remembered in `localStorage`
- A **scroll-spy table of contents** auto-built from H2/H3: highlights the section
  you are reading and auto-numbers sections; clicking a link jumps cleanly without
  flickering the highlight through the sections in between
- A **reading-progress bar** pinned to the top
- A **light/dark theme toggle** (☾/☀, top-left): defaults to the system
  `prefers-color-scheme`, then remembers your choice; dark mode is a warm "sepia
  night" that keeps the book feel
- **Mermaid diagrams** rendered as vector graphics with native Chinese labels and a
  per-theme palette (re-render on theme/font change); the runtime is injected only
  when the doc actually contains a diagram, and degrades to readable source offline
- **★ Insight callouts**: a `★ Insight ─────` block (a `★ Insight` line, box-drawing
  `─` rules, the points, a closing `─` rule) renders as a styled "★ 重點" box. The
  rule lines may be wrapped in backticks — both forms are recognised.
- A built-in **print stylesheet** for printing / exporting to PDF (forces a light,
  paper palette regardless of the on-screen theme)

## Markdown the converter understands

Standard Markdown plus a few editorial touches:

- **Tables** — each is wrapped so a wide table scrolls horizontally inside its own
  box instead of squashing the prose column
- **Fenced code** — kept verbatim in a monospace, non-wrapping block (so ASCII
  diagrams stay aligned); a ` ```mermaid ` block becomes a rendered diagram
- **Multi-line metadata blockquotes** — separate `>` lines (source / author /
  link) keep their line breaks instead of running together
- **★ Insight blocks** — see above

## Dependencies

- The Python `markdown` package at **generation** time — declared in this skill's
  `pyproject.toml`, so `uv sync` (or running via `uv run`) provides it. Use `uv`,
  not `pip`.
- `mermaid.js` and the chosen **Chinese web font** load from a CDN at **view** time
  — nothing to install; the first open of a page with diagrams needs network access
  (only the library is fetched; diagram content stays local). Offline, fonts fall
  back to the system stack and diagrams degrade to readable Mermaid source.

## Tests

```bash
uv run --project <skill-dir> pytest
```

The suite encodes *why* each conversion matters (tables become real tables, ASCII
diagrams stay aligned verbatim, the page declares zh-TW + UTF-8, the TOC is built
from the headings, Mermaid is injected only when needed, the theme/font controls
work, ★ Insight blocks become callouts, …).
