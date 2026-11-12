"""One-off generator: bible-buddy's reference tables are English, the reader is Chinese.

Walks server._ref_notes() and writes references/zh-notes.json — {note id: {label, body}} in Taiwan
Traditional Chinese. Ids come from the table cells, so an upstream edit changes that row's id and it
falls back to English until this is re-run. Rerunning only translates ids the file does not have.

    uv run --directory . python translate_refs.py [--batch 6] [--force]
"""
import asyncio
import json
import sys

from server import ZH_REFS, _ref_notes, _short_label, _structured

SCHEMA = {"type": "json_schema", "schema": {
    "type": "object", "required": ["items"],
    "properties": {"items": {"type": "array", "items": {
        "type": "object", "required": ["id", "label", "body"],
        "properties": {"id": {"type": "string"}, "label": {"type": "string"}, "body": {"type": "string"}}}}}}}

PROMPT = """把下面每一條聖經筆記翻成台灣繁體中文。這些筆記給一般讀經的人看，不是給學者看。

規則：
- 逐條翻譯，id 原樣回傳，不要合併或漏掉任何一條。
- 保留 markdown：`**中譯：**`、`**原文：**`、`**影響：**`、`**常見誤讀：**`、`**第一世紀脈絡：**` 這些標題已經是中文，原樣保留；其餘 ** ** 粗體位置也保留。
- 希伯來文、希臘文原文字、音譯（chesed、plerosai…）、經卷章節（Gen 1:1、Deut 32:11）、學術書名一律保留原文，不要翻也不要拿掉。
- 譯文要讀得順，是中文句子不是英文直譯；術語第一次出現時可用括號補五個字內的白話。
- label：20 個中文字寬（拉丁音譯算半形，兩個字母當一個中文字）以內。原本就是中文的（像「慈愛＝chesed hesed」）就原樣保留；英文或被截斷的（像「誤讀 · plerosai (πληρ」）改寫成看得懂的中文短標，誤讀類保留開頭的「誤讀 · 」。
- body：句意完整翻完，不要摘要、不要刪內容、不要自己加解釋。

{rows}"""


async def run(batch: dict) -> list[dict]:
    rows = "\n\n".join(f"id: {k}\nlabel: {v['label']}\nbody: {v['body']}" for k, v in batch.items())
    data, cost = await _structured(PROMPT.format(rows=rows), SCHEMA, "translate-refs")
    print(f"  {cost} USD" if cost is not None else "  cost unavailable", file=sys.stderr)
    return data.get("items", [])


def _batch_size() -> int:
    return int(sys.argv[sys.argv.index("--batch") + 1]) if "--batch" in sys.argv else 6


def _already_done() -> dict:
    """What earlier runs translated. --force starts over; a missing file is a first run."""
    if "--force" in sys.argv or not ZH_REFS.is_file():
        return {}
    return json.loads(ZH_REFS.read_text())


def _keep(done: dict, items: list[dict], chunk: dict) -> None:
    for it in items:
        if it["id"] in chunk:  # a hallucinated id would otherwise write a note nobody serves
            done[it["id"]] = {"label": _short_label(it["label"]), "body": it["body"]}
    ZH_REFS.parent.mkdir(parents=True, exist_ok=True)
    ZH_REFS.write_text(json.dumps(done, ensure_ascii=False, indent=1, sort_keys=True))


async def main() -> None:
    size, done = _batch_size(), _already_done()
    todo = {f["id"]: f for _, _, f in _ref_notes() if f["id"] not in done}
    print(f"{len(done)} already translated, {len(todo)} to go", file=sys.stderr)
    ids = list(todo)
    for n in range(0, len(ids), size):
        chunk = {i: todo[i] for i in ids[n:n + size]}
        print(f"batch {n // size + 1}/{-(-len(ids) // size)} ({len(chunk)} rows)", file=sys.stderr)
        try:
            items = await run(chunk)
        except Exception as e:  # one bad batch must not throw away the batches before it
            print(f"  failed: {e!r}", file=sys.stderr)
            continue
        _keep(done, items, chunk)
    print(f"wrote {len(done)} rows to {ZH_REFS}", file=sys.stderr)


asyncio.run(main())
