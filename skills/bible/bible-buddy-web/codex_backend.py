"""Codex App Server chat and isolated structured note generation.

Protocol: https://developers.openai.com/codex/app-server
The host executes only the two supplied annotation tools; Codex never writes notes files.
"""
import asyncio
import json
import os
import tempfile
from pathlib import Path


def selected_backend() -> str:
    # The invoking skill sets this explicitly, even when both CLIs are installed.
    value = os.environ.get("BIBLE_BUDDY_BACKEND", "claude").strip().lower()
    if value not in {"claude", "codex"}:
        raise ValueError("BIBLE_BUDDY_BACKEND 必須是 claude 或 codex")
    return value


async def _terminate(process):
    if process.returncode is None:
        try:
            process.terminate()
        except ProcessLookupError:
            pass
        try:
            await asyncio.wait_for(process.wait(), 5)
        except TimeoutError:
            process.kill()
            await process.wait()


def _strict_schema(schema):
    """Codex structured output requires closed objects, including nested note objects."""
    if isinstance(schema, list):
        return [_strict_schema(v) for v in schema]
    if not isinstance(schema, dict):
        return schema
    result = {k: _strict_schema(v) for k, v in schema.items()}
    if result.get("type") == "object":
        result["additionalProperties"] = False
        result["required"] = list(result.get("properties", {}))
    return result


async def structured(prompt, schema):
    # A fresh empty cwd and no user config keep project skills/MCP out of a quick pass.
    with tempfile.TemporaryDirectory(prefix="bible-buddy-codex-") as tmp:
        root = Path(tmp)
        spec, output = root / "schema.json", root / "result.json"
        spec.write_text(json.dumps(_strict_schema(schema["schema"])))
        process = await asyncio.create_subprocess_exec(
            "codex", "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
            "--skip-git-repo-check", "--sandbox", "read-only", "-C", tmp,
            "-c", "features.shell_tool=false", "-c", "web_search=\"disabled\"",
            "--output-schema", str(spec), "--output-last-message", str(output), "-",
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE)
        try:
            _, error = await process.communicate(prompt.encode())
            if process.returncode:
                raise RuntimeError(error.decode(errors="replace")[-2000:] or "Codex 筆記生成失敗")
            data = json.loads(output.read_text())
            if not isinstance(data, dict):
                raise ValueError("Codex 筆記必須是 JSON object")
            yield data
        finally:
            await _terminate(process)


