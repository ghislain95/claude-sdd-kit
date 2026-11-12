---
name: review-interface
description: Review-harness angle — accessibility, worst-case data, design rules and motion of a UI change.
---

# Review angle — interface

This angle checks what a reviewer can check without knowing the owner's intent: accessibility,
robustness to bad data, consistency with the project's design rules, motion. Whether the screen is
*what the owner wanted* is the intent gate's job, not yours. Format: `../review-harness/FINDINGS.md`.

## Method

1. With the `sdd-ui` plugin installed (its files are under the plugin cache, next to `sdd-core`:
   `<plugins>/sdd-ui/skills/<skill>/`), apply on the changed UI files:
   - `web-design-guidelines` (accessibility and UX rules) — convert each of its remarks into the
     shared format, with a `Fails when` (the user and the action that fails);
   - `break-ui`'s **analysis only**: map the fields the changed components render and pick worst-case
     values; check by reading the code or rendering with those values in a scratch file. Never build
     its demo toggle or fixtures in the project, never wait for a user;
   - `review-animations`' `SKILL.md` and `STANDARDS.md` when motion changed.
   Without `sdd-ui`, check by hand: labels and roles, keyboard path, visible focus, contrast, long and
   empty values, loading and error states.
2. Check the diff against the project's design rules (tokens only, no arbitrary values, components
   from the shared library, copy in the product language) from `CLAUDE.md` and the frontend docs.
3. Severity: an action unusable by keyboard or screen reader, or a layout broken by realistic data →
   🛑 BLOCKER; a state missing (loading, empty, error) → 🔴 MAJOR; inconsistency → 🟡 MINOR.

## Never

- Leave a scratch file or a fixture in the working tree: check `git status` before reporting.

## Mechanical backing

Run what `.sdd/harness.yaml` declares under `mechanical.interface` (accessibility linter, component
tests, visual snapshot tests). When the app can be started, a rendered check of the changed screen
(screenshot at desktop and phone width) is attached to the report.
