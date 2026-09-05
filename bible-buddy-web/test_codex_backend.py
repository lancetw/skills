"""The two hosts must produce the same saved notes and terminate every turn."""
import asyncio
import json
from types import SimpleNamespace

import pytest

import codex_backend as backend
import server
from test_server import desk, run


def test_host_choice_is_explicit_even_with_both_host_environments(monkeypatch):
    monkeypatch.setenv('CLAUDECODE', '1')
    monkeypatch.setenv('CODEX_THREAD_ID', 'parent')
    monkeypatch.delenv('BIBLE_BUDDY_BACKEND', raising=False)
    assert backend.selected_backend() == 'claude'
    for host in ('codex', 'claude'):
        monkeypatch.setenv('BIBLE_BUDDY_BACKEND', host)
        assert backend.selected_backend() == host
    monkeypatch.setenv('BIBLE_BUDDY_BACKEND', 'typo')
    with pytest.raises(ValueError):
        backend.selected_backend()


def client():
    return backend.CodexClient(server.HERE, server.SYSTEM_APPEND, server.SKILL,
                               [server.add_annotation, server.update_annotation])


def test_codex_tool_adds_and_verifies_the_same_saved_note(desk):
    async def exercise():
        c = client()
        await c._tool_call({'tool': 'add_annotation', 'arguments': {
            'verse': 4, 'quote': '光和暗', 'label': '分開', 'body': 'b', 'kind': 'lexical'}})
        nid, anchor = server.notes[0]['id'], server.notes[0]['anchor']
        await c._tool_call({'tool': 'update_annotation', 'arguments': {
            'id': nid, 'label': '已修正', 'body': '查證內容', 'kind': 'history'}})
        saved = json.loads(server._notes_file().read_text())['notes']
        assert len(saved) == 1 and saved[0]['id'] == nid
        assert saved[0]['anchor'] == anchor and saved[0]['verified'] is True
        for name, args in [('unknown', {}), ('add_annotation', {}), ('add_annotation', {
                'verse': True, 'quote': '光', 'label': 'x', 'body': '', 'kind': 'lexical'})]:
            with pytest.raises(ValueError):
                await c._tool_call({'tool': name, 'arguments': args})
        assert len(server.notes) == 1
    run(exercise())


def test_codex_events_reply_to_tools_and_surface_failure(desk):
    async def exercise():
        c, replies = client(), []
        async def send(message): replies.append(message)
        c._send = send
        await c.messages.put({'id': 8, 'method': 'item/tool/call', 'params': {
            'tool': 'add_annotation', 'arguments': {'verse': 4, 'quote': '光和暗',
                'label': '分開', 'body': '', 'kind': 'lexical'}}})
        await c.messages.put({'method': 'item/completed', 'params': {
            'item': {'type': 'agentMessage', 'text': '回答'}}})
        await c.messages.put({'method': 'turn/completed', 'params': {'turn': {'status': 'completed'}}})
        events = [ev async for ev in c.receive_response()]
        assert [ev['type'] for ev in events] == ['tool', 'text', 'done']
        assert replies[0]['id'] == 8 and replies[0]['result']['success'] is True
        assert events[-1]['cost'] is None
        await c.messages.put({'method': 'turn/completed', 'params': {
            'turn': {'status': 'failed', 'error': {'message': 'offline'}}}})
        with pytest.raises(RuntimeError, match='offline'):
            async for _ in c.receive_response(): pass
        assert c.turn is None
    run(exercise())


def test_stop_during_turn_start_is_not_lost():
    async def exercise():
        c, calls = client(), []
        c.thread = 'thread'
        async def rpc(method, params):
            calls.append((method, params))
            if method == 'turn/start':
                await c.interrupt()
                return {'turn': {'id': 'turn'}}
            return {}
        c._rpc = rpc
        await c.query('/bible-buddy hello')
        assert calls[-1] == ('turn/interrupt', {'threadId': 'thread', 'turnId': 'turn'})
        assert calls[0][1]['input'][0]['text'] == 'hello'
        await c.messages.put({'method': 'turn/completed', 'params': {'turn': {'status': 'interrupted'}}})
        events = [ev async for ev in c.receive_response()]
        assert events[-1]['result'] == '已停止'
    run(exercise())


def test_dead_process_wakes_pending_rpc_and_stream():
    async def exercise():
        c = client()
        stdout = asyncio.StreamReader()
        stdout.feed_eof()
        c.process = SimpleNamespace(stdout=stdout)
        f = asyncio.get_running_loop().create_future()
        c.pending[1] = f
        await c._read()
        with pytest.raises(RuntimeError, match='已結束'): await f
        with pytest.raises(RuntimeError, match='已結束'):
            async for _ in c.receive_response(): pass
    run(exercise())


def test_codex_schema_closes_nested_objects_without_changing_claude_schema():
    original = json.dumps(server.QUICK_SCHEMA)
    schema = backend._strict_schema(server.QUICK_SCHEMA['schema'])
    assert schema['additionalProperties'] is False
    assert schema['properties']['notes']['items']['additionalProperties'] is False
    assert json.dumps(server.QUICK_SCHEMA) == original


def test_quick_codex_pass_uses_existing_cache_without_fabricating_cost(desk, monkeypatch):
    calls = []
    async def structured(prompt, schema):
        calls.append(prompt)
        yield {'notes': [{'verse': 4, 'quote': '光和暗', 'label': '分開', 'body': '',
                          'kind': 'lexical', 'doodle': 'lamp'}]}
    monkeypatch.setattr(server, 'BACKEND', 'codex')
    monkeypatch.setattr(server, 'codex_structured', structured)
    first = run(server.auto_notes_quick())
    second = run(server.auto_notes_quick())
    assert len(calls) == 1 and first['cost'] is None and second['cached'] is True
    assert run(server.chat_status())['backend'] == 'codex'


def test_changed_passage_replaces_codex_thread(desk, monkeypatch):
    clients = []
    class FakeClient:
        def __init__(self, *args): self.closed = False; clients.append(self)
        async def connect(self): pass
        async def disconnect(self): self.closed = True
    monkeypatch.setattr(server, 'BACKEND', 'codex')
    monkeypatch.setattr(server, 'CodexClient', FakeClient)
    monkeypatch.setattr(server, '_client', None)
    monkeypatch.setattr(server, '_client_stale', False)
    async def exercise():
        first = await server.get_client()
        assert await server.get_client() is first
        await server.chat_reset()
        second = await server.get_client()
        assert first.closed and second is not first
    run(exercise())


def test_reference_translation_keeps_its_original_timeout(monkeypatch):
    import runpy
    calls = []
    async def structured(prompt, schema, key, **kwargs):
        calls.append(kwargs)
        return {'items': []}, None
    monkeypatch.setattr(server, '_structured', structured)
    with monkeypatch.context() as patch:
        patch.setattr(asyncio, 'run', lambda coro: coro.close())
        module = runpy.run_path(str(server.HERE / 'translate_refs.py'))
    run(module['run']({'sample': {'label': 'test', 'body': 'test'}}))
    assert calls == [{'timeout': 300}]
