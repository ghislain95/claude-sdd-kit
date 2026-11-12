---
name: review-bugs
description: Review angle of the harness — bug hunting on the diff (wrong results, crashes, races, edge cases) through Claude Code's /code-review. USE WHEN the review-harness runs, or when asked to hunt for bugs in a change. DO NOT USE for conventions, tests or security (other angles).
---

# Review angle — bug hunting

Claude Code's built-in `code-review` skill is the bug finder; do not re-implement it. Your job is to
run it on the right target at the right level and to bring its findings into the shared format
(`../review-harness/FINDINGS.md`).

## Method

1. Invoke the `code-review` skill on the change's diff at the level the orchestrator gives you
   (`.sdd/harness.yaml` → `budget.bug_hunt_level`; default `medium`, `high` for a change of high
   technical risk). Never `max` or `ultra` unless the owner asked for it.
2. Convert each finding to the shared format. Keep the scenario the skill gives as `Fails when`;
   severity: a wrong result, crash or data loss on a reachable path → 🛑 BLOCKER; reachable only
   through an unusual but valid input → 🔴 MAJOR; cleanup suggestions → 🟡 MINOR.
3. For each BLOCKER or MAJOR, check that the path is reachable from the change's entry points (read
   the caller). An unreachable path is downgraded to MINOR with the reason.

## Mechanical backing

When a finding can be shown by running something (a failing test you write in a scratch file, a
command that reproduces the crash), run it and attach the output. Do not leave the scratch test in the
working tree.
