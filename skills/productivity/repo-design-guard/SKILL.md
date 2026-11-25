---
name: repo-design-guard
description: Install a design-system guard in a repo so Agents use its design system properly — a DESIGN.md stating the token roles, machine checks that fail on misuse, and a review skill that scores a screen against the rules. Use when the user asks to make Agents follow a repo's design system, add a DESIGN.md, enforce design tokens or component rules in CI, or list which repos still lack a guard (「幫這個 repo 加 design system 守門」「讓 Agent 照 design system 寫 UI」「加 DESIGN.md」「哪些 repo 還沒有 DESIGN.md」).
license: MIT
---

# Repo Design Guard

An Agent follows a design system when misuse turns a check red, not when a document asks it nicely. This skill installs three layers, from the one that decides to the one that advises:

```
1. Machine checks   lint, types, a small script     red on misuse, run in CI     decides
2. DESIGN.md        token roles, which check guards what                        tells
3. Review skill     scores a screen against DESIGN.md out of 10                  advises
```

Two words carry the rest of this file:

- **Rule**: one thing the design system forbids or requires, such as "no color written outside the token file", "components imported from their entries", "every control named".
- **Gate**: the command that turns red when a rule is broken, run by an existing CI job.

## 1. Probe

1. `<repo>`: the last path part of `git remote get-url origin`, without `.git`. No remote → the folder holding `git rev-parse --git-common-dir`.
2. Read the repo's `AGENTS.md` / `CLAUDE.md` (root and the UI package), its lint docs and its merge rules first: they decide which paths a change may touch, whether a new dependency is allowed, and which CI job names are fixed.
3. Find, and name with their paths:
   - **Token source**: a tokens file (`tokens.css`, a theme config, `tokens.json`), a prototype the tokens were lifted from, or an existing `DESIGN.md` / `design.md`.
   - **Styling**: plain CSS with custom properties, CSS Modules, Tailwind (which major version), CSS-in-JS.
   - **Component library**: `@ui-sdk/*` (vercel-labs/ui), shadcn/ui, a house library, none.
   - **Linter and type check**: the commands `package.json` runs for them, and which files each reads. A JS linter does not read `.css`.
   - **CI**: the job that runs lint, and whether its name is load-bearing (a merge script that requires jobs by name).
4. Existing guard: a `DESIGN.md`, a `.claude/skills/design-review*`, or a token check script. Another branch or worktree named after this task means another Agent may be on it: ask before going on.

Done when you can name the token source, the styling, the component library, the lint and type commands, and the CI job that will carry a new gate. Then: no guard → 2, a list of repos → 5.

## 2. Find what is already red

List the rules this repo's design system has: from its docs, from the component library's own skill, and these defaults:

- Colors, type sizes and spacing come from tokens, picked by role.
- Components come from the library's public entries; no internal paths.
- No hand-made widget where the library ships one (`role="listbox"`, `"menu"`, `"dialog"` on a `div`).
- Every control has a name; list keys are values or ids, not indexes.
- State is styled from state attributes, not inline styles.

Then prove which are already gated. Make a throwaway copy (`git worktree add --detach "$(mktemp -d)/probe" HEAD`, install its dependencies there), plant one violation per rule, each in its own file written to pass every other rule of the house lint, and run the repo's lint and type check on it. A violation that fails only on an unrelated rule proves nothing: rewrite it until the only error is the rule under test, or none. Remove the copy with `git worktree remove --force` afterwards.

Record a table: rule, gate that already catches it (with the error it prints), or "none". Only the "none" rows get a new check. Strict TypeScript and an every-category linter often catch most component rules already; CSS is the usual gap, because JS linters never read it.

## 3. Write the guard

Work in a worktree of the target repo, on a branch named after the task, based on the remote's tip of its integration branch.

### Machine checks, for each "none" row

Use what the repo already runs, in this order:

1. **A rule of its existing linter**, configured in its config file, with the reason beside it as the repo does.
2. **A linter built for it, when the stack fits and the repo allows a new dependency**: `@shadcn/lint` for Tailwind v4 (ESLint or Oxlint; contracts per component, no arbitrary values). Install it through the repo's dependency policy.
3. **A small script in the repo's own script style** (a shell `scripts/check-*.sh` beside its others, or the language its scripts use) for what no linter reads, typically colors written outside the token file. Count literals in declaration values only: strip comments first, so neither a comment nor a selector such as `:hover` or `#id` counts.

