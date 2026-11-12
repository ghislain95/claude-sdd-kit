---
name: review-security
description: Review angle of the harness — security review of the diff (injection, secrets, authorisation, personal data, unsafe input handling) through Claude Code's /security-review. USE WHEN the review-harness selects the security angle (auth, input handling, storage, network, secrets, dependencies touched), or when asked for a security review of a change.
---

# Review angle — security

Claude Code's built-in `security-review` skill is the reviewer; do not re-implement it. Your job is
to run it on the change and bring its findings into the shared format
(`../review-harness/FINDINGS.md`).

## Method

1. Invoke the `security-review` skill on the change's diff.
2. Add the project-specific checks the generic review cannot know, from `CLAUDE.md` and the module
   docs: who may call each new entry point, which data is personal, which logs must stay clean.
3. Convert each finding: exploitable from outside, or exposing secrets or personal data → 🛑 BLOCKER;
   exploitable only by an authenticated user against their own data, or defence in depth missing →
   🔴 MAJOR; hardening → 🟡 MINOR. `Fails when` = the request or input an attacker sends.

## Mechanical backing

Run what the project declares under `mechanical.security` in `.sdd/harness.yaml` (dependency audit,
secret scanner). Search the diff for committed secrets (the orchestrator's diff command piped to `grep -nE` on key
and token patterns) and report the command.
