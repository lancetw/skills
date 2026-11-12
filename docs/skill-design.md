# Writing and Changing a Skill

Read before editing anything under `skills/`. The mechanical rules are pre-commit hooks (`.pre-commit-config.yaml`); this page holds the judgement calls.

## Layout

- A skill lives at `skills/<category>/<name>/`. After adding, moving or removing one, run `./scripts/gen-plugin-manifest.sh` and commit `.claude-plugin/plugin.json` with it.
- Not ready to ship → `metadata: {internal: true}` in the SKILL.md frontmatter. A folder name alone hides nothing: `npx skills` finds every `SKILL.md` recursively.
- Retire a skill by deleting it; git history keeps it.
- bible-buddy-web finds bible-buddy as a sibling directory (`corpus.skill_path`, the tracked `.claude/skills/bible-buddy` link): keep both in the same category.

## Editing

- A skill that runs only when typed sets `disable-model-invocation: true` in SKILL.md and `policy.allow_implicit_invocation: false` in `agents/openai.yaml` (the `codex-policy` hook).
- Skill files, tests and commit messages stay generic: employer, customer and project names from prompts go in `.git/info/deny.txt` (the `deny-list` hook).
- Format before staging, at the pre-commit rev: `uvx ruff@0.17.2 format <files> && uvx ruff@0.17.2 check --fix <files>`. Otherwise the ruff-format hook rewrites the file and aborts the commit.
- `ruff check --fix` drops an imported pytest fixture as unused: share fixtures through `conftest.py`, never by import.
- Tests: `./scripts/test-skills.sh [skills/<cat>/<skill> ...]`. Run `pre-commit install` once per clone; it adds the commit-msg and pre-push hooks.

## Installed copies

- The skill an agent runs is `~/.agents/skills/<name>`, installed from GitHub by `npx skills add|update -g`, not this checkout. Local commits reach it after push and `npx skills update <name> -g`.
- The install lock (`~/.agents/.skill-lock.json`) records each skill's path in the repo. Moving a skill makes `npx skills update` report it as "deleted upstream" and skip it; re-add it once: `npx skills add lancetw/skills -g -s <name>`.
- Simulating a fresh install or update: `env -u CLAUDE_CONFIG_DIR HOME=$(mktemp -d) npx skills add -g <source>`. `CLAUDE_CONFIG_DIR` beats `HOME` for the Claude Code target, so leaving it set writes into your real `~/.claude/skills`.
