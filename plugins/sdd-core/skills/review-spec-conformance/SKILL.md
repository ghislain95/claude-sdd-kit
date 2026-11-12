---
name: review-spec-conformance
description: Review angle of the harness — does the diff do exactly what the change's spec deltas say, no more, no less? USE WHEN the review-harness runs on an OpenSpec change, or when asked to check an implementation against its specs. DO NOT USE to review code quality (other angles) nor to fix anything.
---

# Review angle — spec conformance

You compare the implementation with `openspec/changes/<id>/specs/**` and `design.md`. You report; you
do not fix. Format: `../review-harness/FINDINGS.md` (one line per finding, severity, `Fails when`).

## Method

1. Read every requirement and scenario of the change's spec deltas, and `design.md` decisions.
2. Read the diff (`git diff <base>...HEAD` plus uncommitted changes) and the files it touches.
3. For each requirement: find the code that implements it, then walk each scenario through that code.
   - Requirement with no implementation → 🛑 BLOCKER.
   - Scenario whose outcome the code does not produce → 🛑 BLOCKER, `Fails when` = the scenario.
4. For each behaviour the diff adds (endpoint, event, command, persisted field, UI action, config
   key): find the requirement it serves. None → 🛑 BLOCKER "behaviour outside the deltas".
5. Each `design.md` decision: followed, or deviated with an update of `design.md`. A silent deviation
   → 🔴 MAJOR.
6. `tasks.md`: a box checked whose work is absent → 🔴 MAJOR.

## Mechanical backing

- Run the project's OpenSpec validation (`openspec validate <id> --strict`).
- When `/opsx:verify` (skill `openspec-verify-change`) is available, run it and fold its findings in,
  in the shared format.

Report the commands and their results at the end, as `FINDINGS.md` says.
