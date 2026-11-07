---
name: domain-modeling
description: Build and sharpen the project's domain vocabulary while framing or designing — challenge terms that conflict with docs/GLOSSARY.md, propose canonical terms for fuzzy ones, stress-test concepts with edge-case scenarios, and update the glossary as terms resolve. Use when a framing/design discussion introduces, renames or disputes a domain concept, or when editing the glossary.
---

# Domain Modeling

Adapted from mattpocock/skills `domain-modeling` (MIT).

This is the *active* discipline: challenging terms, inventing edge-case scenarios, and writing
the glossary down the moment a term crystallises. Merely *reading* the glossary for vocabulary
is not this skill — every framing and design already does that.

## Files

- Glossary: **`docs/GLOSSARY.md`** — canonical term in the docs language (`CLAUDE.md` §Language)
  + code identifier(s), definition, `_Éviter_` synonyms, `_Source_`. Format in
  [GLOSSARY-FORMAT.md](GLOSSARY-FORMAT.md). Entries in an older format (ex. a legacy table)
  migrate to this format when a change touches them.
- Behaviour truth: `openspec/specs/`. Business model reference: `docs/ROADMAP.md` (its business-model
  section, if any) and `docs/ARCHITECTURE.md`. Module boundaries: each module's
  `<module>/docs/MODULES.md` (or `CODING_RULES.md`). Decisions: `docs/adr/ADR-NNN-<titre>.md`.

## During the session

**Challenge against the glossary.** A term used in a way that conflicts with the glossary is
called out immediately (ex.): "The glossary defines *Account* as the billing entity, but you seem
to mean a single user login. Which is it?"

**Sharpen fuzzy language.** Overloaded word → propose the canonical term (ex.): "By *order* do you
mean a *PurchaseOrder* (what the customer bought) or a *Shipment* (what leaves the warehouse)?
They're different things."

**Discuss concrete scenarios.** Stress-test relationships with specific edge cases — ex. a parent
with no children, an item moved between containers mid-process, a platform admin with no tenant,
two sources reporting the same event, a user attached to two tenants — to force precise
boundaries.

**Cross-reference with code.** When the user states how something works, check the code (if
`graphify-out/` exists, graph first: `graphify query` / `explain`). Contradiction → surface it: "The code does X (`file:line`), but you
just said Y. Which is right?"

**Update the glossary inline.** When a term is resolved — *by the user*, not by you alone —
update `docs/GLOSSARY.md` right away. The glossary holds no implementation details: no
thresholds, table names, migrations or algorithms. It is not a spec.

**Code identifiers.** Code keeps its own language (usually English). When a new concept gets a
code name, record the docs-language ↔ code pair in the glossary so product and code keep the same concept under one name each.

## Decisions worth recording

Offer to record a decision as an ADR (`docs/adr/`) only when all three hold:
1. **Hard to reverse** — changing your mind later has a real cost;
2. **Surprising without context** — a future reader will wonder "why this way?";
3. **A real trade-off** — there were genuine alternatives.

If any is missing, skip it: the decision lives in the change's `design.md`.
