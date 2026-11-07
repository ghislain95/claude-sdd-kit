---
name: sdd-init
description: Installe le workflow SDD (OpenSpec + agents spécialisés + review obligatoire + garde-fous git + CI) dans le projet courant, quel que soit le langage — rétro-documente d'abord le code réel, puis génère CLAUDE.md, agents, règles OpenSpec, hook et CI à partir de ce qui a été observé. Aussi `--refresh` pour resynchroniser un projet déjà installé avec une nouvelle version du kit.
argument-hint: "[--refresh]"
disable-model-invocation: true
---

# sdd-init — installer le workflow SDD dans un projet

Tu installes, dans le dépôt courant, le workflow décrit dans le `TUTO.md` du kit : spec-driven
development avec OpenSpec, sous-agents spécialisés, review obligatoire avant verify, post-archive,
garde-fou git mécanique et CI. Le processus est **identique d'un projet à l'autre** ; les règles,
elles, **sortent du code du projet** — jamais d'un autre projet, jamais d'une supposition.

Ce dossier (le « base directory » donné à l'invocation du skill) contient :
- `templates/` — modèles à remplir, convention dans [`templates/VARIABLES.md`](templates/VARIABLES.md) (lis-la en premier) ;
- `references/recon.md` — la checklist de rétro-documentation ;
- `references/adoption.md` — projet qui a déjà un `CLAUDE.md`, des agents ou OpenSpec, et le mode `--refresh`.

`$ARGUMENTS` contient `--refresh` → suis directement `references/adoption.md` §3.

## Principes (à tenir pendant toute l'installation)

1. **Les faits sont ton travail.** Ne demande jamais à l'utilisateur ce que le code, la CI, les
   fichiers de dépendances ou l'historique git peuvent dire. Tu ne demandes que des **choix**.
2. **Observé ≠ souhaité.** Une règle « non-négociable » n'entre dans `CLAUDE.md` que si elle est
   vérifiée dans le code (cite `fichier:ligne`) **ou** tranchée par l'utilisateur. Le reste va en
   « à confirmer » dans le rapport final.
3. **Une règle mécanique devient un contrôle**, pas une consigne : si une règle peut être vérifiée
   par un linter, un test d'architecture ou la CI, propose ce contrôle (ligne de backlog dans
   `docs/ROADMAP.md`) au lieu d'écrire de la prose seulement.
