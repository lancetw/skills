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
2. Read the repo's `AGENTS.md` / `CLAUDE.md` (root and the UI package), its lint docs, its merge rules and wherever else it keeps rules (a contributing guide, a project constitution, the pre-commit config) first: they decide which paths a change may touch, whether a new dependency is allowed, and which CI job names are fixed.
3. Find, and name with their paths:
   - **Token source**: a tokens file (`tokens.css`, a theme config, `tokens.json`), a prototype the tokens were lifted from, or an existing `DESIGN.md` / `design.md`.
   - **Styling**: plain CSS with custom properties, CSS Modules, Tailwind (which major version), CSS-in-JS.
   - **Component library**: `@ui-sdk/*` (vercel-labs/ui), shadcn/ui, a house library, none.
   - **Linter and type check**: the commands `package.json` runs for them, and which files each reads. A JS linter does not read `.css`.
   - **CI**: every job a merge requires (lint, format, type check, tests are common), the image each runs in, and whether job names are load-bearing (a merge script that requires jobs by name). Also the pre-commit hooks: they often run the linter per file rather than the lint script. No CI job runs the linter → the carriers are the pre-commit hooks and the lint script, and the hand-off says the gate runs only where those run.
   - **Package manager**: the version the repo pins (`packageManager`, its Dockerfile, its CI image). Another version rewrites the lockfile.
4. Existing guard: a `DESIGN.md`, a `.claude/skills/design-review*`, or a token check script. Another branch or worktree named after this task means another Agent may be on it: ask before going on; with no one to ask, stop and report it.
5. **UI folder**: the folder holding the UI's `package.json`. Every file below goes there unless the merge rule allows more.

Done when you can name the token source, the styling, the component library, the lint and type commands, and what will carry a new gate (a CI job, else the hooks and the lint script). Then: no guard → 2, a list of repos → 5.

## 2. Find what is already red

List the rules this repo's design system has: from its docs, from the component library's own skill, and these defaults:

- Colors, type sizes and spacing come from tokens, picked by role.
- Components come from the library's public entries; no internal paths.
- No hand-made widget where the library ships one (`role="listbox"`, `"menu"`, `"dialog"` on a `div`).
- Every control has a name; list keys are values or ids, not indexes.
- Any design rule the repo's own docs state (a forbidden prop, a focus-ring color, a library feature the repo turns off).
- State is styled from state attributes, not inline styles.

Then prove which are already gated, one case per value where a rule lists several: each widget role on its own, since a linter that flags `role="listbox"` may let `role="menu"` through. The roles are those of the components the library ships (for shadcn/ui on Radix add `checkbox`); for UI SDK: listbox, menu, menubar, menuitem, dialog, alertdialog, combobox, tablist, tab, switch, slider, radiogroup, tooltip, tree, toolbar, option, progressbar, meter, separator. Make a throwaway copy on the base section 3 uses (`git worktree add --detach "$(mktemp -d)/probe" origin/<integration branch>`, install its dependencies there), plant one violation per rule, each in its own file written to pass every other rule of the house lint, and run the repo's lint and type check on it. Pass the linter the probe files by path: a quoted glob reaches it unexpanded and matches nothing. Judge every command by its exit code, not its output: a repo's git hooks may print errors during `git worktree add` and still exit 0. A violation that fails only on an unrelated rule proves nothing (a `role="switch"` that fails for a missing `aria-checked` passes once the attribute is added): rewrite it until the only error is the rule under test, or none. Remove the copy with `git worktree remove --force` afterwards.

Record a table: rule, gate that already catches it (with the command and the error it prints), or "none". A rule the linter only warns about, in a lint command that passes on warnings, is "none". Only the "none" rows get a new check. Strict TypeScript and an every-category linter often catch most component rules already; CSS is the usual gap, because JS linters never read it.

## 3. Write the guard

Work in a worktree of the target repo, on a branch named after the task, based on the remote's tip of its integration branch.

### Machine checks, for each "none" row

Use what the repo already runs, in this order:

