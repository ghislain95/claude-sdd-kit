# AGENTS.md — équipe virtuelle Claude pour {{PROJECT_NAME}}

<!-- sdd:note: option lean → ne pas utiliser ce fichier : générer AGENTS.md depuis AGENTS.lean.md -->

Ce document décrit comment monter une **équipe produit** entièrement portée par Claude Code, avec des rôles spécialisés. Chaque rôle est défini par un fichier dans [`.claude/agents/`](.claude/agents/) et est invocable via la commande `/agents` (ou `claude --agent <nom>`).

---

## 1. Pourquoi des sous-agents ?

- **Spécialisation** : chaque agent a un prompt système ciblé (PO, dev, reviewer…). Il ne fait pas le travail d'un autre.
- **Contexte propre** : un sous-agent travaille dans son propre contexte. Le contexte principal reste léger.
- **Rigueur** : un agent reviewer ne se laisse pas attendrir par l'auteur du code (lui-même un autre agent).
- **Reproductibilité** : la même tâche prompte le même rôle de la même façon.

---

## 2. Rôles

| Agent | Quand l'invoquer | Outils typiques |
|---|---|---|
| **product-owner** | Cadrer un nouveau besoin métier, écrire une user story, prioriser, identifier les impacts produit | Read, Grep, Glob, WebFetch, Edit, Write (`proposal.md`), Bash (lecture) |
| **architect** | Designer une fonctionnalité transverse : spec deltas + `design.md`, passe adversariale, ADR si structurant | Read, Grep, Glob, Edit, Write (artefacts du change, ADR), Bash (lecture) |
<!-- sdd:each module -->
| **{{MODULE_NAME}}-dev** | Implémenter dans `{{MODULE_PATH}}` ({{MODULE_STACK}}) en respectant ses `CODING_RULES.md` | Read, Edit, Write, Bash, Grep, Glob |
<!-- sdd:endeach -->
<!-- sdd:if multi-module -->
| **full-stack-dev** | Petite feature qui touche deux modules en un lot cohérent | Tous |
<!-- sdd:endif -->
| **code-reviewer** | Revue d'une PR / d'un diff : sévère, par ligne, aucun éloge | Read, Grep, Bash (git diff, contrôles) |
| **tester** | Écrire / compléter les tests (outils de chaque module : `<module>/docs/TESTING_STRATEGY.md`) | Read, Edit, Write, Bash |
| **doc-writer** | Mettre à jour la doc après une feature (READMEs, `docs/`) | Read, Edit, Write |
<!-- sdd:if devops -->
| **devops** | CI, conteneurs, scripts de build/déploiement, secrets | Read, Edit, Write, Bash |
<!-- sdd:endif -->

**Tous les agents tournent en `model: {{AGENT_MODEL}}`**, écrit explicitement dans chaque fichier plutôt qu'hérité de la session : une session lancée sur un modèle moins cher ne dégrade pas silencieusement un agent. Les outils et skills disponibles en renfort sont catalogués dans [`docs/AGENT_TOOLBOX.md`](docs/AGENT_TOOLBOX.md).

---

## 3. Workflow type pour une feature

Le workflow s'appuie sur **OpenSpec** : les artefacts du change
(`openspec/changes/<id>/` — proposal, spec deltas, design, tasks) sont le
contrat passé d'un agent à l'autre.

```
1. product-owner     ← /opsx:new : proposal.md (intent, scope, non-goals)
1b. architect        ← passe adversariale sur la proposition, si le change est structurant
2. architect         ← /opsx:ff : spec deltas + design.md + tasks
3. <module>-dev      ← /opsx:apply : tasks du module<!-- sdd:if multi-module --> (modules en parallèle si le contrat est stabilisé)<!-- sdd:endif -->
<!-- sdd:if devops -->
3b. devops           ← /opsx:apply : si CI/infra/secrets impactés
<!-- sdd:endif -->
4. tester            ← 1 scénario de delta = 1 test
5. code-reviewer     ← revue du diff non commité (obligatoire, avant verify)
6. /opsx:verify      ← implémentation vs specs, tasks cochées
7. commit            ← l'agent, sur la branche du change (docs/CONTRIBUTING.md §2)
8. /opsx:archive     ← fusion des deltas dans openspec/specs/
9. post-archive      ← roadmap, doc-writer (docs/ ne contredit pas les specs fusionnées ;
                       glossaire) ou « aucun impact doc », `## Purpose` des specs touchées
                       (corrigé par la session qui archive)<!-- sdd:if graphify -->, rafraîchissement du graph<!-- sdd:endif --> ;
                       commit chore(<id>)