4. **Rien n'est écrasé sans être lu.** Un fichier cible existant → `references/adoption.md`.
5. **Peu, mais juste.** Un agent, un skill ou une section qui ne sert pas ce projet n'est pas
   généré (ex. pas d'agent `devops` sans Docker ni CI ; pas de `full-stack-dev` avec un seul module).
6. **Vérifier avant de conclure** : chaque commande de contrôle écrite dans un fichier a été lancée
   au moins une fois pendant l'installation, et son résultat figure dans le rapport.

## Phase 0 — Pré-vol

1. `git rev-parse --show-toplevel` (pas un dépôt git → proposer `git init`, sinon s'arrêter),
   `git status --short` (arbre sale → demander s'il faut continuer : l'installation se committe à
   part), `git branch --show-current`, branche par défaut (`git symbolic-ref refs/remotes/origin/HEAD`
   ou, à défaut, `main`/`master` local), remote (`git remote -v` → remote GitHub ? → option `github` ; remote GitHub ou `.github/workflows/`
   présent → option `ci`). Date du jour : `date +%F` (→ `{{INSTALL_DATE}}`).
2. Crée la branche de travail **avant toute écriture** : `git switch -c chore/sdd-init`.
3. Outils — vérifie, et pour chaque manquant donne la commande d'installation (ne l'installe pas
   sans accord) :

   | Outil | Vérif | Install | Requis |
   |---|---|---|---|
   | Node ≥ 20 + npm | `node -v` | nodejs.org / `brew install node` | oui (OpenSpec) |
   | OpenSpec CLI | `openspec --version` | `npm install -g @fission-ai/openspec@latest` | oui |
   | jq | `jq --version` | `brew install jq` / `apt install jq` | oui (sans jq, le hook bloque tout `git`/`gh`) |
   | perl | `perl -v` | présent sur macOS/Linux | oui (lecteur shell du hook) |
   | gh | `gh auth status` | `brew install gh` | si option `github` |
   | uv + graphify | `graphify --version` | `uv tool install "graphifyy[sql]"` | si option `graphify` |

4. Plugins compagnons : demande à l'utilisateur de lancer `/plugin` et de confirmer que
   `superpowers` est installé (le workflow s'appuie sur `systematic-debugging`,
   `verification-before-completion`, `test-driven-development`). S'il manque :
   `/plugin install superpowers@claude-plugins-official`.
5. Fichiers déjà présents (`CLAUDE.md`, `AGENTS.md`, `.claude/agents/`, `.claude/settings.json`,
   `openspec/`, `docs/`) → note-les : ils passent par `references/adoption.md`.

## Phase 1 — Rétro-documentation (le code d'abord)

Suis [`references/recon.md`](references/recon.md). Résumé :

1. **Carte des modules** : liste les modules (VARIABLES.md §4), leur stack et versions épinglées,
   leurs commandes de build / test / lint **telles que la CI les lance** (ou, sans CI, telles que
   les scripts du projet les définissent).
2. **Recon parallèle** : un sous-agent `Explore` (« very thorough ») par module, plus un pour le
   transverse (CI, infra, docs existantes, historique git) — petit projet (module unique, quelques
   milliers de lignes) : fais la recon toi-même, c'est plus rapide. Chacun rend un rapport structuré selon
   `recon.md` §3, chaque affirmation sourcée `fichier:ligne`. Tu agrèges.
3. **Ligne de base** : lance les commandes de contrôle de chaque module. Rouge → note-le tel quel
   (« la ligne de base est rouge : N tests en échec ») ; **ne corrige rien** pendant l'installation.
4. Écris la rétro-doc à partir des templates :
   - `docs/ARCHITECTURE.md` (`templates/docs/ARCHITECTURE.md`)
   - par module : `<module>/docs/CODING_RULES.md`, `MODULES.md`, `TESTING_STRATEGY.md`
     (`templates/module-docs/`) — repo à module unique : directement dans `docs/`
   - `docs/GLOSSARY.md` : amorce depuis les noms du domaine (entités, agrégats, états, rôles)
     trouvés dans le code — définitions courtes, marquées « à confirmer » si déduites
   - `docs/adr/ADR-001-…` : une ADR par **décision structurante déjà prise** et visible dans le code
     (choix de framework, de base, d'auth, de style d'archi), statut `Acceptée (rétro-documentée)`
   - `docs/ROADMAP.md` : objectif tiré du README et des docs existantes (sinon une ligne « à
     confirmer », sans poser de question en plus) + section « Backlog — chantiers flaggés » alimentée
     par ce que la recon a trouvé (TODO/FIXME notables, dettes, contrôles mécaniques à ajouter)
5. **Porte de validation 1** — présente à l'utilisateur un résumé court : modules, stack, commandes
   et leur état, 5 à 10 règles d'architecture observées (avec preuve), risques du domaine supposés,
   points « à confirmer ». Il corrige ; tu ne passes à la phase 2 qu'après son accord.
6. **Options déduites, pas demandées** : `multi-module` (≥ 2 modules), `devops` (Docker, IaC ou
   scripts de déploiement — une CI seule ne suffit pas), `migrations` (VARIABLES §3), `github`, `ci`,
   `lean` (module unique et < ~5 000 lignes de code : `wc -l` sur les fichiers source, hors tests
   et dépendances). Annonce-les dans la porte 1, l'utilisateur peut les contester.

## Phase 2 — Choix (une seule série de questions)

Pose **en une fois** (outil de question, ≤ 4 questions, chaque option expliquée, ta recommandation
en premier) les choix que le code ne peut pas trancher :

1. **Niveau d'autonomie git** — `autonomy-merge` (l'agent committe, pousse, ouvre et fusionne la PR
   si CI verte + review sans BLOQUANT/MAJEUR) · `autonomy-pr` (un humain fusionne) ·
   `autonomy-commit` (l'agent ne pousse pas). Recommande `autonomy-pr` pour une équipe qui découvre
   le workflow, `autonomy-merge` pour un dev solo habitué. Sans remote GitHub : `autonomy-commit`.
2. **Langue** des docs et des réponses (français / anglais) ; code, commits et artefacts OpenSpec
   restent en anglais sauf choix contraire explicite.
3. **Options** (multi-sélection) : `graphify` (carte du code ; proposé coché au-delà de ~20 k
   lignes, décoché en dessous — un petit projet se lit plus vite qu'il ne s'interroge),
   `ui` (proposé coché si le projet a une interface web : plugin `sdd-ui`), `work-style` (proposé
   coché : le mode de travail du kit dans `CLAUDE.md` §12 — cadrage court avec exemples, autonomie
   jusqu'au bout une fois le cadrage validé, rapport final structuré, passation), `caveman` /
   `cockpit` (préférences d'affichage, installées au niveau utilisateur, voir TUTO).
4. **Modèle des agents** (`opus` recommandé : la qualité de la review et de la passe adversariale
   en dépend ; `inherit` pour suivre le modèle de la session).

`{{DOMAIN_RISKS}}` : propose une formulation déduite de la recon et fais-la valider dans la même
série (option « autre » pour corriger).

## Phase 3 — Règles, agents, OpenSpec

1. **OpenSpec** :
   - `openspec init --tools claude` (non interactif). Il génère `openspec/` et les commandes
     `/opsx:*` + skills `openspec-*` dans `.claude/`.
   - Le workflow utilise le jeu étendu (`new`, `ff`, `continue`, `apply`, `verify`, `sync`,
     `archive`, `bulk-archive`, `explore`, `onboard`, `propose`). `openspec config list` : s'il en
     manque, demande à l'utilisateur de lancer `openspec config profile` dans son terminal
     (interactif), puis lance `openspec update`.
   - Note `openspec --version` (→ `{{OPENSPEC_VERSION}}`, épinglé dans la CI).
   - Remplace `openspec/config.yaml` par `templates/openspec/config.yaml` rempli. `context` = une
     synthèse **courte** (≤ 25 lignes : pitch, stack, 5 à 8 règles d'archi critiques, risques,
     langues) qui renvoie aux docs pour le détail — il est injecté dans chaque artefact, chaque ligne
     coûte. En anglais (`{{DOMAIN_RISKS}}` traduit). `rules` gardées, blocs `# sdd:if` résolus.
   - **Pas de rétro-spec massive.** Les specs naissent avec les changes. Propose, dans le rapport
     final, 1 à 3 changes `baseline-<domaine>` pour les domaines les plus critiques : spec deltas
     `ADDED` qui décrivent le comportement **existant**, tâches = tests de caractérisation qui le
     figent. C'est la seule façon propre de rétro-spécifier (les specs ne s'éditent jamais à la main).
     Donne pour chacun la commande prête à lancer (`/opsx:new baseline-<domaine>`) et les 3 à 5
     comportements qu'il figera.
2. **Fichiers racine** : `CLAUDE.md` et `AGENTS.md` depuis `templates/root/` (option `lean` :
   `AGENTS.lean.md`, écrit sous le nom `AGENTS.md`).
3. **Docs de process** : `docs/CONTRIBUTING.md`, `docs/OPENSPEC_GUIDE.md`, `docs/AGENT_TOOLBOX.md`
   (sauf option `lean`), et `docs/GRAPHIFY.md` si option `graphify`, depuis `templates/docs/`.
4. **Agents** (`templates/agents/` → `.claude/agents/`) :
   - toujours : `product-owner`, `architect`, `code-reviewer`, `tester`, `doc-writer`, `README.md` ;
   - `devops` si option `devops` (Docker, IaC, déploiement ; une CI seule ne le justifie pas) ;
   - `module-dev.md` instancié **une fois par module** → `.claude/agents/<module>-dev.md`, rempli
     avec la stack, les règles et les commandes **de ce module** ;
   - `full-stack-dev` seulement si `multi-module` et que l'un consomme l'autre (API + client).
   - `{{AGENT_MODEL}}` écrit en dur dans chaque frontmatter.
5. **Remplissage** — pour chaque fichier : variables, `sdd:fill` (contenu tiré de la rétro-doc,
   jamais générique : « respecter les bonnes pratiques » est interdit, nomme la règle et sa preuve),
   `sdd:if`/`sdd:endif` résolus (un marqueur seul sur sa ligne part avec sa ligne), `sdd:each`
   dépliés, `sdd:note` supprimés, chemins normalisés (VARIABLES §4). Traduis la prose si les docs
   sont en anglais. Les ADR rétro-documentées suivent `templates/docs/adr/ADR-000-template.md`.
6. **Marqueur** : dernière ligne de `CLAUDE.md` = marqueur d'installation (`references/adoption.md`
   §2) — il sert à `/sdd-core:sdd-init --refresh`.

## Phase 4 — Garde-fous

1. **Hook git** : copie `templates/claude/hooks/block-git-writes.{sh,pl,test.sh,conf}` dans
   `.claude/hooks/` (`chmod +x` les `.sh`), remplis la `.conf` (branche protégée, niveau
   d'autonomie). `templates/claude/settings.json` → `.claude/settings.json` (fusion si présent :
   ajoute le hook `PreToolUse`, ne retire rien). Lance `bash .claude/hooks/block-git-writes.test.sh`
   → doit finir par `ALL n CASES OK`.
   ⚠️ À partir de là, le hook est actif pour toi aussi : `git add` par chemins explicites, jamais
   sur la branche protégée, message long via `git commit -F <fichier>`.
2. **CI** (option `ci`) : `templates/github/workflows/{openspec,tooling}.yml` →
   `.github/workflows/` ; `checks.yml` → un `checks-<module>.yml` par module ; `migrations.yml` si
   option `migrations` (aucune migration déjà mergée modifiée, supprimée ou renommée). CI déjà
   présente → n'ajoute que `openspec.yml`, `tooling.yml` (et `migrations.yml`), et vérifie que la CI
   existante lance bien les mêmes commandes que `{{CHECK_COMMANDS}}` (sinon, signale l'écart).
3. **Fichiers divers** : `templates/misc/gitignore-additions` → ajouté à `.gitignore` (sans
   doublon) ; `templates/misc/worktreeinclude` → `.worktreeinclude`. Option `graphify` :
   `templates/misc/graphifyignore` → `.graphifyignore`, puis `graphify update .` et
   `graphify check-update .` ; si le skill `graphify` n'est pas dans ta liste de skills, demande à
   l'utilisateur de lancer `graphify install --platform claude` puis de redémarrer la session.
4. `templates/claude/settings.local.example.json` : **ne le copie pas en `settings.local.json`**.
   Mentionne-le dans le rapport : chaque dev crée le sien (token `gh` personnel, jamais committé).

## Phase 5 — Contrôle

Tout doit passer, sinon corrige avant de livrer :

```bash
grep -rnE '(^|[^$])\{\{[A-Z_]+\}\}|sdd:(fill|if|endif|each|endeach|note)' CLAUDE.md AGENTS.md .claude/agents .claude/hooks .claude/settings.json docs openspec/config.yaml .github .gitignore .worktreeinclude .graphifyignore 2>/dev/null   # vide
openspec validate --all
bash .claude/hooks/block-git-writes.test.sh                      # ALL n CASES OK, quel que soit le niveau d'autonomie
python3 -c "import json; json.load(open('.claude/settings.json'))"
# YAML : le premier outil disponible
for f in openspec/config.yaml .github/workflows/*.yml; do ruby -ryaml -e "YAML.load_file('$f')" 2>/dev/null || python3 -c "import yaml,sys; yaml.safe_load(open('$f'))" || echo "YAML KO: $f"; done
```

plus : chaque commande citée dans `CLAUDE.md` §« Avant de finir » lancée au moins une fois ; chaque
lien relatif des fichiers générés pointe sur un fichier existant (vérifie-les un par un, surtout
avec `MODULE_PATH=.`) ; aucune mention d'une stack, d'un outil ou d'un domaine absents du projet.

Puis dispatche `code-reviewer` (le nouvel agent du projet) sur le diff de l'installation : mission
= cohérence des règles générées avec le code réel (une règle non prouvée = 🔴 MAJOR). Corrige les
BLOQUANT/MAJEUR.

## Phase 6 — Livraison

1. Deux commits sur `chore/sdd-init`, chemins explicites :
   - `docs(sdd-init): reverse-document architecture, modules and conventions` (phase 1) ;
   - `chore(sdd-init): install spec-driven workflow, agents and git guardrails` (phases 3-4).
   Corps : ce qui a été observé vs tranché, ligne de base des tests.
2. Selon l'autonomie : `autonomy-commit` → s'arrêter là ; sinon `git push -u origin chore/sdd-init`
   et `gh pr create` ; `autonomy-merge` → fusion seulement si CI verte (le hook impose `--merge`).
3. **Rapport final** (structuré) :
   - **Fait** : fichiers générés, par phase.
   - **Décisions** : choix de la phase 2.
   - **Observé vs à confirmer** : règles prouvées (nombre) ; liste des « à confirmer ».
   - **Ligne de base** : commandes de contrôle et résultat chiffré.
   - **Attendu de toi** : créer `.claude/settings.local.json` (token gh), relire `CLAUDE.md` §5,
     installer les plugins optionnels choisis.
   - **Prochaine étape** : `/opsx:onboard` pour un premier cycle guidé, ou le premier
     `baseline-<domaine>` proposé, ou `/opsx:new <id>` sur le premier ticket de `docs/ROADMAP.md`.
