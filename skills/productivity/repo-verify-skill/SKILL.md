---
name: repo-verify-skill
description: Build, tune or take stock of a repo's verify skill — the smoke test an Agent runs to prove a change works the way its user meets it, before calling the change done. Use when the user asks to add a verify skill to a repo, to make an existing one faster or steadier, or to list which repos still lack one (「幫這個 repo 建 verify skill」「verify 太慢／不穩」「哪些 repo 還沒有 verify」).
license: MIT
---

# Repo Verify Skill

A verify skill lives in the repo it checks, at `.claude/skills/verify-<repo>/SKILL.md`, so every clone, every machine and every Agent gets it with `git pull`. It drives the real thing: it builds or launches the app, service or CLI, walks the flows its user walks, and judges each by evidence. Green unit tests alone leave a change unverified; the verify skill is what turns "the tests pass" into "it works".

Two words carry the rest of this file:

- **Surface**: where the repo's user meets a change. A CLI's output, an HTTP response, a page in a browser, the files a build writes.
- **Red**: the verify skill exits non-zero, and names the broken flow, when a flow it covers is broken. A verify skill that stays green on a broken change proves nothing.

## 1. Probe

1. `<repo>`: the last path part of `git remote get-url origin`, without `.git`. No remote → the folder holding `git rev-parse --git-common-dir`. A worktree's own folder name is not the repo name.
2. Existing verify skills: any `.claude/skills/verify*/SKILL.md` under `git rev-parse --show-toplevel`. Another branch or worktree with `verify` in its name, other than the one you are in, means another Agent may already be on it: ask the user before going on.
3. The surface and how to reach it, from what the repo says: README, `package.json` scripts, `pyproject.toml`, `Makefile`, CI config, e2e tests, `AGENTS.md` / `CLAUDE.md`. None of these → the header comments of the entry scripts. Still unclear → ask the user what they look at to tell a change worked.
4. What this machine can drive the surface with: the CLI itself, `curl` for HTTP, a browser-automation tool only when one is installed and answers. Without one, a web app is driven through its HTTP API. A static build is served from its output folder (`python3 -m http.server 0 --directory <out>`) and fetched. Code that only runs on a hosting platform (an edge worker, a cloud function) is imported with that platform's objects stubbed, or listed under Boundaries.
5. Read every script before running it. A command that deploys, publishes, pushes, sends, charges or changes real data stays out of the verify skill and goes under Boundaries, even when it is the repo's usual "run".

Done when you can name the surface, the launch or build command, the ready signal (a port answering, a log line, or for a one-shot build its exit code and last line) and the drive tool. Then go to the section for the request: none exists → 2, one exists → 3, a list of repos → 5.

## 2. Write a new verify skill

Write `.claude/skills/verify-<repo>/SKILL.md`. Its frontmatter is `name: verify-<repo>` and a double-quoted `description` (a bare `: ` inside it breaks the YAML) saying what it proves and when to run it: `"Prove a change to <repo> works the way its user meets it: <surface>. Use before calling a change done, or when asked to verify or smoke test."` Its body has these sections:

- **Launch**: the commands from a clean checkout to a running surface, and the ready signal. Dependencies install here. A precondition nothing can install (a file only this machine has, the network, a login) is checked first and exits 2, so "cannot run" never reads as red. A server's PID is the PID of the server command itself: start it without a `cd … &&` before the `&` (use the tool's own directory flag), and save `$!` to a file.
- **Drive**: one to three flows the user actually walks, taken from the README, the CI's e2e jobs or the feature list. Each flow is: action → expected result on the surface, checked by a command that exits non-zero on a mismatch (`test`, `grep -q`, `cmp`, a short `python3 -c` or `node -e` assert). Red is an exit code, never a reading of printed lines.
- **Evidence**: per flow, the command, its output and exit code, plus a second view that does not trust the tool's own words: the bytes of the written file, the body of the HTTP response, a count cross-checked against its source. When the result depends on this machine's state or the network, assert relations (this count equals that count) instead of fixed numbers. Evidence goes to a temp folder outside the repo, never into a commit.
- **Cleanup**: stop what Launch started by its saved PID and confirm with `ps` that nothing is left; remove build output Launch created inside the repo, leaving any that existed before Launch. Keep the evidence folder: the hand-off cites it.
- **Boundaries**: what it leaves unverified (another OS, a flow not covered, a live service, a platform-only path).

The Agent's shell tool starts each call in a fresh shell, so variables and `cd` do not carry over. Write each section as one self-contained block that derives the repo root from `git rev-parse --show-toplevel` run in the working directory, never from the script's own location (anchored there, a red run on a copy silently checks the original tree and stays green), and reads anything it shares (port, PID, evidence folder) from files in the evidence folder. When the blocks together pass about thirty lines, move them into one script under the skill's folder, and run it on both Windows and macOS or mark the other OS unverified under Boundaries.

Done when the file exists; section 4 decides whether it works.

## 3. Tune an existing verify skill

1. Run it exactly as written, three times in a row, timing each run.
2. A step that failed once and passed once is flaky: find its cause (a race on the ready signal, a fixed port already taken, state shared between runs) and fix that. A retry, a sleep or a skipped step hides the cause and leaves the flakiness in place.
3. A run over five minutes: find the slowest step and cut it (a warm cache, a smaller fixture, a narrower flow). Name under Boundaries what each cut stops verifying.
4. A check judged by reading output: turn it into a command that exits non-zero on a mismatch.

Done when three runs in a row pass with the same result; then section 4.

## 4. Prove it: green, then red

1. **Green**: in a fresh shell, run the verify skill as written against the current working tree. Every flow passes, exit 0, with evidence.
2. **Red**, once per flow: make a throwaway copy with `git worktree add "$(mktemp -d)/red" HEAD`. In the copy, break one thing that flow covers; pick at least one break the repo's own tests miss, since that is what the verify skill adds. Run the verify skill's commands with the copy as the working directory (the copy lacks an uncommitted verify skill, so run its commands from the file you wrote). It must exit non-zero and name the broken flow. Then `git worktree remove --force` the copy.
3. Stays green on a broken copy → its check for that flow is too loose: tighten it and repeat this section.

Done when it is green on the working tree and red on every broken copy, each with evidence.

## 5. Take stock across repos

Ask which parent folder to scan, unless the user named one. With the Agent's own file tools (not a shell one-liner, so it works on Windows), list every direct child folder holding `.git`, and for each one whether `.claude/skills/verify*/SKILL.md` exists.

Reply with a table: repo, verify skill (name or 無), and the surface you would guess from its README. Build nothing in this section; offer to start section 1 on the repo the user picks.

## 6. Hand off

Reply in the user's language with: the verify skill's path, the flows it covers, one run's duration, the green and red results from section 4 with the evidence folder's path, and its Boundaries in one line each. Commit it on a branch the way the repo's `AGENTS.md` / `CLAUDE.md` asks; without either, match the style of `git log --oneline -10`. Landing it on the main branch is the user's call.
