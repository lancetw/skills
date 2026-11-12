---
name: improve-loop
description: Autonomous-safe architecture deepening loop. Performs ONE mechanical, behavior-preserving deepening per invocation, test-first on an isolated wt branch, and never merges. Use when driven by /goal or /loop to repeatedly improve codebase architecture without human design decisions. Design-heavy candidates are written up as design docs and skipped, not implemented. The non-interactive sibling of /improve-codebase-architecture.
---

# Improve Loop

A **non-interactive, autonomous-safe** sibling of `/improve-codebase-architecture`.
It does ONE deepening per invocation and is built to be called repeatedly by `/goal`
or `/loop`. Where the interactive skill asks "which to explore?" and runs `/grilling`,
this skill **auto-selects** the safest candidate and **defers** every design decision.

Vocabulary is the `/codebase-design` deep-module language exactly: **module, interface,
implementation, depth, seam, adapter, leverage, locality**. Run that skill for the terms.

## Hard safety invariants (never violate)

1. **Never `merge`, `push`, or open a PR.** Work only on an isolated branch via `wt`.
2. **One candidate per invocation.** Keep diffs reviewable.
3. **TDD or abort — with one exception.** For *new or changed behavior*: write a failing
   test first, then make it pass; if you cannot make it red or reach green, **revert and stop**.
   **Deletion exception:** a behavior-preserving removal of *dead code* (proven by a no-callers
   search across the repo) is verified by the full suite staying green after you remove the
   code **and** its tests — not by a red-green cycle.
4. **Verify before acting.** Re-read the real files to confirm every sub-agent claim
   before editing. (Past runs: claims were wrong as often as right.) A claim you can't
   confirm = skip.
5. **Edit code ONLY for Class-A.** Class-B → a design doc, no code. Class-C → memory only.
6. **Commit discipline.** Stage only files you touched this run; commit on the branch
   (verify the branch by reading it with `git rev-parse --abbrev-ref HEAD`; never `main`);
   never `git commit -a`; run `git diff --cached --name-only` and confirm it matches before
   committing.
7. **Respect ADRs.** A candidate that conflicts with an ADR is Class-B or C, never A.
8. **Dedup.** Read the architecture-review backlog memory; skip completed candidates.
9. **No corner-cutting.** Every artifact — HTML report, design doc, tests, the review
   fan-out itself — meets its full spec; never substitute a lighter version for a specified
   one (e.g. a one-line card list for a diagrammed report, or reused stale candidates for a
   real `Explore` review unless explicitly told the candidates are current). Short on budget
   → narrow the *scope* (fewer candidates / cycles) at full depth, never the full scope at
   reduced quality. If you cannot meet an artifact's spec, say so in the result block rather
   than shipping a degraded one silently.

## Pipeline (one pass)

1. **Review.** Run the *review phase* of `/improve-codebase-architecture` (its parallel
   `Explore` fan-out over the codebase). **Skip** the "which to explore?" question.
   **HTML report (attended-mode):** emit the candidate set as a self-contained HTML report
   to the OS temp dir, then — if a human invoked this run interactively — `open` it and print
   its path. Headless (`/goal`/`/schedule`) runs write the file but do **not** open a browser;
   their result stays the printed `IMPROVE-LOOP RESULT` block.

   **Report quality bar — non-negotiable, do NOT cut corners.** The report MUST match the
   `/improve-codebase-architecture` `HTML-REPORT.md` scaffold exactly — Tailwind + Mermaid via
   CDN, editorial styling. EVERY candidate gets its own `<article>` with ALL of:
   (a) a **before/after diagram** as the centerpiece — Mermaid for graph-shaped relations,
   hand-built `div`/SVG for editorial visuals (mass diagram, call-graph collapse, cross-section);
   mix the patterns, don't make every card identical;
   (b) one-sentence **Problem** and one-sentence **Solution**;
   (c) **Wins** bullets in glossary terms;
   (d) a badge row: recommendation strength + **autonomy class (A/B/C)** + status (done / on-branch / pending);
   (e) an ADR or "why B" callout where relevant.
   End with a loop-view / top-recommendation section.
   **A flat list of cards with one-line descriptions and no before/after diagram is the
   cut-corner failure mode and is NOT acceptable.** If short on budget, cover *fewer*
   candidates at full depth — never all of them shallowly.
2. **Verify claims.** For each candidate, re-read the cited files. Apply the **deletion
   test**. Drop anything you can't confirm.
3. **Classify by autonomy** (rubric below): A / B / C.
4. **Dedup** against backlog memory; drop done candidates.
5. **Act on the single highest-value Class-A candidate:**
   - `wt switch --create refactor/<slug>`; reproduce whatever setup the worktree lacks
     (deps, generated artifacts) rather than falling back to working inline.
   - Write a failing test through an existing interface (red). Implement (green).
   - Run the full verify suite. Green → commit on the branch. Red you can't fix →
     revert the branch and stop.
6. **If no Class-A:** write a design doc for the top Class-B under
   `docs/architecture/<slug>.md` (the friction in glossary terms, the design forks, and a
   recommended deepening). Do **not** edit code.
7. **Record** what happened to the backlog memory (so the next pass dedups it).
8. **Print the result block** (below) so the `/goal` evaluator can judge from the transcript.

## Autonomy classification

**Class A — auto-implement.** ALL of:
- Deletion test is a clear *vanish* (dead code / pure dedup), **or** a behavior-preserving
  extraction of *existing inline logic* into a pure function whose inputs are already
  fixed by the call site.
- **No new interface/seam shape to design** — you relocate, dedup, or delete; you don't
  decide what an interface should look like.
- Local (≲3 files), reversible, testable through an existing interface.
- Touches no ADR.
- *Borderline → treat as B.* When unsure, do NOT auto-edit.

**Class B — design doc, skip code.** Any of: needs an interface or state-emission decision;
more than one reasonable design; reopens/touches an ADR; cross-module seam.

**Class C — log only.** Speculative, value unclear, or ADR-conflicting without strong reason.

## Output contract (required, last lines of every run)

```
IMPROVE-LOOP RESULT
- did: <slug> on branch refactor/<slug>  |  design-doc docs/architecture/<slug>.md  |  none
- suite: <pass>/<total> green  |  reverted (could not reach green)
- remaining auto-safe (A) candidates: <comma list, or "none">
```

`/goal` cannot read files — its evaluator only sees the transcript. This block is the
interface between the loop and `/goal`; the stop signal must be printed, not implied.
The driving condition is met when this prints `remaining auto-safe (A) candidates: none`.

## Usage

Attended, in-session:
```
/goal Repeatedly run the improve-loop skill. Each cycle implement the single highest-value
auto-safe deepening test-first on its own wt branch and PRINT the IMPROVE-LOOP RESULT block.
Never merge, push, or open a PR; design-heavy candidates get a doc and are skipped. Revert and
stop if a cycle can't reach green. Met when a cycle prints "remaining auto-safe (A) candidates:
none", or after 5 cycles.
```

Unattended weekly (recommended — produces review-ready branches you merge yourself):
```
/schedule weekly  claude -p "/goal <the condition above>"
```

Mode default is **propose-safe**: auto-implement Class-A to branches (never merged),
design-doc Class-B, log Class-C. For **propose-only** (no code at all), tell the loop to
treat every candidate as Class-B and emit only design docs.

Composes with: `codebase-design` (vocabulary), `tdd` (red-green), `worktrunk`/`wt`
(isolation), `grilling` (only when a human later picks up a Class-B doc).
