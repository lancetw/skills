
## Plan Mode

- Make the plan extremely concise. Sacrifice grammar for the sake of concision.
- At the end of each plan, give me a list of unresolved questions to answer, if any.
- Would a senior engineer say this is overcomplicated? If yes, simplify.
- When I report a bug, don't start by trying to fix it. Instead, start by writing a test that reproduces the bug. Then, have subagents try to fix the bug and prove it with a passing test.

## Python Import Rules

**CRITICAL**: `npx skills add` does NOT copy `__init__.py` files.

- ❌ `from core import Foo` — fails without `__init__.py`
- ✅ `from core.module import Foo` — works without `__init__.py`

Never create `__init__.py` in skill scripts directories.

## Pointers

- Writing or changing a skill: read `docs/skill-design.md` first.
- `.claude-plugin/plugin.json` is generated: run `./scripts/gen-plugin-manifest.sh` after adding, moving or removing a skill (`--check` reports drift).
