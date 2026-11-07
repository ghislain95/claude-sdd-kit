# Tuto — installer et utiliser le workflow SDD avec Claude Code

> **Le plus simple** : copie le prompt de la section « Installer le workflow dans un projet, en un
> seul prompt » du [`README.md`](README.md), colle-le dans Claude Code à la racine de ton projet.
> Claude fait les §2 et §3 de ce guide à ta place. La suite du guide reste utile pour comprendre ce
> qui a été installé et pour le travail au quotidien (§4 et suivants).

Ce guide part d'une machine vierge et va jusqu'au premier change livré. Compte environ 15 min
d'installation machine, puis 30 à 90 min pour `/sdd-core:sdd-init` sur un projet (selon sa taille ;
il travaille en grande partie seul et ne t'interroge qu'à deux moments).

---

## 1. L'idée en une minute

- **La spec est la source de vérité.** Le comportement attendu vit dans `openspec/specs/<domaine>/spec.md`.
  Toute évolution passe par un **change** OpenSpec (`openspec/changes/<id>/` : proposal, spec deltas,
  design, tasks). Les specs ne s'éditent jamais à la main : elles sont mises à jour à l'archivage du change.
- **Des agents spécialisés** (product-owner, architect, un dev par module, tester, code-reviewer,
  doc-writer, devops) font chacun un métier, avec un contexte propre. La session principale route.
- **La review n'est pas optionnelle** : `code-reviewer` relit le diff avant `/opsx:verify`, sans
  politesse, une ligne par problème, et chasse les tests « arrangés pour passer ».
- **Les règles mécaniques sont des contrôles** : un hook bloque les commandes git dangereuses
  (commit sur `main`, force-push, `reset --hard`…), la CI valide les specs et lance les tests.
- **Les faits sont le travail de l'agent** : il ne te demande que des choix, jamais ce que le code
  peut lui dire.

---

## 2. Installer la machine (une fois par développeur)

### 2.1 Outils

