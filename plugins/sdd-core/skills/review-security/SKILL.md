---
name: review-security
description: Review-harness angle — security review of a change through /security-review plus project-specific checks.
---

# Review angle — security

Claude Code's built-in `security-review` skill is the reviewer; do not re-implement it. Your job is
to run it on the change and bring its findings into the shared format
(`../review-harness/FINDINGS.md`).

## Method

1. Invoke the `security-review` skill on the change, targeted like `review-bugs` §2: it reviews the
   current branch against the default branch, so when the change sits on the default branch, give it
   the orchestrator's diff command and the changed files in the request. Count it as one forked run.
2. Add the project-specific checks the generic review cannot know, from `CLAUDE.md` and the module
   docs: who may call each new entry point, which data is personal, which logs must stay clean.
3. Convert each finding: exploitable from outside, or exposing secrets or personal data → 🛑 BLOCKER;
   exploitable only by an authenticated user against their own data, or defence in depth missing →
   🔴 MAJOR; hardening → 🟡 MINOR. `Fails when` = the request or input an attacker sends.

## Mechanical backing

Run what the project declares under `mechanical.security` in `.sdd/harness.yaml` (dependency audit,
secret scanner). Search the diff for committed secrets (the orchestrator's diff command piped to `grep -nE` on key
and token patterns) and report the command.
