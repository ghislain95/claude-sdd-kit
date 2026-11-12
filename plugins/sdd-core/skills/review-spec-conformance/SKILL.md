---
name: review-spec-conformance
description: Review angle of the harness — does the diff do exactly what the change's spec deltas say, no more, no less? USE WHEN the review-harness runs on an OpenSpec change, or when asked to check an implementation against its specs. DO NOT USE to review code quality (other angles) nor to fix anything.
---

# Review angle — spec conformance

You compare the implementation with `openspec/changes/<id>/specs/**` and `design.md`. You report; you
do not fix. Format: `../review-harness/FINDINGS.md` (one line per finding, severity, `Fails when`).

## Method

1. Artifacts: a missing `proposal.md`, `design.md` or `tasks.md` is a 🔴 MAJOR on the change folder
   (the cycle was skipped); continue with what exists. No `specs/` → nothing to conform to: say so,
   report the missing specs as 🛑 BLOCKER, stop.
2. Read every requirement and scenario of the spec deltas, and the `design.md` decisions.
3. Read the diff (base...head plus uncommitted changes) and the files it touches.
4. For each requirement: find the code that implements it, then walk each scenario through that code
   with the scenario's exact values.
   - Requirement with no implementation → 🛑 BLOCKER.
   - Scenario whose outcome the code does not produce → 🛑 BLOCKER, `Fails when` = the scenario.
5. For each behaviour the diff adds — endpoint, event, command, persisted field, UI action, config
   key, **exported or public function** — find the requirement it serves. None:
   - reachable by a user or another module (called, routed, exported in a public API) → 🛑 BLOCKER
     "behaviour outside the deltas";
   - not called anywhere → 🔴 MAJOR "dead extra code outside the deltas".
6. Each `design.md` decision: followed, or deviated with an update of `design.md`. A silent deviation
   → 🔴 MAJOR.
7. `tasks.md`: a box checked whose work is absent → 🔴 MAJOR.

## Mechanical backing

- `openspec validate <id> --strict`.
- `/opsx:verify` (skill `openspec-verify-change`) when `tasks.md` exists: run it and fold its findings
  in, in the shared format. Without `tasks.md`: skip it and write the reason in the mechanical lines.
