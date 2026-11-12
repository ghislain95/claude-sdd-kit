---
name: review-conventions
description: Review angle of the harness — does the diff respect the project's own rules (CLAUDE.md, module coding rules, ADRs, architecture), do comments and commit messages tell the truth, and did quality silently drop to make something pass? The brief given to the project's code-reviewer agent when the review-harness runs. USE WHEN the review-harness dispatches the conventions angle, or when asked to check a diff against the project's conventions. DO NOT USE to fix code.
---

# Review angle — project conventions and architecture

The review-harness dispatches the project's `code-reviewer` agent with this skill as its brief: the
agent carries the module checklists, forbidden dependencies and the "hidden quality drop" search;
this skill adds mechanical backing and the shared format (`../review-harness/FINDINGS.md`). You do
not dispatch another agent.

## Method

1. Review the diff (the command the orchestrator gives, plus uncommitted changes) with the project's rules: root `CLAUDE.md`,
   `AGENTS.md`, module docs (`CODING_RULES.md`), ADRs, and — if you are the `code-reviewer` agent —
   your own checklist. Give a `Fails when` on every BLOCKER and MAJOR.
2. Run the commands under `mechanical.conventions` of `.sdd/harness.yaml`. A failing command is a
   finding of its own, at the line the tool reports.
3. Always check, whatever the project's rules (they are often silent on these):
   - **comments agree with the code** they describe (a comment saying "from 100" over `> 100` →
     🔴 MAJOR, `Fails when` = a maintainer trusting the comment);
   - **dead code** added by the diff → 🟡 MINOR;
   - **commit messages** of the range: the project's format (`docs/CONTRIBUTING.md`; by default
     `type(<change-id>): subject` plus a body) → 🟡 MINOR per commit that breaks it.
4. Severities: keep the agent's checklist severities unless a finding has no scenario (then MINOR).

## Never

- Accept an exemption added to make a rule pass (an ignore list, a narrowed rule, a suppression
  comment) as a fix: it is a 🛑 BLOCKER unless `design.md` justifies it.
