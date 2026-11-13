---
name: review-sourced-claims
description: Review-harness angle — every figure, date, cause or 'verified' claim in a change's docs, comments and commits has a checkable source.
---

# Review angle — sourced claims

Agents state plausible facts that nobody checked: a count recomputed differently, a date guessed, a
cause invented to make a story coherent, "tested" without a command. This angle checks each claim
against its source. Format: `../review-harness/FINDINGS.md`.

## Scope

Prose the change adds or modifies: Markdown and text files, **code comments** in the diff, the
**commit messages** of the range (`git log base..head`), and the pull request text when there is one.

## Method

1. List the claims: numbers, dates, versions, causes ("because…"), comparisons, behaviour stated in a
   comment, and statements of verification ("tested", "verified in production", "no impact").
2. For each, find its source: a command output you can re-run, a file and line, a commit, a spec, a
   measured report, the code the comment describes. Re-run the command when it is cheap.
3. Severity:
   - claim contradicted by its source (a comment that says the opposite of the code, a wrong figure)
     → 🛑 BLOCKER in a document others act on (spec, ADR, changelog, report, README), 🔴 MAJOR in a
     comment or commit message;
   - claim with no findable source, in a document others act on → 🔴 MAJOR;
   - unsourced claim in a comment or an internal note → 🟡 MINOR.
4. A figure already validated elsewhere (a reviewed table, an earlier verified report) must be read
   from there, not recomputed: a recomputed figure that differs is suspect first.

## Never

- "Fix" a claim yourself by choosing a value: report it with what the source says.
