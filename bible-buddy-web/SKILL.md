---
name: bible-buddy-web
description: "Local web reader for Bible passages with ELI5 annotations — a FastAPI + Claude Agent SDK page that loads a passage from FHL, drops plain-language notes onto the words themselves, and lets a bible-buddy agent verify or expand any of them. Use when the user wants to READ or STUDY scripture in a browser rather than in the terminal: 開網頁查經、網頁版 bible buddy、經文標注、ELI5 筆記、劃線筆記、annotate a passage, bible reader UI, start the bible web app. EXCLUDE: terminal Bible Q&A (bible-buddy), devotionals (bible-bread), content review (bible-fact-check)."
allowed-tools: Read Write Edit Bash Glob Grep
disable-model-invocation: true
license: MIT
---

**回應語言：一律使用台灣繁體中文。**

# Bible Buddy ELI5 — 網頁查經

A local reading desk for scripture. It loads a passage from FHL, drops plain-language
notes onto the words themselves, and lets a `/bible-buddy` agent verify or expand any of
them through a custom tool.

**Single user, single machine, by design.** State is a module-level dict, notes autosave
to one JSON per passage on the Desktop, one event queue serves one reader. It binds
loopback only. Don't put it behind a shared port.

## Path Resolution

Resolve `{WEB}` to this skill's own installation directory. First path that has `server.py`:

1. `.claude/skills/bible-buddy-web/`
2. `~/.claude/skills/bible-buddy-web/`
3. `bible-buddy-web/` (relative to CWD, development)

## Prerequisites

`uv` must be installed (`which uv`). If missing, stop and tell the user:
「bible-buddy-web 需要 uv 套件管理器。請參考 https://docs.astral.sh/uv/getting-started/installation/ 安裝後再試。」

The **bible-buddy skill must be installed alongside it** — `{WEB}/.claude/skills/bible-buddy`
is a symlink to the sibling skill, and the server imports its `scripts/` (FHL fetcher, book
names, Desktop detection) and reads its `references/` tables. Verify before launching:

```bash
test -d {WEB}/.claude/skills/bible-buddy/scripts && echo OK
```

Not OK → tell the user to install bible-buddy the same way (`npx skills add lancetw/skills -g -s bible-buddy`).

## Launch

```bash
uv sync --directory {WEB}
uv run --directory {WEB} uvicorn server:app --port 8765
```

**The user named a passage** (`/bible-buddy-web 路加福音`)? Two cases, and neither is "launch and
let them type it in":

- Server not running yet → put it in the launch environment. The page then opens straight on that
  passage; without this it opens on whatever the browser last read and flips a second later.
  ```bash
  BIBLE_BUDDY_PASSAGE='路加福音' uv run --directory {WEB} uvicorn server:app --port 8765
  ```
  `BIBLE_BUDDY_VERSION` sets the translation (default `rcuv`).
- Server already running → `POST /api/display`, below.

Run it **in the background** and leave it running — the page is the deliverable, and the
agent turns it serves take minutes. The server opens the page in the default browser once it
is ready; still give the user the URL (`http://127.0.0.1:8765`) in case the browser is not
where they are looking. `BIBLE_BUDDY_NO_OPEN=1` suppresses the auto-open.

Port 8765 taken → pick another, pass it as `--port` (the auto-open reads that flag) and say
which one you used. The server binds loopback only.

### The proxy trap

The server drops loopback `HTTP(S)_PROXY` variables at import, on purpose. A package-manager
guard exports a short-lived proxy that dies with it, and the Claude CLI the SDK spawns would
inherit it and fail every call with "Connection refused". Leave that block alone.

## Driving the page from Claude Code

The page is not only steered from its own input box. `POST /api/display` sets what the browser
should be showing; the page polls every 2s and loads it. Use this whenever the user asks for a
passage while the app is running — do not tell them to type it in themselves.

```bash
curl -s -X POST http://127.0.0.1:8765/api/display \
  -H 'content-type: application/json' \
  -d '{"ref": "約翰福音 3:16", "version": "rcuv"}'
```

- `ref` takes the same grammar as the page's own box: `約翰福音 3:16`, `以賽亞書 7:10-17`,
  `創世記 1` (whole chapter), `約翰福音` (= chapter 1). It is parsed by the page, so a bad
  reference shows up on the page's banner, not in this call's response.
- `version` — `rcuv` / `lcc` / `bhs` / `nt`. Omit it to keep the one on screen; omit `ref` to
  change only the version.
- The response echoes `rev`, a counter in server memory. `GET /api/display` reads it back.
  A page opened *after* the command still obeys it: the page asks `/api/display` before it falls
  back to the passage in its own localStorage, so a pending command wins on first paint.

