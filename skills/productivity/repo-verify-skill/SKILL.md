---
name: repo-verify-skill
description: Build, tune or take stock of a repo's verify skill — the smoke test an Agent runs to prove a change works the way its user meets it, before calling the change done. Use when the user asks to add a verify skill to a repo, to make an existing one faster or steadier, or to list which repos still lack one (「幫這個 repo 建 verify skill」「verify 太慢／不穩」「哪些 repo 還沒有 verify」).
license: MIT
---

# Repo Verify Skill

A verify skill lives in the repo it checks, at `.claude/skills/verify-<repo>/SKILL.md`, so every clone, every machine and every Agent gets it with `git pull`. It drives the real thing: it launches the app, service or CLI, walks the flows its user walks, and judges each by evidence. Green unit tests alone leave a change unverified; the verify skill is what turns "the tests pass" into "it works".

Two words carry the rest of this file:

- **Surface**: where the repo's user meets a change. A CLI's output, an HTTP response, a page in a browser, a file the tool writes.
- **Red**: the verify skill fails, and names what broke, when a flow it covers is broken. A verify skill that stays green on a broken change proves nothing.

## 1. Probe

1. Repo root: `git rev-parse --show-toplevel`. `<repo>` is that folder's name.
2. Existing verify skills: any `.claude/skills/verify*/SKILL.md` under the root. A branch or worktree whose name contains `verify` (`git branch -a`, `git worktree list`) means another Agent may already be on it: ask the user before going on.
3. The surface and how to reach it, from what the repo already says: README, `package.json` scripts, `pyproject.toml`, `Makefile`, `.gitlab-ci.yml`, any e2e tests, `AGENTS.md` / `CLAUDE.md`.
4. What this machine can drive the surface with: the CLI itself, `curl` for HTTP, a browser-automation tool only when one is installed and answers. Without one, a web app is driven through its HTTP API when it has one.

Done when you can name the surface, the launch command, the ready signal (a log line, a port answering, a file appearing) and the drive tool. Then go to the section for the request: none exists → 2, one exists → 3, a list of repos → 5.

## 2. Write a new verify skill

Write `.claude/skills/verify-<repo>/SKILL.md`. Its frontmatter `description` says what it proves and when to run it: "Prove a change to <repo> works the way its user meets it: <surface>. Use before calling a change done, or when asked to verify or smoke test." Its body has these sections, each ending on a condition the Agent can check:

- **Launch**: the commands from a clean checkout to a running surface, and the ready signal. Dependencies install here.
- **Drive**: one to three flows the user actually walks, taken from the README, the CI's e2e jobs or the feature list. Each flow is: action → expected result on the surface.
- **Evidence**: per flow, the command, its output and exit code, plus a second view that does not trust the tool's own words: the bytes of the written file, the body of the HTTP response, the row in the database. Evidence goes to a temp folder outside the repo, never into a commit.
- **Cleanup**: stop what Launch started by its own PID, remove the temp folders.
- **Boundaries**: what it leaves unverified (another OS, a flow not covered, a live service).

Point flows at local, test or mocked services. A flow that would send, charge, post or change real data stays out and is listed under Boundaries.

Prefer commands written in the SKILL.md over a script. Write one script only when Launch or Drive needs more than a few commands, and then run it on both Windows and macOS or mark the other OS unverified under Boundaries.

Done when the file exists; section 4 decides whether it works.

## 3. Tune an existing verify skill

1. Run it exactly as written, three times in a row, timing each run.
2. A step that failed once and passed once is flaky: find its cause (a race on the ready signal, a fixed port already taken, shared state between runs) and fix that. A retry, a sleep or a skipped step hides the cause and leaves the flakiness in place.
3. A run over five minutes: find the slowest step and cut it (a warm cache, a smaller fixture, a narrower flow). Name under Boundaries what each cut stops verifying.

Done when three runs in a row pass with the same result; then section 4.

## 4. Prove it: green, then red

1. **Green**: from a fresh shell, follow the verify skill as written against the current commit. Every flow passes, with evidence.
2. **Red**: make a throwaway copy with `git worktree add <temp folder> HEAD`. In the copy, break one thing a flow covers (a returned value, a route, an output field). Run the verify skill against the copy. It must fail and name the broken flow. Then `git worktree remove --force <temp folder>`.
3. Stays green on the broken copy → its checks are too loose: tighten the Drive or Evidence step that should have caught it, and repeat this section.

Done when it is green on the current commit and red on the broken copy, both with evidence.

## 5. Take stock across repos

Ask which parent folder to scan, unless the user named one. With the Agent's own file tools (not a shell one-liner, so it works on Windows), list every direct child folder holding `.git`, and for each one whether `.claude/skills/verify*/SKILL.md` exists.

Reply with a table: repo, verify skill (name or 無), and the surface you would guess from its README. Build nothing in this section; offer to start section 1 on the repo the user picks.

## 6. Hand off

Reply in the user's language with: the verify skill's path, the flows it covers, one run's duration, the green and red evidence from section 4, and its Boundaries. Commit it on a branch the way the repo's own `AGENTS.md` / `CLAUDE.md` asks; landing it on the main branch is the user's call.