class CodexClient:
    """One reader's thread. A dedicated reader lets stop requests run during a turn."""

    def __init__(self, cwd, instructions, skill, tools):
        self.cwd, self.instructions, self.skill = cwd, instructions, skill
        self.tools = {t.name: t for t in tools}
        self.process = self.reader = None
        self.pending = {}
        self.messages = asyncio.Queue()
        self.seq = 0
        self.thread = self.turn = None
        self.stopping = False

    async def _send(self, message):
        self.process.stdin.write((json.dumps(message) + "\n").encode())
        await self.process.stdin.drain()

    async def _rpc(self, method, params):
        self.seq += 1
        rid = self.seq
        future = asyncio.get_running_loop().create_future()
        self.pending[rid] = future
        try:
            await self._send({"id": rid, "method": method, "params": params})
            return await asyncio.wait_for(future, 30)
        finally:
            self.pending.pop(rid, None)

    async def _read(self):
        try:
            while line := await self.process.stdout.readline():
                message = json.loads(line)
                if "method" not in message and message.get("id") in self.pending:
                    future = self.pending[message["id"]]
                    if not future.done():
                        if "error" in message:
                            future.set_exception(RuntimeError(str(message["error"])))
                        else:
                            future.set_result(message.get("result", {}))
                elif "method" in message:
                    await self.messages.put(message)
            raise RuntimeError("Codex App Server 已結束；請重新送出問題")
        except Exception as e:
            for future in self.pending.values():
                if not future.done():
                    future.set_exception(e)
            await self.messages.put(e)

    async def connect(self):
        self.process = await asyncio.create_subprocess_exec(
            "codex", "app-server", "--listen", "stdio://",
            cwd=str(self.cwd), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            limit=4 * 1024 * 1024)
        self.reader = asyncio.create_task(self._read())
        try:
            await self._rpc("initialize", {"clientInfo": {"name": "bible_buddy_web", "version": "1.0"},
                                           "capabilities": {"experimentalApi": True}})
            await self._send({"method": "initialized", "params": {}})
            settings = (await self._rpc(
                "config/read", {"cwd": str(self.cwd), "includeLayers": False}
            ))["config"]
            config = {"mcp_servers": {name: {"enabled": False}
                                      for name in (settings.get("mcp_servers") or {})}}
            specs = []
            for name, tool in self.tools.items():
                types = {str: "string", int: "integer", float: "number", bool: "boolean"}
                schema = {"type": "object", "properties": {k: {"type": types[v]} for k, v in tool.input_schema.items()},
                          "required": list(tool.input_schema), "additionalProperties": False}
                specs.append({"type": "function", "name": name, "description": tool.description, "inputSchema": schema})
            result = await self._rpc("thread/start", {
                "cwd": str(self.cwd), "ephemeral": True, "approvalPolicy": "never", "sandbox": "read-only",
                "developerInstructions": self.instructions.replace("mcp__notes__", "") + f"\nRead and follow {self.skill / 'SKILL.md'}. "
                    f"Resolve {{BIBLE_BUDDY}} to {self.skill}. You are Codex, not Claude Code. "
                    "Skip Claude-only setup/output-style instructions. Use the supplied notes tools for all notes; "
                    "do not write files. Ask questions in chat, not through request_user_input.",
                "dynamicTools": specs, "config": config})
            self.thread = result["thread"]["id"]
        except BaseException:
            await self.disconnect()
            raise

    async def query(self, prompt):
        self.stopping = False
        result = await self._rpc("turn/start", {"threadId": self.thread,
            "input": [{"type": "text", "text": prompt.removeprefix("/bible-buddy ")}]})
        self.turn = result["turn"]["id"]
        if self.stopping:
            await self.interrupt()

    async def _tool_call(self, params):
        tool = self.tools.get(params["tool"])
        args = params.get("arguments")
        if tool is None or not isinstance(args, dict):
            raise ValueError("Unknown annotation tool or invalid arguments")
        if set(args) != set(tool.input_schema):
            raise ValueError("Annotation arguments do not match the schema")
        if any(type(args[k]) is not typ for k, typ in tool.input_schema.items()):
            raise ValueError("Invalid annotation argument type")
        return await tool.handler(args)

    async def receive_response(self):
        try:
            while True:
                message = await self.messages.get()
                if isinstance(message, Exception):
                    raise message
                method, p = message["method"], message.get("params", {})
                if "id" in message:
                    if method == "item/tool/call":
                        yield {"type": "tool", "name": p["tool"], "input": json.dumps(p.get("arguments"), ensure_ascii=False)[:160]}
                        try:
                            result = await self._tool_call(p)
                            reply = {"success": not result.get("is_error", False), "contentItems": [
                                {"type": "inputText", "text": c["text"]} for c in result["content"]]}
                        except Exception as e:
                            reply = {"success": False, "contentItems": [{"type": "inputText", "text": str(e)}]}
                        await self._send({"id": message["id"], "result": reply})
                    else:
                        # Never hang awaiting an approval/question that this web UI cannot answer.
                        await self._send({"id": message["id"], "error": {"code": -32601, "message": "Unsupported request in Bible Buddy"}})
                elif method == "item/completed":
                    item = p["item"]
                    if item["type"] == "agentMessage":
                        yield {"type": "text", "text": item["text"]}
                elif method == "item/started" and p["item"]["type"] in {"commandExecution", "webSearch", "mcpToolCall"}:
                    item = p["item"]
                    yield {"type": "tool", "name": item["type"], "input": str(item.get("command", item.get("query", "")))[:160]}
                elif method == "turn/completed":
                    turn = p["turn"]
                    if turn["status"] == "failed":
                        raise RuntimeError(str(turn.get("error") or "Codex turn failed"))
                    yield {"type": "done", "cost": None, "turns": 1, "is_error": False,
                           "result": "已停止" if turn["status"] == "interrupted" else ""}
                    return
        finally:
            self.turn = None

    async def interrupt(self):
        self.stopping = True
        if self.turn:
            await self._rpc("turn/interrupt", {"threadId": self.thread, "turnId": self.turn})

    async def disconnect(self):
        if self.process is not None:
            await _terminate(self.process)
        if self.reader is not None:
            self.reader.cancel()
            await asyncio.gather(self.reader, return_exceptions=True)
