"""PROTOTYPE, throwaway. Answers: can the Agent SDK dispatch /bible-buddy and have it
annotate the passage on screen via a custom tool, and how does that feel?

Run:  uv run uvicorn server:app --port 8765   then open http://127.0.0.1:8765
"""
import asyncio
import hashlib
import shutil
import subprocess
import json
import os
import re
import sys
import uuid
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    query,
    tool,
)
from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse

# A package-manager guard (pmg) launches `uv run` behind a short-lived loopback proxy and exports it
# (HTTPS_PROXY=http://127.0.0.1:NNNNN, NODE_USE_ENV_PROXY=1). The Claude CLI we spawn would inherit
# that and get "Connection refused" once the guard exits, so drop loopback proxies before anything spawns.
for _k in [k for k in os.environ if k.lower() in ("http_proxy", "https_proxy", "all_proxy", "pip_proxy")]:
    if "127.0.0.1" in os.environ[_k] or "localhost" in os.environ[_k]:
        del os.environ[_k]

HERE = Path(__file__).parent
SKILL = HERE / ".claude/skills/bible-buddy"
sys.path.insert(0, str(SKILL / "scripts"))
from book_names import lookup  # noqa: E402
from detect_desktop import detect_desktop  # noqa: E402
from fetch_fhl import fetch  # noqa: E402  bible-buddy's own fetcher, stdlib only

app = FastAPI()
passage: dict = {"reference": "", "version": "rcuv", "verses": []}
notes: list[dict] = []
events: asyncio.Queue = asyncio.Queue()  # ponytail: one global queue = one user

SYSTEM_APPEND = """你在一個網頁查經工具裡工作。畫面左側顯示 [目前畫面] 列出的經文。
每個關鍵發現（原文字義 lexical、歷史背景 history、常見誤讀或翻譯偏差 misread、相關經文 crossref）
呼叫一次 mcp__notes__add_annotation：quote 必須逐字取自 [目前畫面] 的該節經文，label 20 字內，長分析放 body。
需要使用者選擇時，用編號清單，最後一行寫「請選擇 (1-N)：」。AskUserQuestion 工具不可用。"""


@app.get("/")
async def index():
    return FileResponse(HERE / "static/index.html")


@app.get("/api/passage")
async def get_passage(book: str = "以賽亞書", chapter: int = 7, start: int = 10, end: int = 17, version: str = "rcuv"):
    r = await asyncio.to_thread(fetch, book, chapter, start, end, version)
    if r.get("reference") != passage["reference"]:
        notes.clear()  # notes carry no book/chapter; a new passage means a clean slate
    passage.update(reference=r.get("reference", ""), version=version, verses=r.get("verses", []), book=book)
    return r


@app.get("/api/notes")
async def list_notes():
    return notes


@app.post("/api/notes")
async def add_user_note(body: dict):
    note = {"id": uuid.uuid4().hex[:8], "author": "user", "kind": "personal", **body}
    notes.append(note)
    return note


STUDY_DIR = detect_desktop("bible-buddy")  # where the skill auto-saves its .md reports


@app.get("/api/studies")
async def list_studies():
    files = sorted(STUDY_DIR.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)[:30]
    return [{"name": f.name, "path": str(f)} for f in files]


def _study_file(path: str) -> Path | None:
    p = Path(path).expanduser().resolve()
    return p if p.suffix == ".md" and p.parent == STUDY_DIR.resolve() and p.is_file() else None


@app.get("/api/study", response_class=PlainTextResponse)
async def read_study(path: str):
    p = _study_file(path)
    return p.read_text() if p else "not allowed"


@app.delete("/api/study")
async def delete_study(path: str):
    """Move the report (and its .html twin) to the Trash, never rm: a study is minutes of agent work."""
    p = _study_file(path)
    if not p:
        return {"ok": False, "error": "not allowed"}
    targets = [f for f in (p, p.with_suffix(".html")) if f.exists()]
    if shutil.which("trash"):
        subprocess.run(["trash", *map(str, targets)], check=True)
    else:  # ponytail: no trash CLI → park under .trash/ next to the reports
        bin_ = STUDY_DIR / ".trash"; bin_.mkdir(exist_ok=True)
        for f in targets:
            f.rename(bin_ / f.name)
    return {"ok": True, "trashed": [f.name for f in targets]}


