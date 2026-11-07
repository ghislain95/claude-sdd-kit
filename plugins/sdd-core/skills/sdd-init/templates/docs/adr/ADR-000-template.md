<!-- sdd:note: this file is copied as a template (docs/adr/ADR-000-template.md), {{DOMAIN_RISKS}} replaced and the <…> placeholders kept; the reverse-documentation ADRs created by sdd-init are named ADR-001-<topic>.md, ADR-002-…, status "Accepted (reverse-documented)", Decider "existing — to be confirmed", sections filled from the code. Remove this note in both cases. -->
# ADR-NNN — <Short title of the decision>

- **Status**: Proposed | Accepted | Accepted (reverse-documented) | Superseded by ADR-MMM | Abandoned
- **Date**: YYYY-MM-DD
- **Author**: <architect (Claude) | name>
- **Context**: <epic, ticket or OpenSpec change concerned>
- **Decider**: <who decides>

## Context

<What problem forces a decision now? What constraints (technical, product, costs,
{{DOMAIN_RISKS}})? What happens if we do not decide. Link the change's `design.md` if the
decision comes from it.>

## Decisions

### 1. <Decision>

<What is decided, in one or two affirmative sentences. Then the useful details.>

- **Rejected alternative — <name>**: <why not>.
- **Source**: <official doc at the version pinned in the dependency file, or file:line
  of the installed code; with no source: "unverified">.

## Impact (keep these sections only if they apply)

- **Impacted modules**: <module>: <what>.
- **Modified contracts**: <API / event / message / format>: <details>.
- **Migration / compatibility**: <schema, breaking change, rollback>.
- **Risks and mitigations**: <…>.

## Consequences

- **Positive**: <what the decision makes easy>.
- **Negative / costs**: <what it makes hard, accepted debt, costs in latency, data
  loss, operations>.
- **Follow-up**: <what will need to be reviewed, and when (trigger)>.
