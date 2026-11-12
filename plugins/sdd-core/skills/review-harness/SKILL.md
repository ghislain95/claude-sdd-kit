---
name: review-harness
description: Runs the full review of a change after /opsx:apply — selects the review angles from the diff and the project's .sdd/harness.yaml, runs them one after the other, has every BLOCKER and MAJOR adversarially verified, sends confirmed findings back to the developer agent, loops a bounded number of rounds, writes and commits the review report and posts the review-harness status. USE WHEN an OpenSpec change has been implemented and before /opsx:verify, or when the user asks for "the full review" of a change. DO NOT USE for a quick look at a diff (use code-reviewer) or to review a single angle (use that angle's skill).
argument-hint: "[change-id]"
---

# Review harness

The harness stands in for the owner's eyes on every change that opens no human gate. Its rule:
**every opinion is checked by someone who tries to refute it, and backed by a mechanical check when
one exists.** Finding format for every angle: [`FINDINGS.md`](FINDINGS.md). Configuration schema and
defaults: [`HARNESS_CONFIG.md`](HARNESS_CONFIG.md).

You are the orchestrator: you dispatch agents and keep the count; you do not review or fix yourself.

## 0. Inputs

1. **Change id**: the argument; otherwise the only directory under `openspec/changes/` other than
   `archive/`; otherwise ask the user. Note which of `proposal.md`, `design.md`, `tasks.md` and
   `specs/` exist: the angles need to know (a missing artifact is reported, not guessed).
2. **Diff range**: base = `git merge-base HEAD <default branch>`. If that diff is empty (the change
   was committed on the default branch), base = the parent of the first commit that touched
   `openspec/changes/<id>/` (the empty tree, `git hash-object -t tree /dev/null`, when that commit is
   the root commit). Still empty → stop and tell the user there is nothing to review.
   Head = `HEAD`, plus uncommitted changes. Record **head reviewed first**.
3. **Settings**: `.sdd/harness.yaml`. Missing file → the defaults of `HARNESS_CONFIG.md`, said in the
   report. Present file → its keys only: an angle with no `angles.<angle>` key is never selected.
4. **Clock and counter**: start time (`date +%s`); agent runs = 0.

## 1. Select the angles

Always: `spec-conformance`, `conventions`, `bugs`, `tests`, `sourced-claims` (the last one is cheap
and covers comments and commit messages, which every diff has).
Conditional: `security`, `performance`, `interface` — selected when a path of the diff matches a glob
of `angles.<angle>`.

Write the selection, with the reason for each angle left out, at the top of the report.

## 2. Review pass 1 — angles one after the other

For each selected angle, in the order above, dispatch **one** agent with: the change id, the diff
range, the artifacts present, the angle's skill to follow (`sdd-core:review-<angle>`), its
`mechanical.<angle>` entries, `budget.effort`, `budget.bug_hunt_level` (for `bugs`), and the
instruction to answer in the format of `FINDINGS.md`.

- **Conventions** is dispatched as the project's `code-reviewer` agent itself, with the
  `review-conventions` skill as its brief. No `code-reviewer` agent → a general agent with that skill.
  Never ask an agent to dispatch another one.
- Agents run **sequentially**; never two heavy builds at once (`budget.heavy_builds`).
- Before each dispatch, apply the budget rule (§6).

Collect the findings; merge the same location and problem reported by two angles (keep the higher
severity, list both angles).

## 3. Verify every BLOCKER and MAJOR — one verifier per pass

Dispatch **one** verifier agent with all of this pass's BLOCKER and MAJOR findings, verbatim. Its
instruction: for each finding, try to **refute** it — the input cannot occur, the path is
unreachable, the spec allows it, the evidence is misread — and answer one of:

- `confirmed`;
- `confirmed, downgraded to <severity>` with the reason (the defect is real but smaller);
- `refuted` with the reason.

Refuted findings leave the fix list and stay in the report with the refutation. MINOR findings are not
verified; they go to the developer, who fixes them when cheap.

## 4. Fix rounds — `budget.rounds` at most

A **fix round** = the developer fixes the confirmed BLOCKER and MAJOR findings, then a new review
pass checks the result. Review pass n+1 follows fix round n.

1. Send the confirmed BLOCKER and MAJOR findings, verbatim, to the developer agent: the one the
   project's routing table in `CLAUDE.md` names for the code concerned; none → the agent that
   implemented the change; none → a general agent. It **commits on the change branch** and runs the
   touched modules' tests green before handing back.
2. Next review pass: re-run the angles that produced those findings, **plus** `conventions` and
   `tests` whenever code changed, on the diff base..new head, then §3.
3. Stop when no BLOCKER and no MAJOR is open. After fix round `budget.rounds` with one still open:
   stop, write the report, escalate to the owner with the open findings and what was tried. Never
   start another round.

## 5. Report, commit and status

Write `openspec/changes/<id>/review.md`:

```markdown
# Review — <id>
Base: <sha> · Head reviewed first: <sha> · Head reviewed last: <sha>
Review passes: <n> · Fix rounds: <n> · Duration: <min> · Agent runs: <n>/<budget>
## Angles
| Angle | Ran | Why / why not | Mechanical checks |
## Findings
| # | Angle | Severity | Location | Verification | Status (fixed in round n / refuted / open / minor) |
## Finding lines
<each finding line verbatim, with its mechanical evidence indented below it>
## Refuted and downgraded
<finding line> — <verifier's reason>
## Not covered
<angles skipped for budget, checks impossible locally and moved to post-deploy, missing artifacts>
```

Commit it on the change branch (`docs(<id>): review report`, or with the last fix round's commit), so
it travels with the pull request.

Status on the head commit, when the branch is pushed:

```bash
gh api "repos/{owner}/{repo}/statuses/$(git rev-parse HEAD)" \
  -f state=<success|failure> -f context=review-harness \
  -f description="<passes> passes, <open> open BLOCKER/MAJOR"
```

- `success` only when zero BLOCKER and MAJOR are open **and** every selected angle ran. A budget stop
  is always `failure`, even with nothing open: the coverage is incomplete.
- No remote or branch not pushed yet → not posted; the report says "status not posted: no remote" or
  "posted after push". Posting refused (token without the commit-statuses permission) → say so in the
  report and to the user. Never claim a status that was not posted.

The status is set by the agent: it prevents forgetting the review, not lying about it. The report in
the pull request is what makes it auditable.

## 6. Budget

- **What counts as an agent run**: every agent you dispatch (angle, verifier, developer), and every
  forked skill an angle invokes (one `code-review` or `security-review` run = one agent run). Angles
  report the forks they made.
- **Rule**: a dispatch that would bring the runs above `budget.agent_runs`, or that starts after
  `budget.minutes` have elapsed, is not made.
- **Minimum to plan for**: pass 1 = selected angles + 1 verifier; each fix round = 1 developer + the
  re-run angles + 1 verifier. With the five constant angles and one round: about 13 runs.
- When the rule stops you: finish the report, list what was not covered, post `failure`, tell the
  owner. Never raise the effort above `budget.effort`; never use an ultracode-scale fan-out.