@tool(
    "add_annotation",
    "在網頁經文閱讀區加一條筆記。quote 必須是 [目前畫面] 中該節經文的逐字子字串；label 20 字內；長分析放 body。kind: lexical|history|misread|crossref",
    {"verse": int, "quote": str, "label": str, "body": str, "kind": str},
)
async def add_annotation(args: dict) -> dict:
    v = next((x for x in passage["verses"] if str(x["verse"]) == str(args["verse"])), None)
    text = v["text"] if v else ""
    i = text.find(args["quote"])
    note = {
        "id": uuid.uuid4().hex[:8],
        "verse": str(args["verse"]),
        "anchor": None if i < 0 else {"start": i, "end": i + len(args["quote"])},
        "label": args["label"][:20],
        "body": args.get("body", ""),
        "kind": args.get("kind", "lexical"),
        "author": "agent",
    }
    notes.append(note)
    await events.put({"type": "note", "note": note})
    miss = "" if i >= 0 else "（quote 對不上畫面經文，已改為節層級筆記）"
    return {"content": [{"type": "text", "text": f"已加入筆記 {note['id']} {miss}"}]}


_client: ClaudeSDKClient | None = None


async def get_client() -> ClaudeSDKClient:
    global _client
    if _client is None:
        opts = ClaudeAgentOptions(
            cwd=str(HERE),
            setting_sources=["project"],
            system_prompt={"type": "preset", "preset": "claude_code", "append": SYSTEM_APPEND},
            mcp_servers={"notes": create_sdk_mcp_server("notes", tools=[add_annotation])},
            allowed_tools=["Read", "Grep", "Glob", "Bash", "WebSearch", "WebFetch", "Write", "Edit", "Skill", "mcp__notes__add_annotation"],
            disallowed_tools=["AskUserQuestion"],
            permission_mode="acceptEdits",
            max_turns=80,
            max_budget_usd=5.0,
        )
        _client = ClaudeSDKClient(options=opts)
        await _client.connect()
    return _client


def _short(d: dict) -> str:
    s = json.dumps(d, ensure_ascii=False)
    return s if len(s) < 160 else s[:160] + "…"


async def run_turn(message: str) -> None:
    try:
        c = await get_client()
        ctx = "\n".join(f"[{v['verse']}] {v['text']}" for v in passage["verses"])
        prompt = f"/bible-buddy {message}\n\n[目前畫面] {passage['reference']}（{passage['version']}）\n{ctx}"
        await c.query(prompt)
        async for m in c.receive_response():
            if isinstance(m, SystemMessage) and m.subtype == "init":
                print("skills loaded:", m.data.get("skills"), file=sys.stderr)
            elif isinstance(m, AssistantMessage):
                for b in m.content:
                    if isinstance(b, TextBlock):
                        await events.put({"type": "text", "text": b.text})
                    elif isinstance(b, ToolUseBlock):
                        await events.put({"type": "tool", "name": b.name, "input": _short(b.input)})
            elif isinstance(m, ResultMessage):
                await events.put({"type": "done", "cost": m.total_cost_usd, "turns": m.num_turns, "is_error": m.is_error, "result": m.result})
    except Exception as e:  # prototype: surface, don't handle
        await events.put({"type": "error", "text": repr(e)})


@app.post("/api/chat/stop")
async def chat_stop():
    if _client is not None:
        await _client.interrupt()  # the running turn ends with a ResultMessage, which the SSE loop turns into "done"
    return {"ok": True}


@app.post("/api/chat")
async def chat(body: dict):
    asyncio.create_task(run_turn(body["message"]))

    async def gen():
        while True:
            try:
                ev = await asyncio.wait_for(events.get(), 15)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
                continue
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
            if ev["type"] in ("done", "error"):
                break

    return StreamingResponse(gen(), media_type="text/event-stream")


# ── auto notes: arrows on load, before anyone asks the agent ──────────────────
REFS = SKILL / "references"
KINDS = ["lexical", "history", "misread", "crossref"]
_quick_cache: dict[str, list] = {}  # ponytail: in-memory; sqlite in the real thing


