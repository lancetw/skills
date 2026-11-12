#!/usr/bin/env bash
set -euo pipefail

# Fail when the ruff pre-commit runs is not the one pyproject.toml pins and uv.lock
# locks: two ruff versions format the same file differently, so each rewrites what
# the other just formatted.

hook="$(grep -A1 'astral-sh/ruff-pre-commit' .pre-commit-config.yaml | sed -n 's/.*rev: v\([^ ]*\).*/\1/p')"
pin="$(sed -n 's/.*"ruff==\([^"]*\)".*/\1/p' pyproject.toml)"
lock="$(grep -A1 '^name = "ruff"$' uv.lock | sed -n 's/^version = "\(.*\)"/\1/p')"
if [ -n "$hook" ] && [ "$hook" = "$pin" ] && [ "$pin" = "$lock" ]; then
  exit 0
fi
echo "ruff versions differ: pre-commit v${hook:-?}, pyproject.toml ==${pin:-?}, uv.lock ${lock:-?}." >&2
echo "Fix: pin one version in pyproject.toml, run uv lock, and set the same rev in .pre-commit-config.yaml." >&2
exit 1
