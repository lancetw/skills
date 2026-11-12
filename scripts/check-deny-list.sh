#!/usr/bin/env bash
set -euo pipefail

# Fail when a file (or, at the commit-msg stage, the commit message) contains a term from the local
# deny-list: employer, customer or project names that came in through a prompt or a pasted notice
# and must not ship in this public repo.
#
# The list is local and untracked, because a tracked list would itself leak the names. One literal
# term per line:
#   $(git rev-parse --git-common-dir)/info/deny.txt
# No list, nothing to check.

LIST="$(git rev-parse --git-common-dir)/info/deny.txt"
[ -s "$LIST" ] || exit 0
[ "$#" -gt 0 ] || exit 0

if grep -n -H -i -F -f "$LIST" -- "$@"; then
  echo "Deny-listed name found (list: $LIST). Use a generic placeholder such as <customer>." >&2
  exit 1
fi