The command changes the passage, which restarts the agent session and switches the notes file,
exactly as if the user had pressed 載入.

## What the page does

**Passage bar** — reference plus version (和合本修訂版 / 呂振中 / BHS 希伯來文 / NT 希臘文),
fetched from FHL. `以賽亞書 7` (no verses) loads the whole chapter. Translator footnotes are
split out of the verse text into a 譯註 list, and note anchors are offsets into the *stripped*
text.

**🔍 全本搜尋** — keyword search across all 66 books (FHL `se.php`), in whichever version the bar
has selected. A hit loads that whole chapter and scrolls to the verse. The search index carries
some versions in their Strong's-number edition, so hit previews are stripped before display;
an original-language version finds nothing for a Chinese keyword.

**原文** — two views, both off by default:

- **「原」 in the verse gutter** expands FHL's word analysis (`qp.php`, one verse per call — a
  whole chapter errors out) under that verse: the original verse, every word with its 字形分析
  and 中文字義, and a 直譯 line. Hebrew renders RTL, Greek LTR. Clicking a word opens its Strong's
  entry (`sd.php`) in the note card — transliteration, 欽定本 counts, gloss tree. Plain text,
  escaped, never run through the markdown renderer.
- **⇄ 雙欄對照** puts a second version in a right-hand column, verse-aligned. `原文` picks BHS or
  NT 希臘文 by testament. It reads through `/api/side`, which deliberately does **not** touch the
  server's passage state or restart the agent session the way `/api/passage` does.

Both survive `render()` (which rebuilds `#verses` on every note change) because the open verses
and their fetched data live in module state, not in the DOM.

**Notes land on the words.** Four sources, each tagged on its card:

| Author | Where it comes from | Cost |
|---|---|---|
| `refs` | bible-buddy's own `translation-bias.md` / `commonly-misread-passages.md` tables, matched to the loaded verses, served in Chinese through `references/zh-notes.json` | free, instant, already verified |
| `quick` | ✨ 生成 ELI5 筆記 — one schema-constrained model pass, 10–14 notes for the whole passage | one paid pass, cached per passage+version |
| `agent` | the chat agent calling `mcp__notes__add_annotation` during a turn | part of the turn |
| `user` | 反白經文 → ✎ 手動筆記 | free |

反白 a phrase → ✨ ELI5 筆記 writes one note for exactly those words (not cached — the user
asked for that one). A `quick` note is flagged 未驗證; its card offers 🔍 請 agent 驗證, which
sends the agent a turn that ends in `mcp__notes__update_annotation` on the same id, so the
note is rewritten in place rather than duplicated.

**Chat** streams over SSE. A refreshed page reattaches to the running turn instead of losing
it. Changing passage starts a fresh agent session, since the old history is about other verses.

### The reference tables are English

bible-buddy's tables are written in English, and this is a Chinese reading desk. `references/zh-notes.json`
holds the Traditional Chinese `label` and `body` of every row, keyed by the note id that `_ref_notes()`
derives from the row's own cells. A row with no entry serves in English rather than failing, and a passage
whose notes were saved before the file existed is re-translated when it is loaded again.

Upstream edits a row → its cells change → its id changes → it falls back to English until regenerated:

```bash
uv run --directory {WEB} python translate_refs.py        # only the ids the file is missing
uv run --directory {WEB} python translate_refs.py --force  # all 96 rows again
```

That is a paid model pass (about US$2 for the whole set, ~$0.10 per batch of 6). Don't run it as a
side effect of something else; the committed JSON is what makes these notes free at read time.

## Where the work is saved

`~/Desktop/bible-buddy/notes/<reference> (<version>).json`, rewritten atomically on every
mutation, plus `.last-passage.json` so a restarted server restores what the page is showing.
Deleted notes are remembered as hidden ids — the cached ELI5 pass must not resurrect them.

## When something goes wrong

**✗ ELI5 筆記失敗：API 529 過載** — the pass is not cached on failure, so the button doubles
as retry. Retries are capped at 3 and the pass has a 180s ceiling, by design: the CLI's own
~10 retries kept the spinner up for minutes.

**「尚未載入經文」** — chat, ELI5 and notes all need a passage; the server reloads the last
one automatically, so this means that reload also failed (usually FHL unreachable).

**A quote that does not match the verse** — the note degrades to verse-level (no underline)
instead of failing. Expected, not a bug.

Failures surface rather than being swallowed. Read the uvicorn stderr for `model pass:` /
`model retry:` / `quick pass failed:` lines before theorising.
