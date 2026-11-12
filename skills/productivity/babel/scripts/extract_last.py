#!/usr/bin/env python3
"""Extract the previous assistant response from the current Claude Code session.

Reads the newest .jsonl transcript in ~/.claude/projects/<sanitized-cwd>/,
finds the last real user message, then walks backwards to the assistant's final
visible answer — the trailing run of text after the last tool call, as the user
reads it, not the whole tool-driven turn's interim narration. Prints it verbatim
to stdout. See extract_last_response for the boundary rule.

Stdlib only. No __init__.py needed (skills install rule).
"""
import json
import os
import re
import sys


def transcript_dir():
    sanitized = re.sub(r"[^A-Za-z0-9]", "-", os.getcwd())
    return os.path.join(os.path.expanduser("~/.claude/projects"), sanitized)


UUID_JSONL = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl$"
)


def newest_jsonl(d):
    """Newest main-session transcript. Main sessions are UUID-named; agent/fork
    transcripts use other names and must not be picked up."""
    files = [os.path.join(d, f) for f in os.listdir(d) if UUID_JSONL.fullmatch(f)]
    if not files:
        files = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".jsonl")]
    return max(files, key=os.path.getmtime) if files else None


def is_real_user(entry):
    """A message the human actually typed — not a tool_result, not meta."""
    if entry.get("type") != "user" or entry.get("isSidechain") or entry.get("isMeta"):
        return False
    content = entry.get("message", {}).get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        has_text = any(b.get("type") == "text" for b in content if isinstance(b, dict))
        has_tool_result = any(
            b.get("type") == "tool_result" for b in content if isinstance(b, dict)
        )
        return has_text and not has_tool_result
    return False


def assistant_text(entry):
    if entry.get("type") != "assistant" or entry.get("isSidechain"):
        return None
    content = entry.get("message", {}).get("content", [])
    texts = [
        b.get("text", "")
        for b in content
        if isinstance(b, dict) and b.get("type") == "text"
    ]
    joined = "\n\n".join(t for t in texts if t.strip())
    return joined or None


def has_tool_use(entry):
    """True if an assistant entry called a tool. Marks the boundary between the
    final visible answer and the tool-driven work that preceded it."""
    if entry.get("type") != "assistant" or entry.get("isSidechain"):
        return False
    content = entry.get("message", {}).get("content", [])
    return any(
        isinstance(b, dict) and b.get("type") == "tool_use" for b in content
    )


def session_jsonl(d):
    """Exact main-session transcript via CLAUDE_CODE_SESSION_ID (set in skill
    Bash env, and inside a context:fork subagent it still names the MAIN
    session). Fallback: newest UUID-named jsonl — fragile once nested CLI
    sessions (e.g. the claude backend's own `claude -p`) land in the same dir."""
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if sid:
        p = os.path.join(d, sid + ".jsonl")
        if os.path.isfile(p):
            return p
    return newest_jsonl(d)


def extract_last_response(entries):
    """The assistant's final visible answer, as the user reads it — not the whole
    turn. Returns the joined text, or None if no response precedes the last user
    message.

    A tool-driven turn emits many interim text blocks ("Let me check X")
    interleaved with tool calls; only the trailing run of text *after the last
    tool_use* is the answer. Walking backwards from the last real user message we
    collect assistant text and stop at the first tool_use (or the user prompt
    that started the turn), so interim narration never leaks into the output.
    """
    last_user = next(
        (i for i in range(len(entries) - 1, -1, -1) if is_real_user(entries[i])), None
    )
    if last_user is None:
        return None

    collected = []
    for i in range(last_user - 1, -1, -1):
        entry = entries[i]
        if has_tool_use(entry):
            if collected:
                break
            continue  # trailing tool call with no answer yet — keep looking back
        text = assistant_text(entry)
        if text:
            collected.append(text)
        elif collected and is_real_user(entry):
            break
    return "\n\n".join(reversed(collected)) if collected else None


def main():
    d = transcript_dir()
    if not os.path.isdir(d):
        sys.exit(f"transcript dir not found: {d}")
    path = session_jsonl(d)
    if not path:
        sys.exit(f"no .jsonl transcript in {d}")

    with open(path, encoding="utf-8") as f:
        entries = []
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    result = extract_last_response(entries)
    if result is None:
        sys.exit("no previous assistant response found")

    print(result)


if __name__ == "__main__":
    main()
