"""PROTOTYPE, throwaway. Answers: can the Agent SDK dispatch /bible-buddy and have it
annotate the passage on screen via a custom tool, and how does that feel?

Run:  uv run uvicorn server:app --port 8765   then open http://127.0.0.1:8765
"""
import asyncio
import json
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
    tool,
)
from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse

HERE = Path(__file__).parent
SKILL = HERE / ".claude/skills/bible-buddy"
sys.path.insert(0, str(SKILL / "scripts"))
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
    passage.update(reference=r.get("reference", ""), version=version, verses=r.get("verses", []))
    return r


@app.get("/api/notes")
async def list_notes():
    return notes


@app.post("/api/notes")
async def add_user_note(body: dict):
    note = {"id": uuid.uuid4().hex[:8], "author": "user", "kind": "personal", **body}
    notes.append(note)
    return note


@app.get("/api/study", response_class=PlainTextResponse)
async def read_study(path: str):
    p = Path(path).expanduser().resolve()
    if not (p.suffix == ".md" and "bible-buddy" in p.parts and p.is_file()):
        return "not allowed"
    return p.read_text()


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
