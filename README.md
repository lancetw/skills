# lancetw/skills

Taiwan Traditional Chinese (繁體中文) skills for AI coding agents.

## Skills

| Skill | Description | Output |
|-------|-------------|--------|
| **learn-tw** | Generate personalized learning docs explaining a project in plain Taiwan Chinese | `FOR[yourname].md` |
| **prd-tw** | Help non-technical stakeholders write clear requirements documents in Taiwan Chinese | `REQUIREMENTS.md` |

---

## Installation

### Install globally (recommended)

```bash
npx skills add lancetw/skills -g
```

### Install a specific skill only

```bash
npx skills add lancetw/skills -g -s learn-tw
```

### Install to current project only (not global)

Omit the `-g` flag to install project-level only:

```bash
npx skills add lancetw/skills
```

### Browse available skills before installing

```bash
npx skills add lancetw/skills -l
```

---

## Usage

### learn-tw

After installation, invoke in your agent:

```
/learn-tw
```

Explores the current codebase and generates a `FOR[yourname].md` file in the project root. The document covers:

- Project overview, architecture, and codebase structure
- Technology choices and why they were picked
- Design decisions and trade-offs
- Lessons learned, pitfalls, and best practices
- Engineering mindset and debugging approaches

All written in engaging, plain Taiwan Traditional Chinese with proper terminology (e.g. 程式碼, 資料庫, 伺服器).

### prd-tw

```
/prd-tw
```

Guides you through writing a requirements document (PRD) in Taiwan Traditional Chinese. Designed for non-technical stakeholders — no jargon, focus on **what** not **how**.

The generated document includes:

- Purpose and core requirements with user goals
- User workflow scenarios (step-by-step)
- Explicit out-of-scope items
- Measurable success criteria

Output is saved as `REQUIREMENTS.md` or `[功能名稱]_需求文件.md`.

---

## Management

```bash
# List installed skills
npx skills ls -g

# Check for updates
npx skills check

# Update all skills
npx skills update

# Remove a skill
npx skills remove -g learn-tw
```

## License

MIT