| Outil | Pourquoi | Installation (macOS ; Linux : équivalent `apt`) |
|---|---|---|
| Claude Code | — | https://claude.com/claude-code (CLI, app desktop ou extension IDE) |
| Node ≥ 20 | CLI OpenSpec | `brew install node` |
| OpenSpec | cycle des changes | `npm install -g @fission-ai/openspec@latest` |
| jq | hook git (sans jq, **toutes** les commandes `git`/`gh` de l'agent sont bloquées) | `brew install jq` |
| gh | PR, CI | `brew install gh` puis `gh auth login` |
| uv + graphify (optionnel) | carte du code interrogeable | `brew install uv`, `uv tool install "graphifyy[sql]"`, puis `graphify install --platform claude` (skill `/graphify`) |

Vérifie : `node -v && openspec --version && jq --version && gh auth status`.

### 2.2 Profil OpenSpec étendu

Le workflow utilise toutes les commandes `/opsx:*` (new, ff, continue, apply, verify, sync, archive,
bulk-archive, explore, onboard, propose). Dans un terminal :

```bash
openspec config profile
```

Choisis le profil personnalisé et coche tous les workflows. Vérifie avec `openspec config list`.

### 2.3 Plugins Claude Code

Dans une session Claude Code (n'importe quel dossier) :

```
/plugin marketplace add ghislain95/claude-sdd-kit
/plugin install sdd-core@sdd-kit
/plugin install superpowers@claude-plugins-official
```

Optionnels :

```
/plugin install sdd-ui@sdd-kit                     # projets avec une interface web
/plugin marketplace add JuliusBrussee/caveman
/plugin install caveman@caveman                    # réponses compressées (économie de tokens)
```

Pour l'app desktop uniquement, les mods d'affichage (cockpit OpenSpec, cartes, bandeau de session) :
voir https://github.com/ghislain95/claude-mods.

Redémarre la session : `/sdd-core:sdd-init` doit apparaître dans la liste des commandes.

---

## 3. Installer le workflow dans un projet

Ouvre Claude Code **à la racine du dépôt** (arbre git propre de préférence), puis :

```
/sdd-core:sdd-init
```

### Ce qui se passe

| Phase | Ce que fait Claude | Ce que tu fais |
|---|---|---|
| 0. Pré-vol | Vérifie les outils, crée la branche `chore/sdd-init`, repère les fichiers déjà présents | Confirmer `superpowers` installé |
| 1. Rétro-doc | Un sous-agent par module lit le code : stack, commandes de la CI, architecture réelle, conventions, vocabulaire. Lance les tests (ligne de base). Écrit `docs/ARCHITECTURE.md`, les docs de module, le glossaire, des ADR rétro-documentées, la roadmap | **Porte 1** : relire le résumé (règles observées, points à confirmer) et corriger |
| 2. Choix | Une seule série de questions | Niveau d'autonomie git, langue, options, modèle des agents |
| 3. Règles | `openspec init`, `CLAUDE.md`, `AGENTS.md`, agents (un dev par module), `openspec/config.yaml`, docs de process | — |
| 4. Garde-fous | Hook git + sa config, `.claude/settings.json`, workflows CI, `.gitignore` | — |
| 5. Contrôle | Aucun marqueur de template restant, `openspec validate --all`, tests du hook, review de l'installation par le nouvel agent `code-reviewer` | — |
| 6. Livraison | Deux commits (`docs(sdd-init)`, `chore(sdd-init)`), PR selon l'autonomie, rapport final | Lire le rapport, créer ton `.claude/settings.local.json` |

### Les niveaux d'autonomie git

| Niveau | L'agent… | Pour qui |
|---|---|---|
| `autonomy-commit` | committe sur la branche du change ; tu pousses et ouvres la PR | découverte, repo sans GitHub |
| `autonomy-pr` | committe, pousse, ouvre la PR ; **un humain fusionne** | équipe (recommandé au départ) |
| `autonomy-merge` | fusionne aussi, seulement si CI verte et review sans BLOQUANT/MAJEUR | dev solo habitué |

Le niveau est appliqué mécaniquement par `.claude/hooks/block-git-writes.conf` (`ALLOW_PUSH`,
`ALLOW_PR_MERGE`) — tu peux le changer à tout moment en éditant ce fichier.

### Après l'installation

- Crée `.claude/settings.local.json` (gitignoré) à partir de `.claude/settings.local.example.json` si
  `gh` doit utiliser un token dédié au repo. **Ne committe jamais ce fichier.**
- Relis `CLAUDE.md` §« Règles non-négociables » : chaque règle y cite sa preuve ; supprime celles qui
  ne te conviennent pas.
- Lance `/opsx:onboard` pour un premier cycle guidé sur du vrai code.

---

## 4. Au quotidien

### Une feature

```
/opsx:new <change-id>     cadrage : product-owner écrit proposal.md (intent, scope, non-goals)
                           → change structurant (nouveau contrat, migration, choix transverse) :
                             l'architect tente de casser la proposition avant de continuer
/opsx:ff                  architect : spec deltas + design.md + tasks.md
/opsx:apply               les agents de dev exécutent les tâches, tests compris
                           → code-reviewer relit le diff non commité (obligatoire)
/opsx:verify              l'implémentation correspond-elle aux specs ?
                           → commit feat(<id>) sur la branche feat/<id>
/opsx:archive             les deltas sont fusionnés dans openspec/specs/
                           → post-archive : roadmap, impact doc, Purpose des specs, graph
                           → commit chore(<id>), PR
```

Tu peux dire simplement « je veux pouvoir exporter les factures en CSV » : la session route vers
`product-owner` et lance le cycle. Elle annonce toujours l'agent choisi (« Routing → `architect`
parce que… »).

### Un bug

`<module>-dev` reproduit et trouve la cause racine → `tester` écrit le test qui échoue → fix →
`code-reviewer`. Bug trivial (< 30 min, comportement spécifié intact) : pas de change OpenSpec, mais
une branche `fix/<scope>-<desc>` et une PR comme le reste.

### Hygiène de session

| Situation | Outil |
|---|---|
| Session longue, changement de sujet, contexte pollué | `/sdd-core:passation [objectif suivant]` puis `/clear` — préféré à `/compact` |
| Terme métier flou ou contesté | le skill `domain-modeling` met à jour `docs/GLOSSARY.md` |
| Tous les ~5 changes, jamais en cours de change | `/sdd-core:improve-codebase-architecture` |
| Session ratée, post-archive douloureux | `/sdd-core:retro` (améliore l'environnement de l'agent, pas le code) |
| Review UI (si `sdd-ui`) | `/sdd-ui:web-design-guidelines <fichiers>`, `sdd-ui:break-ui` |

---

## 5. Le garde-fou git

Le hook `PreToolUse` lit chaque commande Bash de l'agent (sous-agents compris) comme le shell la
lit, et bloque notamment :

- commit / merge / revert / cherry-pick sur une branche protégée ; tout push d'une branche protégée ;
  push sans remote et branche explicites ; force-push ;
- réécriture d'historique (`rebase`, `commit --amend`, `reset` vers une révision…) ;
- staging en masse (`git add -A`, `git add .`, `commit -a`) — l'agent ajoute par chemins explicites ;
- ce qui jette du travail (`reset --hard`, `clean -f`, `checkout .`, `stash drop`, `branch -D`) ;
- `--no-verify` ; `gh pr merge` autre que `--merge` (et selon `ALLOW_PR_MERGE`).

Faux positifs connus : un `$(…)` qui exécute vraiment une commande git interdite, même dans un message
de commit → passer par `git commit -F <fichier>` ; `mkdir x && cd x && git commit` → deux appels.

Tests : `bash .claude/hooks/block-git-writes.test.sh` (lancés aussi en CI par `tooling.yml`).
C'est un garde-fou contre l'erreur, pas un bac à sable.

---

## 6. Mettre à jour

```
/plugin marketplace update sdd-kit
/plugin update sdd-core@sdd-kit
```

Puis, dans chaque projet installé : `/sdd-core:sdd-init --refresh`. Il compare les fichiers générés
avec la nouvelle version des templates, applique ce qui vient du kit, **garde tes modifications
locales**, et ne touche jamais aux specs, aux changes ni à la rétro-doc.

---

## 7. Pièges connus

| Symptôme | Cause | Fix |
|---|---|---|
| Toute commande `git` de l'agent bloquée | `jq` absent | `brew install jq` |
| `/opsx:ff` ou `/opsx:verify` inconnus | profil OpenSpec minimal | §2.2 puis `openspec update` dans le projet |
| L'agent répond sur un code qui n'existe plus | graph graphify périmé | `graphify update .` (`--force` après suppression ou renommage de fichiers) |
| Un agent invente une règle | règle absente de la rétro-doc | corrige `CLAUDE.md` ou le `CODING_RULES.md` du module : ce sont eux que les agents lisent |
| Les skills se déclenchent hors de propos | trop de skills installés | désinstalle ce qui ne sert pas (`/plugin`) : chaque description entre dans chaque session |
| Deux sessions sur le même checkout mélangent leurs fichiers | arbre de travail partagé | une session par worktree, ou nommer explicitement les chemins à committer |
