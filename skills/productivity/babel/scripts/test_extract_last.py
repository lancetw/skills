#!/usr/bin/env python3
"""Reproduces the bug: babel translated a tool-driven turn's interim narration
instead of the final answer. Run: python3 test_extract_last.py

Fixture mirrors a real transcript (ngs 3c14d91b): one long tool-driven turn with
several interim "let me check" text blocks, a final review block, then two
response-less slash commands (/reload-skills, /babel). The extractor must return
ONLY the final block.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_last import extract_last_response  # noqa: E402


def _user(text):
    return {"type": "user", "message": {"content": text}}


def _cmd(name):  # slash command as recorded: real user, no assistant response
    return {"type": "user", "message": {"content": f"<command-name>/{name}</command-name>"}}


def _caveat():
    return {"type": "user", "isMeta": True, "message": {"content": "<local-command-caveat>..."}}


def _asst_text(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def _asst_tool():
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "x", "name": "Bash", "input": {}}]}}


def _tool_result():  # type "user" but NOT real input
    return {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}


FINAL = "## Thermo-Nuclear Review\n\nThe change looks correct."
INTERIM = "I'll start by understanding the scope of changes on this branch."


def tool_driven_turn():
    """Original user prompt, a turn with interim narration + final answer, then
    two response-less slash commands, then /babel."""
    return [
        _user("review this branch"),
        _asst_text(INTERIM),
        _asst_tool(),
        _tool_result(),
        _asst_text("Now let me read the actual code diff."),
        _asst_tool(),
        _tool_result(),
        _asst_text("The hook is reused elsewhere. Let me confirm."),
        _asst_tool(),
        _tool_result(),
        _asst_text(FINAL),
        _cmd("reload-skills"),  # no assistant response follows
        _caveat(),
        _cmd("babel"),
    ]


def combined_text_and_tool_entry():
    """Rare: interim narration text lives in the SAME entry as its tool_use."""
    return [
        _user("do the thing"),
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Let me run it."},
            {"type": "tool_use", "id": "x", "name": "Bash", "input": {}},
        ]}},
        _tool_result(),
        _asst_text("Done — all green."),
        _cmd("babel"),
    ]


def simple_no_tool_turn():
    return [
        _user("what is 2+2?"),
        _asst_text("It is 4."),
        _cmd("babel"),
    ]


def split_final_answer():
    """Final answer streamed as two consecutive text entries, no tool between."""
    return [
        _user("explain"),
        _asst_text("first, some background."),
        _asst_tool(),
        _tool_result(),
        _asst_text("Part A of the answer."),
        _asst_text("Part B of the answer."),
        _cmd("babel"),
    ]


def demo():
    r = extract_last_response(tool_driven_turn())
    assert r == FINAL, f"expected only the final block, got:\n{r!r}"
    assert INTERIM not in r, "interim narration leaked into the translation source"

    r = extract_last_response(combined_text_and_tool_entry())
    assert r == "Done — all green.", r
    assert "Let me run it." not in r

    assert extract_last_response(simple_no_tool_turn()) == "It is 4."

    assert extract_last_response(split_final_answer()) == (
        "Part A of the answer.\n\nPart B of the answer."
    )

    assert extract_last_response([_cmd("babel")]) is None  # nothing precedes it

    print("all checks passed")


if __name__ == "__main__":
    demo()
