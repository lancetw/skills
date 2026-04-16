# lancetw/skills

Taiwan Traditional Chinese (繁體中文) skills for AI coding agents.

## Skills

| Skill | Description |
|-------|-------------|
| [learn-tw](learn-tw/SKILL.md) | Generate personalized learning docs in Taiwan Traditional Chinese |
| [prd-tw](prd-tw/SKILL.md) | Help non-technical stakeholders write clear requirements documents in Taiwan Traditional Chinese |
| [humanizer-zh-tw](humanizer-zh-tw/SKILL.md) | Remove AI-generated traces from Chinese text |
| [weather-hint-tw](weather-hint-tw/SKILL.md) | Friendly weather reminders with outfit advice, auto IP detection |
| [bible-buddy](bible-buddy/SKILL.md) | First-century Hebrew scripture interpretation from Yeshua's Jewish perspective |
| [bible-fact-check](bible-fact-check/SKILL.md) | 10-point quality checklist for biblical content review |
| [daily-bread](daily-bread/SKILL.md) | Daily devotional with first-century Jewish pedagogy for mainstream Christians (requires bible-buddy) |

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

## License

MIT
