# docs/GLOSSARY.md — format

```md
### {Groupe, ex. Commandes et livraison}  (sous `## Termes`)

**Commande d'achat** (`PurchaseOrder`, `PurchaseOrderStatus`) :
Engagement d'un client sur une liste d'articles et un prix, avant toute expédition.
_Éviter_ : commande (seul : ambigu avec l'expédition)
_Source_ : `openspec/specs/ordering/spec.md`
```

## Rules

- **Canonical term in the docs language** (product vocabulary, `CLAUDE.md` §Langue), then the
  **code identifier(s)** in backticks, or `(pas d'identifiant)`.
- **Be opinionated.** Several words for one concept → pick the best, list the others under `_Éviter_`.
- **Tight definitions.** One or two sentences: what it IS, not what it does. No implementation
  details (thresholds, tables, migrations, classes beyond the identifier).
- **Only project-specific domain terms.** General programming concepts (timeout, cache, endpoint) don't belong.
- **Group** terms under thematic subheadings.
- Unresolved conflicts are marked `⚠️ À arbitrer` and listed in the final `## À arbitrer`
  section until the user decides.
- An entry in an older format (ex. a legacy table) that a change touches is rewritten in this
  format and removed from there.
