---
name: review-bugs
description: Review-harness angle — bug hunting on a change through /code-review plus a domain edge pass (numbers, boundaries, time).
---

# Review angle — bug hunting

Claude Code's built-in `code-review` skill finds generic bugs; a short domain edge pass after it
catches the classes it tends to miss (numbers, boundaries, time). Format:
`../review-harness/FINDINGS.md`.

## Method

1. **Level**: the `bug_hunt_level` the orchestrator gives (default `medium`). Use at least `medium`
   when the diff computes money, quantities, percentages or thresholds. Never `max` or `ultra` unless
   the owner asked for it.
2. **Run `code-review`** on the change (committed, per the harness §0), from the checkout where the
   change is checked out, with the level and a target: the branch name (`<level> <branch>`, reviewed
   against the default branch) when the change branch is not the default branch; otherwise the
   changed files as path targets. Count it
   as one forked run in your mechanical lines.
3. **Domain edge pass**, by hand, on each computation and condition the diff adds:
   - decimal arithmetic in binary floating point (sums of prices, `0.1 + 0.2`, a sum that lands just
     under a threshold), rounding at half a unit, currency units;
   - the exact boundary values named in the specs, one below and one above;
   - empty, zero, negative, very large and missing inputs; duplicates; unsorted input;
   - time: time zones, day boundaries, daylight saving; text: encoding, case, whitespace.
   Run the code on each suspicious input (a scratch script, removed afterwards) and attach the output.
4. **Severity**: a wrong result, crash or data loss on a reachable path → 🛑 BLOCKER; reachable only
   through an unusual but valid input → 🔴 MAJOR; cleanup suggestions → 🟡 MINOR. The public API (as
   `review-spec-conformance` defines it) and called code are reachable. Only code with no caller
   outside the public API is downgraded, with the reason.

## Never

- Leave a scratch file in the working tree: check `git status` before reporting.
