---
name: app-unwaterfall-fix
description: Find waterfalls on a codebase's hot paths (independent async calls awaited one after another) and make the proven-safe ones concurrent without changing behavior; list the rest for review.
disable-model-invocation: true
argument-hint: "[path, route or service, default: current project]"
---

# App Unwaterfall Fix

Target: `$ARGUMENTS`, or the current project root minus vendored and generated code when empty.

A **waterfall** is two or more async calls awaited in sequence when neither needs the other, so each adds a full round-trip of latency for nothing.

## Steps

1. **Map the hot paths.** A hot path is code a user waits on: request handlers, API routes, page or server-component loaders, RPC handlers, jobs whose result a user awaits, CLI startup. Find entry points from the router or framework config and the server bootstrap, and list each by file and handler name in `HOTPATHS.md` in the scratchpad.
   Done when every entry point in scope is listed.

2. **Trace.** Follow each entry point through every awaited call, into helpers, down to the I/O (DB, HTTP, cache, filesystem, queue). Record each sequence of two or more awaits with a verdict and a one-line reason:
   - **dependent**: B reads A's result, or A's side effect must land first (write then read, auth check before data access, ordered events, a transaction on one connection).
   - **independent**: everything else.
   - **unsure**: you can't tell from the code.

   Done when every entry point is ticked and every sequence has a verdict.

3. **Flatten the independent ones**, one entry point per change: one commit each (no git → note the diff in `HOTPATHS.md`).
   1. **Pin**: with the repo's own runner, write or find tests that exercise the entry point's result and its error path, and see them pass on the current code. No runner → flatten nothing and list every sequence under **For review**, since adding one is the user's call.
   2. **Flatten** in the codebase's own idiom (`Promise.all` / `Promise.allSettled`, `asyncio.gather` / `TaskGroup`, Go `errgroup`, Rust `join!` / `try_join!`). Keep error semantics: fail-fast stays fail-fast, a tolerated failure uses the settled form. A partly dependent chain starts the independent call early and awaits it where its result is first needed. A per-item `await` in a loop runs concurrently, bounded by the project's existing limiter when the target is rate-limited or pooled.
   3. **Hold**: rerun the pinned tests unchanged plus the project's test, lint and type check. Anything red → revert and move to **For review**.

   These go to **For review** instead of being flattened: unsure sequences, and any change that alters observable ordering, error behavior, or load on a rate-limited or pooled target with no existing limiter.
   Done when every independent sequence is flattened and green, or listed for review with its reason.

4. **Report.** Hand off with:
   - **Fixed**: entry point, sequence, round-trips removed, and the pinned tests that prove it.
   - **For review**: sequences left as they are, worst latency first, with the evidence and the decision needed.
   - **Skipped**: entry points or areas not traced, and why.
