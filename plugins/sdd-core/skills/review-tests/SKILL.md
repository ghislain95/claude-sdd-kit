---
name: review-tests
description: Review angle of the harness — does every scenario of the spec deltas have a test, and would those tests actually catch a regression of the changed code (mutation evidence when the tooling exists)? USE WHEN the review-harness runs, or when asked to judge the tests of a change. DO NOT USE to write the missing tests (that is the tester's job).
---

# Review angle — tests

Two questions: **coverage** (is every specified behaviour tested?) and **strength** (would the tests
fail if the changed code were wrong?). Format: `../review-harness/FINDINGS.md`.

## Coverage

1. List every scenario of `openspec/changes/<id>/specs/**`.
2. For each, find the test that exercises it (feature file, test name, assertion). None → 🛑 BLOCKER
   "untested scenario", `Fails when` = the scenario regressing unnoticed.
3. A test that exercises the scenario but does not assert its outcome (asserts only "no error",
   "defined", a count where the content matters) → 🔴 MAJOR.
4. An order asserted that the contract does not impose, or an order imposed by the contract that no
   test checks with an input arriving out of order → 🔴 MAJOR.

## Strength

1. Run the project's mutation command for the changed code when `.sdd/harness.yaml` declares one
   under `mechanical.tests.mutation` (scoped to the changed classes or files, never the whole suite).
   Each surviving mutant on changed code is a finding: 🛑 BLOCKER if it changes a specified outcome,
   🔴 MAJOR otherwise. Attach the mutant.
2. When mutation tooling is absent, mutate by hand: for the two or three riskiest changed lines,
   flip a condition or a boundary in a scratch copy, run the relevant tests, restore. Report each
   survivor the same way, and add the line `no mechanical backing: mutation tooling absent (manual
   mutation of N lines)`.
3. Run the changed modules' test command and report its result; a red suite is a 🛑 BLOCKER.

## Never

- Leave a mutated file behind: restore and check `git status` is unchanged before reporting.
- Run two heavy builds at once; follow `budget.heavy_builds` in `.sdd/harness.yaml`.
