<!-- sdd:note: ce fichier est copié comme modèle (docs/adr/ADR-000-template.md), {{DOMAIN_RISKS}} remplacé et les placeholders <…> gardés ; les ADR de rétro-doc créés par sdd-init s'appellent ADR-001-<sujet>.md, ADR-002-…, statut « Acceptée (rétro-documentée) », Décideur « existant — à confirmer », sections remplies depuis le code. Retirer cette note dans les deux cas. -->
# ADR-NNN — <Titre court de la décision>

- **Statut** : Proposée | Acceptée | Acceptée (rétro-documentée) | Remplacée par ADR-MMM | Abandonnée
- **Date** : AAAA-MM-JJ
- **Auteur** : <architect (Claude) | nom>
- **Contexte** : <epic, ticket ou change OpenSpec concerné>
- **Décideur** : <qui tranche>

## Contexte

<Quel problème force une décision maintenant ? Quelles contraintes (techniques, produit, coûts,
{{DOMAIN_RISKS}}) ? Ce qui se passe si on ne décide pas. Lier le `design.md` du change si la
décision en vient.>

## Décisions

### 1. <Décision>

<Ce qui est décidé, en une ou deux phrases affirmatives. Puis le détail utile.>

- **Alternative rejetée — <nom>** : <pourquoi pas>.
- **Source** : <doc officielle à la version épinglée dans le fichier de dépendances, ou fichier:ligne
  du code installé ; sans source : « non vérifiée »>.

## Impact (sections à garder seulement si elles s'appliquent)

- **Modules impactés** : <module> : <quoi>.
- **Contrats modifiés** : <API / événement / message / format> : <détails>.
- **Migration / compatibilité** : <schéma, breaking change, rollback>.
- **Risques et mitigations** : <…>.

## Conséquences

- **Positives** : <ce que la décision rend facile>.
- **Négatives / coûts** : <ce qu'elle rend difficile, dette assumée, coûts en latence, perte de
  données, exploitation>.
- **Suivi** : <ce qui devra être revu, et quand (déclencheur)>.
