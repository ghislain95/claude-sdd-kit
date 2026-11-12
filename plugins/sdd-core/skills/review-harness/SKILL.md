---
name: review-harness
description: Runs the full review of a change after /opsx:apply — selects the review angles from the diff and the project's .sdd/harness.yaml, runs them one after the other, has every BLOCKER and MAJOR adversarially verified, sends confirmed findings back to the developer agent, loops at most three rounds, writes the review report and posts the review-harness status. USE WHEN an OpenSpec change has been implemented and before /opsx:verify, or when the user asks for "the full review" of a change. DO NOT USE for a quick look at a diff (use code-reviewer) or to review a single angle (use that angle's skill).
argument-hint: "[change-id]"
---

# Review harness

The harness stands in for the owner's eyes on every change that opens no human gate. Its rule:
**every opinion is checked by someone who tries to refute it, and backed by a mechanical check when
one exists.** Finding format for every angle: [`FINDINGS.md`](FINDINGS.md). Configuration schema:
[`HARNESS_CONFIG.md`](HARNESS_CONFIG.md).

## 0. Inputs

- The change id (argument, or the only change under `openspec/changes/` with unchecked work).
- The diff: `git diff <base>...HEAD` plus uncommitted changes, `<base>` = the merge base with the
  default branch.
- `.sdd/harness.yaml`. Missing → use the defaults of `HARNESS_CONFIG.md` and say so in the report.
- Start time (`date +%s`) for the time budget.

## 1. Select the angles

Always: `spec-conformance`, `conventions`, `bugs`, `tests`.
Add each conditional angle whose `when` patterns in `.sdd/harness.yaml` match a path of the diff
(`security`, `performance`, `interface`, `sourced-claims`). A documentation-only diff runs
`sourced-claims` and `spec-conformance` only; say why the others were limited.

Write the selection, with the reason for each angle left out, at the top of the report.

## 2. Run the angles — one after the other

For each selected angle, dispatch one agent with: the change id, the diff range, the angle's skill to
follow (`sdd-core:review-<angle>`), the relevant `mechanical.<angle>` entries, and the instruction to
answer in the format of `FINDINGS.md`. Agents run **sequentially**, never two heavy builds at once
(`budget.heavy_builds`). Before each dispatch, check the budget (§6).

Collect the findings; deduplicate the same location and problem reported by two angles (keep the
higher severity, list both angles).

## 3. Verify every BLOCKER and MAJOR — one combined verifier per round

Dispatch **one** verifier agent with all of this round's BLOCKER and MAJOR findings. Its instruction:
for each finding, try to **refute** it — show the input cannot occur, the path is unreachable, the
spec allows it, the mechanical evidence is misread. Default to *confirmed* only when the refutation
fails. It answers per finding: `confirmed` or `refuted` with the reason.

Refuted findings are dropped from the fix list and kept in the report with the refutation. MINOR
findings are not verified; they are listed for the developer, who fixes them when cheap.

## 4. Fix loop — three rounds at most

1. Send the confirmed BLOCKER and MAJOR findings to the developer agent that owns the code (the
   project's routing table in `CLAUDE.md`), with the finding lines verbatim.
2. When it hands back, re-run only the angles that produced those findings, on the new diff, then §3.
3. Stop when no BLOCKER and no MAJOR is left. After the **third** round with one still open: stop,
   write the report, and escalate to the owner with the open findings and what was tried. Do not
   start a fourth round.

## 5. Report and status

Write `openspec/changes/<id>/review.md`:

```markdown
# Review — <id>
Base: <sha> · Head: <sha> · Rounds: <n> · Duration: <min> · Agent runs: <n>
## Angles
| Angle | Ran | Why / why not | Mechanical checks |
## Findings
| # | Angle | Severity | Location | Status (fixed in round n / refuted / open / minor) |
## Refuted
<finding line> — <refutation>
## Not covered
<angles skipped for budget, checks impossible locally and moved to post-deploy>
```

Then, when the change has a pull request or a pushed head commit, post the status on the head commit:

```bash
gh api "repos/{owner}/{repo}/statuses/$(git rev-parse HEAD)" \
  -f state=<success|failure> -f context=review-harness \
  -f description="<n> rounds, <open> open BLOCKER/MAJOR"
```

`success` only with zero open BLOCKER and MAJOR. If posting fails (token without the commit-statuses
permission), say so in the report and to the user; never claim the status was posted.

The status is set by the agent: it prevents forgetting the review, not lying about it. The report in
the pull request is what makes it auditable.

## 6. Budget

Before each agent dispatch, compare elapsed minutes and agent runs with `budget.minutes` and
`budget.agent_runs` (the token budget is enforced through the number of agent runs). Exceeded → stop
dispatching, finish the report with the angles not covered under **Not covered**, post `failure`, and
tell the owner. Never raise the effort above `budget.effort`; never use an ultracode-scale fan-out.
