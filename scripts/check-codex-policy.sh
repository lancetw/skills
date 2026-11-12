#!/usr/bin/env bash
set -euo pipefail

# A skill that runs only when typed must say so to both Claude Code and Codex. Claude Code reads SKILL.md's
# `disable-model-invocation: true`; Codex ignores it and reads agents/openai.yaml's
# `policy.allow_implicit_invocation: false` instead (https://developers.openai.com/codex/skills,
# "Optional metadata"). With only the first, Codex picks the skill on its own.

bad=0
for skill in skills/*/*/SKILL.md; do
  dir="$(dirname "$skill")"
  claude=0 codex=0
  sed -n '2,/^---$/p' "$skill" | grep -Eq '^disable-model-invocation:[[:space:]]*true[[:space:]]*$' && claude=1
  [ -f "$dir/agents/openai.yaml" ] && grep -Eq '^[[:space:]]+allow_implicit_invocation:[[:space:]]*false[[:space:]]*$' "$dir/agents/openai.yaml" && codex=1
  if [ "$claude" != "$codex" ]; then
    if [ "$claude" = 1 ]; then
      echo "$dir: SKILL.md says disable-model-invocation: true, but agents/openai.yaml lacks policy.allow_implicit_invocation: false" >&2
    else
      echo "$dir: agents/openai.yaml says allow_implicit_invocation: false, but SKILL.md lacks disable-model-invocation: true" >&2
    fi
    bad=1
  fi
done
[ "$bad" = 0 ] || echo "Fix: give both agents the same rule (see the comment in scripts/check-codex-policy.sh)." >&2
exit "$bad"
