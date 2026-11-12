# lancetw/skills

Taiwan Traditional Chinese (繁體中文) skills for AI coding agents.

## Skills

Skills live under `skills/<category>/<skill-name>/`. `npx skills` finds them recursively, so `-s <skill-name>` works whatever the category.

```
skills/
├── bible/          # Bible study: interpretation, devotionals, fact-check, web reader
├── knowledge/      # zh-TW learning docs, requirements docs, writing, planning unknowns
├── productivity/   # Daily tools: Markdown to HTML, translation, weather
├── app/            # app-*-fix sweeps: find, fix what is proven safe, list the rest
└── matt/           # Workflows built on Matt Pocock's skills
```

### Bible &nbsp;·&nbsp; `skills/bible/`

| Skill | Description |
|-------|-------------|
| [bible-buddy](skills/bible/bible-buddy/SKILL.md) | First-century Hebrew scripture interpretation from Yeshua's Jewish perspective |
| [bible-fact-check](skills/bible/bible-fact-check/SKILL.md) | 10-point quality checklist for biblical content review |
| [bible-bread](skills/bible/bible-bread/SKILL.md) | Daily devotional / QT guide with first-century Jewish pedagogy for mainstream Christians (requires bible-buddy) |
| [bible-buddy-web](skills/bible/bible-buddy-web/SKILL.md) | Prototype local web reader — passage on screen, ELI5 notes on the words, agent verification (requires bible-buddy) |

### Knowledge &nbsp;·&nbsp; `skills/knowledge/`

| Skill | Description |
|-------|-------------|
| [learn-tw](skills/knowledge/learn-tw/SKILL.md) | Generate personalized learning docs in Taiwan Traditional Chinese |
| [prd-tw](skills/knowledge/prd-tw/SKILL.md) | Help non-technical stakeholders write clear requirements documents in Taiwan Traditional Chinese |
| [humanizer-zh-tw](skills/knowledge/humanizer-zh-tw/SKILL.md) | Remove AI-generated traces from Chinese text |
| [know-your-unknowns](skills/knowledge/know-your-unknowns/SKILL.md) | Surface unknowns as interactive HTML artifacts — 11 techniques for before, during, and after implementation |

### Productivity &nbsp;·&nbsp; `skills/productivity/`

| Skill | Description |
|-------|-------------|
| [markdown-to-html](skills/productivity/markdown-to-html/SKILL.md) | Convert any Markdown file into a styled, readable HTML page for long-form Traditional Chinese reading |
| [babel](skills/productivity/babel/SKILL.md) | Translate Claude's previous response via an external CLI model (codex / agy / claude) in a forked context |
| [weather-hint-tw](skills/productivity/weather-hint-tw/SKILL.md) | Friendly weather reminders with outfit advice, auto IP detection |

### App &nbsp;·&nbsp; `skills/app/`

| Skill | Description |
|-------|-------------|
| [app-fresh-fix](skills/app/app-fresh-fix/SKILL.md) | Whole-project sweep after a new model release: fix what is proven broken, inconsistent, inefficient or unneeded; list the rest |
| [app-state-fix](skills/app/app-state-fix/SKILL.md) | Find implicit state machines, make the safe ones explicit without behavior change, list impossible states for review |
| [app-device-fix](skills/app/app-device-fix/SKILL.md) | Browser sweep across widths, touch and throttled 3G; fix what breaks with before/after screenshots |
| [app-unwaterfall-fix](skills/app/app-unwaterfall-fix/SKILL.md) | Make independent awaits on hot paths concurrent, pinned by tests; list unsure or ordering-sensitive ones for review |

### Matt &nbsp;·&nbsp; `skills/matt/`

| Skill | Description |
|-------|-------------|
| [improve-loop](skills/matt/improve-loop/SKILL.md) | Autonomous-safe architecture deepening loop: one behavior-preserving change per run, test-first on a `wt` branch, never merges |

See each skill's `SKILL.md` for details.

## Installation

```bash
# Install globally (recommended)
npx skills add lancetw/skills -g

# Install a specific skill only
npx skills add lancetw/skills -g -s learn-tw

# Install to current project only
npx skills add lancetw/skills

# Browse available skills
npx skills add lancetw/skills -l
```

## Management

```bash
npx skills ls -g           # List installed skills
npx skills check           # Check for updates
npx skills update          # Update all skills
npx skills remove -g learn-tw  # Remove a skill
```

## Development

Read [docs/skill-design.md](docs/skill-design.md) before changing a skill. Once per clone:

```bash
pre-commit install   # ruff, bandit, shellcheck, conventional commits, manifest sync; tests on push
./scripts/test-skills.sh
```

`.claude-plugin/plugin.json` groups the skills under one "Lancetw Skills" heading in the `npx skills add` menu. It is generated: after adding, moving or removing a skill, run `./scripts/gen-plugin-manifest.sh` and commit the result.

### Upgrading from the flat layout

Skills moved from `<name>/` to `skills/<category>/<name>/`. If you installed before the move, `npx skills update` reports your skills as "deleted upstream" and skips them; re-add them once:

```bash
npx skills add lancetw/skills -g -s <name>
```

## License

MIT