Wire each new check into the command the existing lint job runs (`"lint": "<linter> && bash scripts/check-tokens.sh"`), never into a new CI job, so job names a merge rule requires stay as they are. When the repo tests its scripts in CI, add the script's test and lint (`shellcheck`) to that job's list.

**Existing violations**: a new check usually starts red. Do not rewrite the screens in this change. Record a baseline (each file's count) that the check must match exactly: a new violation fails, a removed one fails until the baseline is lowered, so it never goes loose. Note in the script: `shortcut: counts literals, so swapping one literal for another passes`.

Give each script a test that runs it on a throwaway folder: green when counts match, red on a new literal, red on a stale baseline, blind to comments, selectors and the token file.

### DESIGN.md

At the root of the UI package (the path its merge rule allows), in the [DESIGN.md format](https://github.com/google-labs-code/design.md) (alpha: YAML front matter, markdown body).

- **A token file or prototype already holds the values** → front matter has `name` and `description` only; the body names those files as the source and never copies a value, which would drift.
- **No token source, Tailwind or a DTCG pipeline** → DESIGN.md is the source: tokens in its front matter, written out with `npx -p @google/design.md designmd export --format css-tailwind|json-tailwind|dtcg DESIGN.md` (the dot-free `designmd` alias; the CLI has no plain-CSS format).
- **No token source, plain CSS** → write the custom properties into one token stylesheet first, then treat it as the case above.

Body, about forty lines: tokens grouped by role with what each group is for, and the line "pick a token by its role, not by its value"; how components take the look (the library's styling hook, the layer order); a table of each rule and the gate that enforces it, including the rules that only a reviewer can judge. Do not restate decisions already written in `AGENTS.md` / `CLAUDE.md`: point to them. Every fact in it comes from the repo; leave out what you cannot point to.

### Component library skill

`@ui-sdk/*` installed and its skill absent → `npx skills add vercel-labs/ui --skill ui-sdk`; it reads the docs shipped inside the installed package, so it matches the pinned version. Do not copy its rules into DESIGN.md. Respect the repo's opt-outs: a repo that forbids the library's agent features keeps them out of shipped code and out of the gates.

### Review skill

`.claude/skills/design-review-<repo>/SKILL.md`, frontmatter `name: design-review-<repo>` and a double-quoted `description`. Sections:

- **Gate**: run the lint and type commands first; red → fix before any score.
- **Look**: read DESIGN.md; see the changed screen (pictures from the repo's verify skill, or its preview build in a browser tool); open the same view in the prototype when there is one.
- **Score**: 0 to 10 per line (tokens by role, hierarchy, spacing rhythm, states, text), each point off with its evidence. Overall is the lowest line, not the average.
- **Report**: overall score, the table, "matches" and "to fix" with file and selector. The score is advice and gates nothing.

## 4. Prove it: green, then red

1. **Green**: in the worktree, the full lint and type commands exit 0, and each new script's test passes.
2. **Red**, once per new check: in a throwaway copy that carries the change, plant one violation the check covers (a color literal in a stylesheet) and run the lint command. It must exit non-zero with the new check's own message. A failure from another rule does not count.
3. For each rule an existing gate already covered (section 2), the probe's output is the red evidence.

Done when every rule in the table has a red run, each with the command and its output.

## 5. Take stock across repos

Ask which parent folder to scan, unless the user named one. With the Agent's own file tools, list every direct child folder holding `.git`, and for each: a `DESIGN.md` (anywhere above `node_modules`), a `.claude/skills/design-review*`, and the styling you would guess from its `package.json`. Reply with a table; build nothing; offer section 1 on the repo the user picks.

## 6. Hand off

Reply in the user's language with: the rule table (rule, gate, red evidence), the files written, the baseline's total and the largest files in it, and what is left to a reviewer. Commit on the branch the way the repo's `AGENTS.md` / `CLAUDE.md` asks, one commit per merge boundary: files outside the path a merge rule allows (a root `.claude/skills/`) go in their own commit and are flagged for a person's merge request. Pushing, opening the merge request and changing the lint gate under other open branches are the user's call.