<!-- sdd:if autonomy-merge -->
10. PR + fusion      ← l'agent : CI verte + review sans BLOQUANT/MAJEUR, sinon il demande
<!-- sdd:endif -->
<!-- sdd:if autonomy-pr -->
10. PR               ← l'agent ouvre la PR ; un humain fusionne
<!-- sdd:endif -->
<!-- sdd:if autonomy-commit -->
10. push + PR        ← un humain (l'agent ne pousse jamais)
<!-- sdd:endif -->
```

Le cycle de référence est dans [`CLAUDE.md` §3](CLAUDE.md) ; `/opsx:archive` n'intervient qu'**après**
le commit d'implémentation, et la fusion qu'après l'archive.

À chaque étape, le contexte est passé via le résultat de l'agent précédent (résumé court + chemins de fichiers).

---

## 4. Workflow type pour un bug

```
1. <module>-dev   ← reproduire en local + identifier la cause racine
2. tester         ← écrire un test qui échoue
3. <module>-dev   ← fixer ; faire passer le test
4. code-reviewer  ← revue minimale (focus sur la régression)
```

Bug qui contredit une spec → change OpenSpec `fix-<bug>`. Hotfix trivial (< 30 min, comportement spécifié intact) → branche `fix/<scope>-<desc>` sans change.

---

## 5. Conventions communes à tous les agents

Chaque agent hérite implicitement de `CLAUDE.md` et des `CODING_RULES.md` du module dans lequel il opère. En plus :

- **Aucun agent** n'invente un module ou un package racine.
- **Aucun agent** ne commit de secret.
- **Git** : les agents travaillent sur une branche selon [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) §2 ; **aucun agent** ne committe ni ne pousse sur
  `{{DEFAULT_BRANCH}}`, ne force-push ni ne réécrit l'historique. Le hook
  [`.claude/hooks/block-git-writes.sh`](.claude/hooks/block-git-writes.sh) l'impose, sous-agents
  compris. Un sous-agent dispatché pour une tranche ne committe que si son brief le lui demande ;
  sinon c'est l'agent principal qui committe après la review.
- Tout agent qui modifie du code finit par lancer les contrôles du module, **les mêmes que la CI** :
<!-- sdd:each module -->
  - `{{MODULE_PATH}}` : `{{MODULE_CHECK}}`
<!-- sdd:endeach -->
- Tout agent qui modifie un contrat externe le fait naître dans les spec deltas, puis `doc-writer` le documente au post-archive.
<!-- sdd:if graphify -->
- Tout agent qui lit du code interroge d'abord le graph (`graphify explain|affected|path|query`), après `graphify check-update .`.
<!-- sdd:endif -->

---

## 6. Comment ajouter un nouveau rôle

1. Créer `.claude/agents/<nom>.md` avec le frontmatter suivant :
   ```yaml
   ---
   name: <nom>
   description: UTILISER QUAND <déclencheurs concrets>. NE PAS UTILISER <contre-indications>.
   tools: [Read, Edit, Write, Bash, Grep, Glob]   # ou un sous-ensemble
   model: {{AGENT_MODEL}}
   ---
   ```
   Un agent qui doit lancer des commandes de lecture (graphify, git diff, tests) a besoin de `Bash`.
2. Décrire la **mission**, les **lectures obligatoires**, les **règles dures**, le **workflow**, les **livrables attendus** et les **anti-patterns**.
3. Mettre à jour la table de la section 2 ci-dessus et [`.claude/agents/README.md`](.claude/agents/README.md).
4. Tester en l'invoquant sur une petite tâche.

La `description` est ce que lit Claude principal pour router : déclencheurs concrets (« UTILISER QUAND… ») et contre-indications (« NE PAS UTILISER… ») valent mieux qu'une phrase générale.

---

## 7. Invocation

Dans Claude Code :
```
/agents                              # liste les agents disponibles
```

Ou laisser Claude principal **déléguer automatiquement** : il lit la description de chaque agent et choisit le bon selon la table de routage de [`CLAUDE.md` §8](CLAUDE.md).
