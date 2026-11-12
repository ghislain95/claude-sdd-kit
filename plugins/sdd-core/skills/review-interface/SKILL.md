---
name: review-interface
description: Review angle of the harness — accessibility, worst-case data, visual consistency and motion of a UI diff. USE WHEN the review-harness selects the interface angle (a UI component, style, copy or interaction changed), or when asked to review a UI change. DO NOT USE to judge the product intent (that is the owner's QA).
---

# Review angle — interface

This angle checks what a reviewer can check without knowing the owner's intent: accessibility,
robustness to bad data, consistency with the project's design rules, motion. Whether the screen is
*what the owner wanted* is the intent gate's job, not yours. Format: `../review-harness/FINDINGS.md`.

## Method

1. With the `sdd-ui` plugin installed, use its skills on the changed UI files:
   `sdd-ui:web-design-guidelines` (accessibility and UX rules), `sdd-ui:break-ui` (worst-case data),
   and read `sdd-ui:review-animations`' `SKILL.md` and `STANDARDS.md` when motion changed.
   Without `sdd-ui`, check by hand: labels and roles, keyboard path, visible focus, contrast, long and
   empty values, loading and error states.
2. Check the diff against the project's design rules (tokens only, no arbitrary values, components
   from the shared library, copy in the product language) from `CLAUDE.md` and the frontend docs.
3. Severity: an action unusable by keyboard or screen reader, or a layout broken by realistic data →
   🛑 BLOCKER; a state missing (loading, empty, error) → 🔴 MAJOR; inconsistency → 🟡 MINOR.

## Mechanical backing

Run what `.sdd/harness.yaml` declares under `mechanical.interface` (accessibility linter, component
tests, visual snapshot tests). When the app can be started, a rendered check of the changed screen
(screenshot at desktop and phone width) is attached to the report.