1. **A rule of its existing linter**, configured in its config file, with the reason beside it as the repo does.
2. **A linter built for it, when the stack fits and the repo allows a new dependency**: `@shadcn/lint` for Tailwind v4 (ESLint or Oxlint). Its rules: `no-restyle` (contracts per component), `no-raw-colors` (palette classes and color literals in JSX attributes), `no-arbitrary-values`, `no-inline-styles`, `no-unknown-classes`, `require-static-classes`; `settings.shadcn.note` appends a line (a pointer to DESIGN.md) to every message. Install it through the repo's dependency policy, with the pinned package manager.
3. **A small script in the repo's own script style** (a shell `scripts/check-*.sh` beside its others, or the language its scripts use) for what no linter reads: colors written outside the token definitions, and widget roles the linter let through. When the token file also holds other styles, skip custom-property declarations (`--name: value`) instead of skipping the file. Colors hide in two places: stylesheet declarations (hex, functional notation, common named colors; strip comments first and count values only, so neither a comment nor a selector such as `:hover` or `#id` counts) and strings in code (an SVG `fill="#fff"`, a chart color constant). Roles are a `grep` over JSX for `role=` with the library's widget roles. Read the baseline with `tr -d '\r'`, since a Windows checkout may turn its line ends into CRLF, and let every failure message point to DESIGN.md.

The script takes the folder to read and the baseline file as arguments, so section 4 can run it against other branches. Wire each new check into the command the existing lint job runs (`"lint": "<linter> && bash scripts/check-tokens.sh"`), never into a new CI job, so job names a merge rule requires stay as they are. When the repo tests its scripts in CI, add the script's test and lint (`shellcheck`) to that job's list. Run the script once in the CI job's own image, or with no CI job the image the repo builds in (`docker run` with a copy of the UI folder): its shell, `awk`, `grep` and `find` may not be the ones on this machine (an Alpine image has no `bash`, and its `awk` reads escapes in bracket expressions differently). Where the repo's script style and that image disagree, the image wins: write POSIX `sh`.

**Existing violations**: a new check usually starts red. Do not rewrite the screens in this change. Record a baseline that the check must match exactly: a new violation fails, a removed one fails until the baseline is lowered, so it never goes loose. For a script: each file's count. For a linter rule: the linter's own suppression file when it has one (ESLint 9.24 or later: `eslint . --suppress-rule <rule>`, then `--prune-suppressions` after a removal). A generated baseline file goes into the formatter's ignore list, since the tool rewrites it unformatted. Note in the script: `shortcut: counts literals, so swapping one literal for another passes`.

Give each script a test that runs it on a throwaway folder: green when counts match, red on a new literal in a stylesheet and in a code string, red on a stale baseline, red on a hand-made role, blind to comments, selectors and the token file.

### DESIGN.md

