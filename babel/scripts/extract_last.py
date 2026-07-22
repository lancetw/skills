#!/usr/bin/env python3
"""Extract the previous assistant response from the current Claude Code session.

Reads the newest .jsonl transcript in ~/.claude/projects/<sanitized-cwd>/,
finds the last real user message, then walks backwards collecting the full
assistant text of the turn before it. Prints the verbatim text to stdout.

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

    last_user = next(
        (i for i in range(len(entries) - 1, -1, -1) if is_real_user(entries[i])), None
    )
    if last_user is None:
        sys.exit("no user message found in transcript")

    # Walk backwards from the last user message: skip noise (tool results,
    # system entries, local-command output) until the first assistant text,
    # then collect the whole turn, stopping at the user prompt that started it.
    collected = []
    for i in range(last_user - 1, -1, -1):
        text = assistant_text(entries[i])
        if text:
            collected.append(text)
        elif collected and is_real_user(entries[i]):
            break
    if not collected:
        sys.exit("no previous assistant response found")

    print("\n\n".join(reversed(collected)))


if __name__ == "__main__":
    main()
