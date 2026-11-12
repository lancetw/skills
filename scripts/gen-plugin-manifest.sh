#!/usr/bin/env bash
set -euo pipefail

# Generate .claude-plugin/plugin.json from the skills/ tree.
#
# `npx skills add lancetw/skills` reads `name` + `skills[]` from this manifest
# and shows every skill grouped under one "Lancetw Skills" heading.
#
# The file is GENERATED, never hand-edited. Re-run after adding/removing a skill:
#   ./scripts/gen-plugin-manifest.sh
# Verify it is in sync (pre-commit):
#   ./scripts/gen-plugin-manifest.sh --check   # exits non-zero if stale

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

PLUGIN_NAME="lancetw-skills"
PLUGIN_DESC="Taiwan Traditional Chinese (繁體中文) skills for AI coding agents — Bible study, zh-TW knowledge and writing, productivity and dev tools."
OUT=".claude-plugin/plugin.json"

MODE="write"
[ "${1:-}" = "--check" ] && MODE="check"
[ "$MODE" = "write" ] && mkdir -p "$(dirname "$OUT")"

# Prune vendored deps so find never descends into per-skill .venv trees.
find skills \
  \( -type d \( -name .venv -o -name node_modules -o -name .claude \) -prune \) \
  -o \( -type f -name SKILL.md -print \) \
| sed -e 's#/SKILL.md$##' -e 's#^#./#' \
| LC_ALL=C sort \
| MODE="$MODE" PLUGIN_NAME="$PLUGIN_NAME" PLUGIN_DESC="$PLUGIN_DESC" OUT="$OUT" python3 -c '
import json, os, sys
skills = [l.strip() for l in sys.stdin if l.strip()]
if not skills:
    sys.exit("error: no skills found under skills/")
data = {"name": os.environ["PLUGIN_NAME"], "description": os.environ["PLUGIN_DESC"], "skills": skills}
content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
out = os.environ["OUT"]
if os.environ["MODE"] == "check":
    try:
        current = open(out, encoding="utf-8").read()
    except FileNotFoundError:
        current = None
    if current != content:
        sys.exit("drift: %s is stale or missing — run ./scripts/gen-plugin-manifest.sh" % out)
    print("ok: %s is up to date (%d skills)" % (out, len(skills)))
else:
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    print("wrote %s with %d skills" % (out, len(skills)))
'
