# Agents Claude Code — {{PROJECT_NAME}}

Chaque fichier `*.md` de ce dossier définit un **sous-agent** spécialisé. Claude principal les
choisit seul d'après leur `description` (« UTILISER QUAND / NE PAS UTILISER ») ; on peut aussi les
lister avec `/agents`. Workflow et conventions : [`/AGENTS.md`](../../AGENTS.md).

## Table de routage

**Avant d'écrire ou de coder, identifier le bon agent et déléguer.** N'agir soi-même que si aucun
agent ne correspond ou si la tâche est triviale (lecture rapide, question factuelle).

| L'utilisateur demande… | Agent |
|---|---|
| « je veux une feature X », « on devrait pouvoir Y », besoin métier flou, prioriser, user story, proposal | `product-owner` |
| « comment on devrait faire X », choix transverse<!-- sdd:if multi-module -->, impact > 1 module<!-- sdd:endif -->, nouveau contrat externe, spec deltas, design.md, ADR, passe adversariale | `architect` |
<!-- sdd:each module -->
| implémentation dans `{{MODULE_PATH}}` ({{MODULE_STACK}}) | `{{MODULE_NAME}}-dev` |
<!-- sdd:endeach -->
<!-- sdd:if multi-module -->
| petite feature cohérente touchant plusieurs modules | `full-stack-dev` |
<!-- sdd:endif -->
| « review ce diff », « valide ma PR », « regarde ce que j'ai fait » ; systématique après une implémentation | `code-reviewer` |
| écrire / compléter des tests, test de régression | `tester` |
| mettre à jour la doc, README, glossaire, `docs/` ; post-archive | `doc-writer` |
<!-- sdd:if devops -->
| infra, conteneurs, CI, secrets, configs de prod | `devops` |
<!-- sdd:endif -->

### Règles de routage
- Plusieurs agents possibles → celui qui **maximise la spécialisation**<!-- sdd:if multi-module --> (l'agent du module plutôt que `full-stack-dev` si la tâche ne touche qu'un module)<!-- sdd:endif -->.
- Demande ambiguë → **1 question max** à l'utilisateur, puis router.
- Feature large → cycle OpenSpec : `product-owner` (proposal) → [`architect` passe adversariale]
  → `architect` (deltas + design + tasks) → agents de dev (tasks) → `tester` → `code-reviewer` →
  `/opsx:verify` → commit → `/opsx:archive` → post-archive (`doc-writer` si impact doc).
- Bug → agent de dev du module (reproduire, cause racine), `tester` (test qui échoue), fix,
  `code-reviewer`.
- Toujours annoncer l'agent choisi avant délégation : « Routing → `<agent>` parce que <raison> ».

### Quand ne pas déléguer
- Question factuelle (« où est défini X ? ») → réponse directe.
- Lecture de fichier demandée explicitement → exécuter.
- Tâche < 5 min, single-shot, sans risque → exécuter, et signaler qu'elle eût pu être déléguée.

## Modèle et outils
- **Tous les agents tournent en `model: {{AGENT_MODEL}}`**, écrit explicitement dans chaque
  fichier plutôt qu'hérité : une session lancée sur un modèle moins cher ne dégrade pas un agent
  en silence.
- Les outils sont ceux du frontmatter de chaque agent (source de vérité). `architect` et
  `product-owner` ont `Write`/`Edit`, limités par consigne à leurs livrables
  (`openspec/changes/<id>/`, `docs/adr/` ; `proposal.md`) ; leur `Bash` sert à la lecture.
- `code-reviewer` n'a pas `Edit` : il signale, ne corrige pas.

## Ajouter un agent
1. Créer `<nom>.md` :
   ```yaml
   ---
   name: <nom>
   description: UTILISER QUAND <déclencheurs concrets>. NE PAS UTILISER <cas voisins → autre agent>.
   tools: [Read, Edit, Write, Bash, Grep, Glob]
   model: {{AGENT_MODEL}}
   ---
   ```
2. Décrire mission, lectures obligatoires, règles dures, workflow, anti-patterns, livrable.
3. Mettre à jour la table de routage ci-dessus, [`/AGENTS.md`](../../AGENTS.md) et le `CLAUDE.md`.
4. Tester en l'invoquant sur une petite tâche.
