---
name: app-fresh-fix
description: Run after each new model release. Sweeps the whole project for anything broken, inconsistent, inefficient, or no longer needed; fixes what is proven, lists the rest for review.
disable-model-invocation: true
argument-hint: "[path, default: current project]"
---

# App Fresh Fix

Target: `$ARGUMENTS`, or the current project root when empty.

Each finding sits under one lens:

- **Broken**: wrong output, crash, failing or skipped test, dead link, config pointing at nothing.
- **Inconsistent**: two patterns for one job, doc contradicting code, naming drift, diverged duplicates.
- **Inefficient**: needless work at runtime, build, or in the dev loop.
- **No longer needed**: zero callers, stale flag or fallback, unused dependency, commented-out code, finished TODO.

## Steps

1. **Read every file.** List tracked files (`git ls-files`, else `rg --files`) into `SWEEP.md` in the scratchpad, skipping generated, vendored, lock, binary and media files (name what you skipped). Read each one and log findings: lens, location, one-line claim. Large project → fan out by directory to sub-agents; `SWEEP.md` stays the one list.
   Done when every listed file is ticked off.

2. **Prove.** A finding is **sure** only when an instrument backs it, run now and recorded beside it: a red test or repro, a type check or lint error, a benchmark, or zero `rg` hits for a non-exported symbol across code, strings, config, routes and templates. Everything else is **unsure**. Also unsure, even when proven: changes to observable behavior, public API, persisted data or schemas, security, and taste calls.

3. **Fix the sure ones**, smallest change each: one commit per finding (no git → note the diff in `SWEEP.md`). After each fix, rerun its instrument and the project's test, lint and type check. A fix that turns anything red moves back to unsure.

4. **Report.**
   - **Fixed**: lens, what changed, the check that proves it.
   - **For review**: unsure findings, worst first, with the evidence and the decision needed.
   - **Skipped**: files or areas not read, and why.
