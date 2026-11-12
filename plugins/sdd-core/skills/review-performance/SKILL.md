---
name: review-performance
description: Review angle of the harness — are the performance thresholds written in the proposal met, measured, and does the diff add an obvious cost (N+1 queries, unbounded loops, payload or bundle growth, work on the render path)? USE WHEN the review-harness selects the performance angle, or when asked whether a change is fast enough.
---

# Review angle — performance

"Acceptable" is a number, not an impression. The thresholds come from the change's `proposal.md`
(section on measured thresholds) and from `mechanical.performance` in `.sdd/harness.yaml`. Format:
`../review-harness/FINDINGS.md`.

## Method

1. List the thresholds that apply to the change: from the proposal, and the project-wide ones in
   `.sdd/harness.yaml` (response time of an endpoint, bundle size, render time, query count…). No
   proposal or no threshold in it → only the configuration's thresholds; say so in the report.
2. Measure each one with the command the configuration gives, on the change's code. A threshold
   exceeded → 🛑 BLOCKER with the measured value; within 10 % of it → 🟡 MINOR.
3. A threshold that applies but cannot be measured locally (needs production data, a device) →
   say so in the report and add it to the post-deploy checks of the change; not a finding.
4. Read the diff for costs no threshold covers yet: a query inside a loop, a collection loaded
   without a bound, a synchronous call on a hot path, a dependency added to the main bundle. Each
   → 🔴 MAJOR with `Fails when` = the input size where it hurts, or 🟡 MINOR if the size is bounded.

## Never

- Report a measurement without the command and the environment it ran in.
- Run a measurement concurrently with another heavy build.
