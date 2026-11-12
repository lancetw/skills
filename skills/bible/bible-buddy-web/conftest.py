"""Fixtures shared by test_server.py and test_codex_backend.py."""

import pytest
import server

VERSES = [
    {"verse": "4", "text": "上帝看光是好的，於是上帝就把光和暗分開。", "footnotes": [], "cuts": []},
    {"verse": "5", "text": "上帝稱光為晝，稱暗為夜。", "footnotes": [], "cuts": []},
]


@pytest.fixture
def desk(tmp_path, monkeypatch):
    """A passage on screen and an empty notes directory, with nothing left over between tests."""
    monkeypatch.setattr(server, "NOTES_DIR", tmp_path / "notes")
    server.passage.update(
        reference="創世記 1:4-5", version="rcuv", book="創世記", verses=[dict(v) for v in VERSES]
    )
    server.notes.clear()
    server.hidden.clear()
    server._passes.clear()
    yield tmp_path / "notes"
    server.notes.clear()
    server.hidden.clear()
