---
name: review-tests
description: Review angle of the harness — does every scenario of the spec deltas have a test, and would those tests actually catch a regression of the changed code (mutation evidence when the tooling exists, hand mutation and adversarial inputs otherwise)? USE WHEN the review-harness runs, or when asked to judge the tests of a change. DO NOT USE to write the missing tests (that is the tester's job).
---

# Review angle — tests

Two questions: **coverage** (is every specified behaviour tested?) and **strength** (would the tests
fail if the changed code were wrong?). Format: `../review-harness/FINDINGS.md`.

## Coverage

1. List every scenario of `openspec/changes/<id>/specs/**`.
2. For each, find the test that exercises it (feature file, test name, assertion):
   - a scenario that names a **boundary or exact value** (a threshold, a limit, an exact amount) must
     be tested with that exact value; otherwise any input that exercises the same behaviour suffices;
   - none → 🛑 BLOCKER "untested scenario", `Fails when` = the scenario regressing unnoticed.
3. A test that exercises the scenario but does not assert its outcome (only "no error", "defined", a
   count where the content matters) → 🛑 BLOCKER if no other test covers the scenario, 🔴 MAJOR
   otherwise.
4. An order asserted that the contract does not impose, or an order imposed by the contract that no
   test checks with an input arriving out of order → 🔴 MAJOR.

## Strength

1. Run `mechanical.tests.run` from `.sdd/harness.yaml` (the changed modules' tests); red → 🛑 BLOCKER.
2. Mutation: when `mechanical.tests.mutation` is set, run it on the changed files (`{files}`), never
   the whole codebase. Each surviving mutant on changed code is a finding at the mutated line:
   🛑 BLOCKER if it changes a specified outcome, 🔴 MAJOR otherwise; the missing test goes in `Fix`.
3. Without mutation tooling, mutate by hand: for the riskiest changed lines (conditions, boundaries,
   arithmetic, early returns), flip one thing in a scratch copy, run the relevant tests, restore.
   Report each survivor the same way and add `no mechanical backing: mutation tooling absent (manual
   mutation of N lines)`.
4. **Adversarial inputs**: mutants cannot reveal what the code never computed right. For each numeric
   computation the specs constrain, run the code with one input that stresses its representation
   (decimal sums that land on a threshold, half-unit rounding, very large values) and compare with
   the specified outcome. A wrong result is a 🛑 BLOCKER for the tests angle too (no test catches it).

## Never

- Leave a mutated or scratch file behind: restore and check `git status` before reporting.
- Run two heavy builds at once; follow `budget.heavy_builds`.
