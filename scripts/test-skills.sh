#!/usr/bin/env bash
set -euo pipefail

# Run each skill's tests: pytest where it has test_*.py files (in its own uv project when it has a
# pyproject.toml), and node --test for *.test.mjs. Only the skills named as arguments, if any.
#   ./scripts/test-skills.sh                              # all skills
#   ./scripts/test-skills.sh skills/bible/bible-buddy-web
#   ./scripts/test-skills.sh skills/bible/bible-buddy-web -- -k anchor   # pytest options after --
# Pre-push runs it on the skills changed since the upstream branch (or origin/main).

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

dirs=()
pytest_args=()
while [ "$#" -gt 0 ]; do
  if [ "$1" = "--" ]; then
    shift
    pytest_args=("$@")
    break
  fi
  [ -d "$1" ] || { echo "not a skill folder: $1 (pytest options go after --)" >&2; exit 2; }
  dirs+=("$1")
  shift
done

if [ "${#dirs[@]}" -eq 0 ] && [ "${PRE_COMMIT:-}" = 1 ]; then
  base="$(git rev-parse -q --verify '@{u}' || git rev-parse -q --verify origin/main || true)"
  [ -n "$base" ] || { echo "no upstream to diff against; run ./scripts/test-skills.sh by hand" >&2; exit 0; }
  while IFS= read -r d; do [ -d "$d" ] && dirs+=("$d"); done < <(
    git diff --name-only "$base"...HEAD -- skills | cut -d/ -f1-3 | sort -u
  )
elif [ "${#dirs[@]}" -eq 0 ]; then
  dirs=(skills/*/*)
fi

# A git hook (pre-push) exports these; left in, a test's `git` would act on this repo instead of
# its own fixture repo. Cleared after the diff above.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES \
  GIT_COMMON_DIR GIT_PREFIX GIT_NAMESPACE GIT_QUARANTINE_PATH

failed=()
# ${a[@]+"${a[@]}"}: macOS bash 3.2 with set -u rejects an empty "${a[@]}".
for d in ${dirs[@]+"${dirs[@]}"}; do
  py_tests="$(find "$d" \( -name .venv -o -name node_modules \) -prune -o -name 'test_*.py' -print -quit)"
  js_tests="$(find "$d" \( -name .venv -o -name node_modules \) -prune -o -name '*.test.mjs' -print -quit)"
  [ -n "$py_tests$js_tests" ] || continue
  echo "== $d"
  if [ -n "$py_tests" ]; then
    project=(--no-project)
    [ -f "$d/pyproject.toml" ] && project=()
    (cd "$d" && command uv run ${project[@]+"${project[@]}"} --with pytest pytest -q ${pytest_args[@]+"${pytest_args[@]}"}) || failed+=("$d")
  fi
  if [ -n "$js_tests" ]; then
    (cd "$d" && find . \( -name .venv -o -name node_modules \) -prune -o -name '*.test.mjs' -print0 | xargs -0 node --test) || failed+=("$d")
  fi
done

if [ "${#failed[@]}" -gt 0 ]; then
  printf 'tests failed: %s\n' "${failed[@]}" >&2
  exit 1
fi