At the root of the UI package (the path its merge rule allows), in the [DESIGN.md format](https://github.com/google-labs-code/design.md) (alpha: YAML front matter, markdown body).

- **A token file or prototype already holds the values** → front matter has `name`, `description` and `omitted`: one `{section, reason}` entry per token section the linter knows (`colors`, `typography`, `spacing`, `rounded`, `components`; it warns on `motion`), each with its true reason ("values live in <token file>", or "none exist"). The body names those files as the source and never copies a value, which would drift.
- **No token source, Tailwind or a DTCG pipeline** → DESIGN.md is the source: tokens in its front matter, written out with `designmd export --format css-tailwind|json-tailwind|dtcg|css-vars DESIGN.md` (the dot-free `designmd` alias; `css-vars` for plain CSS custom properties; check `designmd export --help` of the installed version).

Body, about sixty lines, in the section order the installed `designmd spec` prints, leaving out the sections the repo has nothing for: Overview (where the values live, as `@path` references resolved from DESIGN.md's folder, which may not leave it, and "pick a token by its role, not by its value"), Colors (token groups by role), Typography, Layout, Elevation & Depth, Shapes, Components (how components take the look: the library's styling hook, the layer order), Do's and Don'ts (each rule and the gate that enforces it, stating the gate's reach honestly: what it reads, what it skips, and the rules only a reviewer can judge). Check the file against the format with its linter: install `@google/design.md` into a temp folder through the machine's dependency guard and run `<temp>/node_modules/.bin/designmd lint DESIGN.md` (or `npx -p @google/design.md designmd lint DESIGN.md` where `npx` is allowed). Zero errors and zero warnings; then format it with the repo's formatter and lint it again. The linter does not check `@path` targets: confirm each exists. A repo convention that contradicts a rule you write (palette classes paired per theme where the rule asks for role tokens) is baselined, not fixed, and named in the hand-off. Do not restate decisions already written in `AGENTS.md` / `CLAUDE.md`: point to them. Every fact in it comes from the repo; leave out what you cannot point to.

### Component library skill

`@ui-sdk/*` installed → its skill ships inside the package (`node_modules/@ui-sdk/core/skills/ui-sdk/SKILL.md`), matching the pinned version: point to it from DESIGN.md's Components section. `npx skills add vercel-labs/ui --skill ui-sdk` fetches the latest version instead and writes outside the UI folder (`.agents/`, `skills-lock.json`); use it only when the repo wants it. Do not copy its rules into DESIGN.md. Respect the repo's opt-outs: a repo that forbids the library's agent features keeps them out of shipped code and out of the gates.

### Review skill

`.claude/skills/design-review-<repo>/SKILL.md` at the repo root (often outside the path a UI merge rule allows: its own commit), frontmatter `name: design-review-<repo>` and a double-quoted `description`. Sections:

- **Gate**: run the lint and type commands first; red → fix before any score.
- **Look**: read DESIGN.md; read the prototype's list of decided differences, if it keeps one; see the changed screen where every screen and state can be reached (the built app served the way the repo serves it, often its Dockerfile, with the exact build, serve and stop commands; confirm it renders, since a framework's preview server may serve an empty shell; with no backend, name the screens that cannot be reached); open the same view in the prototype, naming how (its URL parameters) and how to hide its own chrome. A verify skill's pictures rarely cover every screen and state: name what they show.
- **Score**: out of 10 per line (tokens by role, hierarchy, spacing rhythm, states, text), anchored: 10 is no difference outside the decided list (no prototype: no break of a DESIGN.md rule), each distinct difference costs one point with its evidence, a state the prototype lacks is unjudged. Overall is the lowest line, not the average.
- **Report**: overall score, the table, "matches", "to fix" with file and selector, and "not seen". The score is advice and gates nothing.

Run the review skill once yourself before the hand-off, as section 4 asks of the checks: a review skill nobody ran hides wrong paths and missing steps.

## 4. Prove it: green, then red

1. **Green**: in the worktree, every command the required CI jobs run exits 0 (lint, format, type check, tests), and each new script's test passes. A test that fails on the base commit too is not this change's: show that run and list it.
2. **Red**, once per new check and once per gate an existing rule relies on, each with the command that fails (a type check is not the lint command): in a throwaway copy that carries the change (commit first, or copy the changed files into a fresh worktree), plant one violation the check covers (a color literal in a stylesheet) and run the lint command. It must exit non-zero with the new check's own message. A failure from another rule does not count, and since the lint command chains the linter first (`&&`), the plant must pass the linter to reach the new check.
3. For each rule an existing gate already covered (section 2), the probe's output is the red evidence.
4. **Landing**: run the new checks, from this branch, against every other worktree and local branch of the repo, with this branch's baseline, reading each one read-only (`git archive <branch> <UI folder>` into a temp folder, or the worktree's own files). Each one that goes red is a branch the change would break on its next rebase: list them. The baseline is a snapshot of the base commit; regenerate it right before landing.

Done when every rule in the table has a red run with the command and its output, or is listed as a reviewer's rule with the reason no tool can see it.

## 5. Take stock across repos

Ask which parent folder to scan, unless the user named one. With the Agent's own file tools, list every direct child folder holding `.git`, folding worktrees into their repo (a `.git` file, not a folder, marks a worktree; `git rev-parse --git-common-dir` names its repo), and for each repo: a `DESIGN.md` (anywhere outside `node_modules` and `.git`), a `.claude/skills/design-review*`, and the styling you would guess from its `package.json`. Reply with a table; build nothing; offer section 1 on the repo the user picks.

## 6. Hand off

Reply in the user's language with: the rule table (rule, gate, red evidence), the files written, the baseline's total and the largest files in it, and what is left to a reviewer. Commit on the branch the way the repo's `AGENTS.md` / `CLAUDE.md` asks, one commit per merge boundary: files outside the path a merge rule allows (a root `.claude/skills/`) go in their own commit and are flagged for a person's merge request. Pushing, opening the merge request and changing the lint gate under other open branches are the user's call.
