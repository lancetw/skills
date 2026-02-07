# lancetw/skills

Taiwan Traditional Chinese (繁體中文) skills for AI coding agents.

## Skills

| Skill | Description |
|-------|-------------|
| [learn-tw](learn-tw/SKILL.md) | Generate personalized learning docs in Taiwan Chinese |
| [prd-tw](prd-tw/SKILL.md) | Help stakeholders write requirements documents in Taiwan Chinese |
| [humanizer-zh-tw](humanizer-zh-tw/SKILL.md) | Remove AI-generated traces from Chinese text |

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
