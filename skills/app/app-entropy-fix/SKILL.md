---
name: app-entropy-fix
description: Long-running architecture entropy reduction for a whole codebase. Picks the shape the code would have if built today knowing every current requirement, then converges on it in rounds — each round migrates every caller to one canonical implementation, deletes the replaced one and locks the rule with a machine check. Product decisions and breaking migrations are recorded and skipped, never guessed.
disable-model-invocation: true
argument-hint: "[path, default: current project] [max rounds, default 10]"
---

# App Entropy Fix

Target: the path in `$ARGUMENTS`, or the current project root. Budget: the number in `$ARGUMENTS`, or 10 rounds.

Adapted from Khazix, the `/goal` architecture-governance prompt: <https://x.com/Khazix0918/status/2126324185626734795>

**Core idea:** assume today is the product's first day, but every real requirement, business constraint and product shape is already known. Design the codebase that should exist, then converge on it through safe, incremental, verified refactors.

## Lenses

Each finding sits under one:

1. **Single source of truth**: a business rule, data definition, config value, piece of state or design token defined in more than one place.
2. **Canonical implementation**: two implementations of one meaning or job (parallel stacks, duplicated logic, temporary patches, compatibility layers). Compatibility with a real caller or a stated contract stays.
3. **Deep modules** (Ousterhout, *A Philosophy of Software Design*): shallow modules, pass-through layers, abstractions that leak their internals.
4. **Cohesion and coupling**: unclear ownership or dependency direction, cycles, implicit coupling, cross-layer access, shared mutable state.
5. **Locality of change**: one business concept whose change touches many unrelated files.
6. **Deletion over accumulation**: complexity that can simply go.
7. **Enforceable architecture**: an agreed rule with nothing stopping it from regressing (type, lint, AST rule, contract test, CI step).

**Deletion test** for every layer: delete it in your head. Complexity vanishes → the layer goes. Complexity spreads to its callers → the layer earns its place.

## Areas

Sweep each: UI components and design system · business logic and domain model · API and data contracts · state management and data flow · data access and caching · config and env vars · error handling and retries · logging and observability · auth and permissions · naming, directories and module boundaries · utilities and shared infrastructure · tests, build and dev tooling.

## Setup

1. **Isolate.** `wt switch --create refactor/entropy` (no `wt` → `git worktree add`). Reproduce whatever setup the worktree lacks (deps, generated files) instead of working in the main tree.
2. **State file.** Keep `$(git rev-parse --git-common-dir)/entropy-fix/PROGRESS.md`: outside the commit, shared by every worktree, survives a new session. It holds the maps, the task pool (open / done / pending decision) and one line per round. A run that finds it resumes from it.
3. **Map.** Read the real business, architecture, history (`git log`, existing ADRs), tech stack, tests and production constraints. Write into the state file: architecture map, dependency graph, state-ownership map, duplicate-implementation list, tech-stack list (one row per job, every stack doing it), deviation list. Each entry cites the files it rests on.
   Done when every area above has entries or "nothing found, looked at …".
4. **Baseline.** Find the project's test, type and lint commands and run them. No usable tests for an area → the first round there writes characterization tests through its public interface; until they exist, its findings stay for review.

## Round

Each round is one closed loop. Never ship a new abstraction, directory or interface without migrating its callers.

1. **Pick** the highest-value open task. Re-read the cited files; a claim you can't confirm is dropped.
2. **Callers.** Find every real caller and dependent (`rg -F` across code, strings, config, routes, templates).
3. **Options.** Sketch at least two refactors and pick the one with the lowest *total* complexity: code, concepts and interfaces left behind, not lines changed.
4. **Classify.** Pending decision, recorded in the pool and skipped, when it needs a product call, a major architecture change, a breaking migration, or touches public API, persisted data or schemas, security, or an ADR. Then take the next independent task.
5. **Pin** the behavior: tests that pass before the change and go red if it breaks.
6. **Migrate** every caller to the canonical implementation, then **delete** the replaced one. Old and new never coexist past the round.
7. **Review**: a sub-agent that did not write the change reads the diff against the lenses and the pinned tests. A finding becomes a fix only once a run turns it red.
8. **Verify**: full test, type and lint run green. Red you can't fix in three tries → revert the round and mark the task for review.
9. **Lock**: add the cheapest check that stops this entropy coming back (lint rule, AST rule via `ast-grep`, import-boundary rule, contract test, CI step) and watch it fail on the old shape.
10. **Record**: one commit for the round, staged by path; an ADR in the repo's ADR directory (none → `docs/adr/`) when the round settled a convention; the round line in the state file. Rescan the areas the round touched and add new finds to the pool.
11. **Print** the result block, then start the next round without asking.

## Never

- Merge, push or open a PR. The branch is the hand-off.
- Over-abstract, move directories for no gain, trade readability for fewer lines, or merge concepts that only look alike.
- Break existing behavior, data compatibility or an external contract.

## Stop

Stop when no high-value task is left, the round budget is spent, or no remaining task can be done safely.

**Converged** means all hold, each checked by an instrument, not asserted:

- every core business concept has one named authoritative implementation;
- every core module has a clear job and public interface;
- no meaning has two implementations without a written reason;
- no unapproved cycles between core modules;
- business logic is decoupled from UI, storage, framework and external services;
- a new feature fits inside one module boundary;
- each settled rule has an automated regression check;
- every existing behavior, data format and contract still holds.

## Result block

Print after every round and as the last lines of the run. A `/goal` evaluator sees only the transcript, so the stop signal must be printed:

```
ENTROPY-FIX RESULT
- round: <n>/<budget>  did: <task> (<commit>)  |  reverted: <task>  |  none
- checks: tests <pass>/<total>, type <ok|n/a>, lint <ok|n/a>, new guard: <name|none>
- pending decisions: <count> (in PROGRESS.md)
- open tasks: <count>
- status: continuing | converged | budget | no-safe-work
```

## Report

At stop: **pending decisions** first (each with evidence and the decision needed), then **done** (round, lens, commit, guard), **left** (open tasks, worst first), **skipped** (areas not read and why), and the branch with its next command.
