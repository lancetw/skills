---
name: app-state-fix
description: Find every implicit state machine in a codebase, make the safe ones explicit without changing behavior, and list the rest for review with their states, transitions, and impossible-but-representable combinations.
disable-model-invocation: true
argument-hint: "[path or feature, default: current project]"
---

# App State Fix

Target: `$ARGUMENTS`, or the current project root minus vendored and generated code when empty.

An **implicit state machine** is a lifecycle whose legal states and transitions live only in the programmer's head: spread across booleans (`isLoading`, `isError`, `hasData`), nullable fields that must agree, status strings compared ad hoc, or effects that set each other off. It works until two pieces drift and the app lands in an **impossible state**, one no transition was meant to produce.

## 1. Sweep for signals

Each hit is a lead, not a finding. Search every category:

- **Flag clusters**: two or more booleans on one owner (component state, store slice, class, DB row) describing one lifecycle: `isLoading`/`isError`/`isSuccess`, `isOpen`/`isClosing`.
- **Paired nullables**: fields that must be set or empty together: `data` + `error`, `startedAt` + `finishedAt`, `user` + `token`.
- **Loose status fields**: `status` / `phase` / `mode` / `step` typed as plain string or number and compared by literal in more than one place.
- **Compound guards**: conditions over several flags, `if (a && !b || c)`, especially when repeated with variations.
- **Cascades**: effects, watchers, listeners, or callbacks that set state which triggers another (`useEffect` chains, signals, DB triggers, job status updates).
- **Persisted lifecycles**: columns that jointly encode one (`status`, `deleted_at`, `approved_by`, `retry_count`).
- **Explicit machines**: enum + transition table, XState, exhaustive reducer. Record them as the baseline the codebase already has.

Done when every category has been searched in scope and every hit is a candidate or dismissed with a reason. Expect many: a non-trivial app with only a handful of candidates usually means a category was skimmed, so re-run that category before moving on.

## 2. Reconstruct each machine

Group candidates by the lifecycle they encode; one machine may span several files. For each machine record:

- **Owner**: where the state lives, by symbol name.
- **States**: the states the code intends, read from how it branches on the flags.
- **Transitions**: `event: from → to`, each citing the symbol that performs it.
- **Impossible states**: every combination the representation allows but no intended state covers (n booleans allow 2^n).
- **Reachability**: for each impossible state, the code path that produces it (race, missing reset, error path, early return), or "unreachable" with the reason, or "unknown" with where you looked.
- **Fix shape**: one line, with what it improves on each axis below.

Pick the fix shape that improves all three axes and makes none worse:

- **UX**: the user can no longer land in the impossible state (spinner and error at once, a double submit, a stale form after success).
- **DX**: the legal states and transitions read in one place, and the type checker rejects an illegal combination.
- **AX**: an agent can list every state and transition from one greppable definition, so its next edit cannot add an illegal transition unnoticed.

Prefer the smallest shape that does it: derive the value instead of storing it, then a discriminated union, then an enum + transition function, then a statechart library only when the machine has nested or parallel states or timers and the codebase already uses one. Match the explicit machines recorded in step 1.

Order machines by risk: reachable impossible states first, then persisted ones (they corrupt data), then UI-only ones.

Done when every candidate is a machine record or merged into one, and every impossible state carries a reachability verdict.

## 3. Make machines explicit

One machine per change, in risk order: one commit per machine in a git repo, otherwise note the diff beside its record. A machine with a reachable impossible state cannot be converted without changing behavior, so it waits for the user's decision in item 4. Convert the others now. For each:

1. **Pin**: write tests for every intended transition from step 2 with the repo's own runner, and see them pass on the current code. No runner in the repo: convert nothing and list every machine under **For review**, since adding a runner is the user's call.
2. **Convert**: replace the flags, nullables, or loose status with the chosen shape, route every transition through it, delete the old fields, and update every caller.
3. **Hold**: re-run the pinned tests unchanged plus the type check; both stay green. A conversion that turns anything red is reverted and moves to **For review**.
4. **Reachable impossible states**: write a failing test that drives the current code into it, and list it as a decision for the user: which legal state it should become. Don't pick silently. Once decided, convert that machine with steps 1 to 3, the new test included.

Done when every converted machine has its old fields gone, its pinned tests and type check green, and each reachable impossible state is either fixed on the user's decision or listed open with its failing test.

## 4. Report

Per machine, in risk order: an ASCII state diagram and the record from step 2. Hand off with:

- **Fixed**: one line per converted machine: owner, shape chosen, and the pinned tests plus type check that prove it.
- **For review**: every machine left implicit, worst first, each with the evidence seen and the decision needed (the reachable impossible state and its failing test, or why it wasn't converted). A redesign too large for one change → name the `prototype` skill's logic branch as its next move.
- **Skipped**: areas not swept, and why.

Close with the count of implicit machines found, converted, and left, plus the explicit ones already there.
