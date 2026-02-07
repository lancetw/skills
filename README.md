# lancetw/skills

Custom skills for Claude Code, written in Taiwan Traditional Chinese.

## Skills

| Skill | Description |
|-------|-------------|
| **learn-tw** | Generate personalized learning docs (`FOR[name].md`) explaining a project in plain Taiwan Chinese |
| **prd-tw** | Help non-technical stakeholders write clear requirements documents in Taiwan Chinese |

## Installation

### Install all skills globally (recommended)

```bash
npx skills add lancetw/skills -g -a claude-code -y
```

### Install a specific skill

```bash
# learn-tw only
npx skills add lancetw/skills -g -a claude-code -s learn-tw -y

# prd-tw only
npx skills add lancetw/skills -g -a claude-code -s prd-tw -y
```

### Install to current project only (not global)

```bash
npx skills add lancetw/skills -a claude-code -y
```

### Browse available skills first

```bash
npx skills add lancetw/skills -l
```

## Usage

After installation, use the skills in Claude Code:

```
/learn-tw     # Generate a learning document for the current project
/prd-tw       # Create a requirements document
```

## License

Proprietary