def _note_id(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:8]


def _verse_text(verse: str) -> str:
    v = next((x for x in passage["verses"] if str(x["verse"]) == str(verse)), None)
    return v["text"] if v else ""


def _add(note: dict) -> dict | None:
    if any(n["id"] == note["id"] for n in notes):
        return None
    notes.append(note)
    return note


def _table_rows(path: Path):
    for line in path.read_text().splitlines():
        if not line.startswith("| ") or line.startswith("| Scripture") or line.startswith("|---"):
            continue
        yield [c.strip() for c in line.strip().strip("|").split("|")]


def _verses_in(ref: str) -> list[str]:
    """'Isaiah 7:14' / 'Isaiah 7:10-17' / 'Isaiah 7' → loaded verse numbers it covers."""
    info = lookup(passage.get("book", ""))
    if not info:
        return []
    names = {info[1], info[3]}
    m = re.match(r"^(.+?) (\d+)(?::(\d+)(?:-(\d+))?)?$", ref)
    if not m or m.group(1) not in names or int(m.group(2)) != int(re.search(r" (\d+)", passage["reference"]).group(1)):
        return []
    loaded = [str(v["verse"]) for v in passage["verses"]]
    if not m.group(3):
        return loaded
    lo, hi = int(m.group(3)), int(m.group(4) or m.group(3))
    return [v for v in loaded if lo <= int(v) <= hi]


@app.get("/api/auto-notes/refs")
async def auto_notes_refs():
    """Instant, verified: rows from bible-buddy's own reference tables that hit the loaded passage."""
    out = []
    for cells in _table_rows(REFS / "translation-bias.md"):
        if len(cells) < 5 or cells[3].startswith("Same as"):
            continue
        for v in _verses_in(cells[0]):
            bold = re.search(r"\*\*(.+?)\*\*", cells[1])
            text = _verse_text(v)
            i = text.find(bold.group(1)) if bold else -1
            term = re.match(r"^(\S+) \((\w+)\)", cells[3])
            label = f"{bold.group(1)}＝{term.group(1)} {term.group(2)}" if bold and term else cells[3][:20]
            note = {"id": _note_id("bias", cells[0], cells[1]), "verse": v,
                    "anchor": None if i < 0 else {"start": i, "end": i + len(bold.group(1))},
                    "label": label[:20], "body": f"**中譯：** {cells[2]}\n\n**原文：** {cells[3]}\n\n**影響：** {cells[4]}",
                    "kind": "misread", "author": "refs"}
            if _add(note):
                out.append(note)
    for cells in _table_rows(REFS / "commonly-misread-passages.md"):
        if len(cells) < 4:
            continue
        for v in _verses_in(cells[0]):
            text = _verse_text(v)
            head = re.split(r"[，：「。；]", text)[0][:8]  # arrow on the verse's first clause
            note = {"id": _note_id("misread", cells[0], cells[3]), "verse": v,
                    "anchor": {"start": 0, "end": len(head)} if head else None,
                    "label": f"誤讀 · {cells[3].replace('*', '')[:14]}", "body": f"**常見誤讀：** {cells[1]}\n\n**第一世紀脈絡：** {cells[2]}",
                    "kind": "misread", "author": "refs"}
            if _add(note):
                out.append(note)
    return out


QUICK_SCHEMA = {"type": "json_schema", "schema": {
    "type": "object", "required": ["notes"],
    "properties": {"notes": {"type": "array", "items": {
        "type": "object", "required": ["verse", "quote", "label", "body", "kind"],
        "properties": {"verse": {"type": "integer"}, "quote": {"type": "string"}, "label": {"type": "string"},
                       "body": {"type": "string"}, "kind": {"type": "string", "enum": KINDS}}}}}}}

QUICK_PROMPT = """你是第一世紀猶太教背景的聖經學者。對下面這段經文產生 10 到 14 條速讀筆記，讓讀者一眼看到值得停下來的字。
規則：
- quote：逐字取自該節經文的子字串，2 到 8 個字，不含標點；每節最多 2 條，不同條不可重疊。
- label：台灣繁體中文，14 字以內；原文字義類寫成「希伯來/希臘字 音譯＝意思」，例「עַלְמָה almah＝年輕女子」。
- body：1 到 3 句，說明為什麼重要；不確定的寫「（待驗證）」。
- kind：lexical（原文字義）、history（歷史處境）、misread（常見誤讀或翻譯偏差）、crossref（相關經文）。
- 不要教會式應用，不要靈意化。

{ref}（{version}）
{text}"""


