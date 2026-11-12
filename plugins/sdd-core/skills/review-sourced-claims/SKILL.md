---
name: review-sourced-claims
description: Review angle of the harness — does every figure, date, cause, version or "verified" statement written by the change (docs, comments, changelog, commit and PR text, reports) have a source the reader can check? USE WHEN the review-harness runs on a diff that touches documentation or prose, or when asked to fact-check a document an agent wrote.
---

# Review angle — sourced claims

Agents state plausible facts that nobody checked: a count recomputed differently, a date guessed, a
cause invented to make a story coherent, "tested" without a command. This angle checks each claim
against its source. Format: `../review-harness/FINDINGS.md`.

## Method

1. List the claims the diff adds or changes in prose: numbers, dates, versions, causes ("because…"),
   comparisons, and statements of verification ("tested", "verified in production", "no impact").
2. For each, find its source: a command output you can re-run, a file and line, a commit, a spec, a
   measured report. Re-run the command when it is cheap.
3. Severity:
   - claim contradicted by its source → 🛑 BLOCKER (`Fails when` = a reader acting on the false
     figure or cause);
   - claim with no findable source, in a document others act on (spec, ADR, changelog, report,
     README) → 🔴 MAJOR;
   - unsourced claim in a comment or an internal note → 🟡 MINOR.
4. A figure that was already validated elsewhere (a reviewed table, an earlier verified report) must
   be read from there, not recomputed: a recomputed figure that differs is suspect first.

## Never

- "Fix" a claim yourself by choosing a value: report it with what the source says.
