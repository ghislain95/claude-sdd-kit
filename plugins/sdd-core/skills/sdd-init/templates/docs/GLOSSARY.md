# Glossary

The shared vocabulary of the domain, for the team and for the agents: a term that contradicts it
during framing gets challenged. Rule: **one concept = one word**. Synonyms go under
_Avoid_, and the OpenSpec spec (`openspec/specs/`) wins in case of conflict. The glossary is
maintained through the `sdd-core:domain-modeling` skill: a
new or disputed term is settled with the user, then written here.

## Format

```
**Order** (`Order`, `order_id`):
A purchase request placed by a customer, identified by its `order_id`. On screen: "order".
_Avoid_: purchase (the payment, not the request), cart (before checkout)
_Source_: `openspec/specs/ordering/spec.md`
```

Rules:

- **Canonical term in {{DOC_LANG}}** in bold, followed by its **code identifier(s)** in
  parentheses and backticks. No identifier: `(no identifier)`.
- **Definition = what it IS**, in one or two sentences. **No implementation details**: no
  threshold, table, migration or class beyond the identifier. Those details live in the
  spec, `MODULES.md` or the code.
- **Only domain-specific terms.** General programming concepts (timeout,
  cache, endpoint) do not belong here.
- `_Avoid_` lists the rejected synonyms; `_Source_` points to the spec (or document, or code
  file) that is authoritative.
- Terms **grouped by theme** (one `###` per theme, under `## Terms`).
- An unresolved conflict is not settled silently: it is marked `⚠️ To settle` in the entry
  and listed under [To settle](#to-settle).

## Terms

<!-- sdd:fill: seed taken from the code — business entities/aggregates/value objects, status enums and recurring screen names. One `###` per theme. Each entry in the format above, `_Source_` = the code file that defines it (no spec yet). Two names for the same concept found in the code → entry marked `⚠️ To settle`. No more than ~20 terms: the most central ones. -->

## To settle

<!-- sdd:fill: list of the vocabulary conflicts found during the reverse documentation (term, observed variants with files, recommendation) — or "No conflict found." -->