_quick_tasks: dict[str, asyncio.Task] = {}
_quick_status: dict[str, str] = {}  # live progress per passage, e.g. "API 529 重試 2/3"; the page polls it while waiting
QUICK_RETRIES = 3     # the CLI retries 529/5xx itself with backoff; its default (~10) kept the spinner up for minutes
QUICK_TIMEOUT_S = 180  # hard ceiling on one pass, so the button can never spin forever


async def _quick_run(key: str, ref: str, version: str, verses: list[dict]) -> list[dict]:
    """The model pass itself. Runs as its own Task so a page refresh (client disconnect) cannot cancel it."""
    text = "\n".join(f"[{v['verse']}] {v['text']}" for v in verses)
    opts = ClaudeAgentOptions(cwd=str(HERE), setting_sources=[], tools=[], allowed_tools=[], max_turns=1,
                              output_format=QUICK_SCHEMA, env={"CLAUDE_CODE_MAX_RETRIES": str(QUICK_RETRIES)})
    found: list[dict] = []
    _quick_status[key] = ""
    try:
        async with asyncio.timeout(QUICK_TIMEOUT_S):
            async for m in query(prompt=QUICK_PROMPT.format(ref=ref, version=version, text=text), options=opts):
                if isinstance(m, SystemMessage) and m.subtype == "api_retry":
                    d = m.data
                    _quick_status[key] = f"API {d.get('error_status') or '?'}，重試 {d.get('attempt')}/{d.get('max_retries')}（{round((d.get('retry_delay_ms') or 0) / 1000)}s 後）"
                    print("quick pass retry:", key, _quick_status[key], file=sys.stderr)
                elif isinstance(m, ResultMessage):
                    if m.is_error:  # an API failure (529 overloaded, timeout) arrives as a result, not an exception
                        raise RuntimeError(m.result or f"API error (HTTP {m.api_error_status})")
                    found = (m.structured_output or {}).get("notes", [])
                    print("quick pass:", ref, len(found), "notes", m.total_cost_usd, "USD", file=sys.stderr)
    except TimeoutError:
        raise RuntimeError(f"逾時：{QUICK_TIMEOUT_S}s 內沒有結果（API 可能過載）") from None
    finally:
        _quick_status.pop(key, None)
    return found


@app.get("/api/auto-notes/quick/status")
async def auto_notes_quick_status():
    key = f"{passage['reference']}|{passage['version']}"
    return {"status": _quick_status.get(key, "")}


@app.get("/api/auto-notes/quick")
async def auto_notes_quick():
    """One cheap model pass per passage. Concurrent or repeated callers (a refreshed page) share the same Task.
    A failed pass is not cached: the next call starts a fresh Task, so the button doubles as retry."""
    key = f"{passage['reference']}|{passage['version']}"
    if key not in _quick_cache:
        task = _quick_tasks.get(key)
        if task is None or (task.done() and task.exception() is not None):
            task = _quick_tasks[key] = asyncio.create_task(_quick_run(key, passage["reference"], passage["version"], list(passage["verses"])))
        try:
            _quick_cache[key] = await asyncio.shield(task)  # shield: cancelling this request must not cancel the shared task
        except Exception as e:
            print("quick pass failed:", key, repr(e), file=sys.stderr)
            return {"error": str(e)}
    out = []
    for n in _quick_cache[key]:
        text = _verse_text(n["verse"])
        i = text.find(n["quote"])
        note = {"id": _note_id("quick", key, str(n["verse"]), n["quote"]), "verse": str(n["verse"]),
                "anchor": None if i < 0 else {"start": i, "end": i + len(n["quote"])},
                "label": n["label"][:20], "body": n["body"],  # author=quick is what the UI flags as unverified
                "kind": n["kind"] if n["kind"] in KINDS else "lexical", "author": "quick"}
        if _add(note):
            out.append(note)
    return out
