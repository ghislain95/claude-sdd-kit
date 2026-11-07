# docs/GLOSSARY.md — format

```md
### {Group, e.g. Orders and delivery}  (under `## Terms`)

**Purchase order** (`PurchaseOrder`, `PurchaseOrderStatus`):
A customer's commitment to a list of items and a price, before any shipment.
_Avoid_: order (alone: ambiguous with the shipment)
_Source_: `openspec/specs/ordering/spec.md`
```

## Rules

- **Canonical term in the docs language** (product vocabulary, `CLAUDE.md` §Language), then the
  **code identifier(s)** in backticks, or `(no identifier)`.
- **Be opinionated.** Several words for one concept → pick the best, list the others under `_Avoid_`.
- **Tight definitions.** One or two sentences: what it IS, not what it does. No implementation
  details (thresholds, tables, migrations, classes beyond the identifier).
- **Only project-specific domain terms.** General programming concepts (timeout, cache, endpoint) don't belong.
- **Group** terms under thematic subheadings.
- Unresolved conflicts are marked `⚠️ To settle` and listed in the final `## To settle`
  section until the user decides.
- An entry in an older format (e.g. a legacy table) that a change touches is rewritten in this
  format and removed from there.
