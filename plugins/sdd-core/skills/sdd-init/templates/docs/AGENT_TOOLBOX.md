<!-- sdd:note: ne pas générer avec l'option lean (module unique, petit projet) ; supprimer ce commentaire -->
# {{PROJECT_NAME}} — Boîte à outils des agents

Catalogue des skills, hooks et contrôles retenus pour le développement assisté de {{PROJECT_NAME}},
**et de ceux écartés, avec la raison**, pour ne pas refaire l'évaluation. Base : le kit
`claude-sdd-kit` (plugins `sdd-core`<!-- sdd:if ui --> et `sdd-ui`<!-- sdd:endif -->), installé par `/sdd-core:sdd-init`.

La table « demande → outil » à utiliser au quotidien est dans [`CLAUDE.md` §11](../CLAUDE.md).
Ce document en est le catalogue complet. Toute addition ou retrait d'outil s'y note, datée.

## 1. Principes

- **OpenSpec est le process.** Les packs « cycle complet » (spec → plan → build → test → review →
  ship) recouvrent ce qu'OpenSpec fait déjà ; on en prend des idées, pas les plugins.
- **Jamais de plugin entier qui doublonne superpowers.** Des skills `tdd` / `debugging` /
  `code-review` concurrents se déclenchent au hasard. On *vendorise* le skill utile, seul.
- **Lire avant d'installer.** Un `SKILL.md` devient des instructions pour l'agent : on le lit en
  entier, on vérifie l'absence de scripts ou d'effets de bord, puis on le copie dans
  `.claude/skills/<nom>/` avec `LICENSE` et `SOURCE.md` (dépôt, commit, date, modifié ou non).
- **Peu de skills.** Chaque description de skill entre dans le contexte de chaque session et
  peut se déclencher hors de propos. Un skill qui ne sert pas est retiré.
- **Une règle mécanique devient un contrôle, pas une consigne** (hook, test d'architecture, lint,
  CI). Les consignes écrites sont réservées aux jugements.

## 2. Retenus

| Outil | Source | Ce que c'est | Quand |
|---|---|---|---|
| OpenSpec (`/opsx:*`) | [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) (CLI npm `@fission-ai/openspec`) | Specs source de vérité + changes (proposal, deltas, design, tasks), archive qui fusionne les deltas | Toute feature non triviale ([`OPENSPEC_GUIDE.md`](OPENSPEC_GUIDE.md)) |
| superpowers | plugin officiel `claude-plugins-official` | `brainstorming`, `systematic-debugging`, `test-driven-development`, `verification-before-completion`… | Partout, sauf pour remplacer `/opsx:new` / `/opsx:ff` |
| `/sdd-core:passation` | `sdd-core` (idées : mattpocock `handoff`) | Document de reprise : objectif, état, décisions, tenté et raté, faits vérifiés vs supposés, fichiers clés, prochaine étape, mode de travail. Écrit dans `.claude/passation/` (gitignoré) + presse-papier | Avant `/clear` ou une nouvelle session, dès que le contexte s'alourdit ou que le sujet change |
| `sdd-core:domain-modeling` | `sdd-core` (mattpocock, adapté) | Challenge les termes contre [`GLOSSARY.md`](GLOSSARY.md), propose le terme canonique, met à jour le glossaire quand l'utilisateur tranche | Cadrage, design ; aussi lu par `product-owner`, `architect`, `code-reviewer` |
| `/sdd-core:improve-codebase-architecture` | `sdd-core` (mattpocock, adapté) | Audit des points chauds (git<!-- sdd:if graphify --> + graphify<!-- sdd:endif -->) → rapport des modules « creux » → cadrage du candidat choisi → ligne dans [`ROADMAP.md`](ROADMAP.md), section « Backlog — chantiers flaggés » | À la main, tous les ~5 changes, jamais en cours de change |
| `/sdd-core:retro` | `sdd-core` (mattpocock, adapté) | Rétro sur l'**environnement** de l'agent : navigation, contrôles automatiques, règles du reviewer, fichiers de pilotage, économie d'outils | Après un archive douloureux ou une session ratée |
<!-- sdd:if ui -->
| `/sdd-ui:web-design-guidelines` | `sdd-ui` (vercel-labs/agent-skills) | Lint accessibilité / UX (`aria`, focus, formulaires, reduced motion…) en `fichier:ligne`, règles récupérées en ligne à chaque exécution | Review de tout change UI |
| `sdd-ui:break-ui` | `sdd-ui` (emilkowalski/skills) | Données pire cas (libellés longs, compteurs énormes, zéro, champs manquants) derrière un toggle DEV-only ; l'utilisateur bascule et juge | Avant de livrer un écran de données |
| `sdd-ui:emil-design-eng`, `sdd-ui:animate`, `/sdd-ui:review-animations`, `sdd-ui:improve-animations` | `sdd-ui` (emilkowalski/skills) | Finition UI, construction d'une animation dans le bon ordre de décision, revue du code de mouvement, audit motion. ⚠️ Les plans d'`improve-animations` sont des **entrées** pour `/opsx:new` ou la roadmap, pas un process parallèle | Polish d'un composant, nouvelle transition, review d'un diff qui touche du mouvement |
<!-- sdd:endif -->
| Hook [`block-git-writes.sh`](../.claude/hooks/block-git-writes.sh) | `sdd-core` (mattpocock `git-guardrails`, adapté) | `PreToolUse` sur Bash : impose la partie mécanique des règles git ([`CONTRIBUTING.md`](CONTRIBUTING.md) §2). Lit la commande comme le shell (heredocs, guillemets, substitutions), suit le dossier réel (`cd`, `git -C`, `switch`). Réglages dans `block-git-writes.conf`. Coût mesuré : ~70-110 ms par appel | Toujours actif ([`.claude/settings.json`](../.claude/settings.json)) ; agit aussi sur les sous-agents. Sans `jq`, il bloque toute commande `git`/`gh`. Faux positifs assumés : un `$(…)` non échappé qui exécuterait vraiment une commande git interdite, même dans un message → citer le délimiteur du heredoc (`<<'EOF'`) ou passer par `git commit -F <fichier>` ; un dossier créé dans la même commande avant le `cd` compte comme inexistant → deux appels ; un `git switch <branche>; git commit` sans `&&` est jugé sur la branche de départ. `git <op> --abort/--quit` reste permis |
<!-- sdd:if ci -->
| CI GitHub Actions | `sdd-core` | [`openspec.yml`](../.github/workflows/openspec.yml) : `openspec validate --all` (CLI épinglé) + garde « specs modifiées sans change ». `checks-<module>.yml` (un par module, dans [`.github/workflows/`](../.github/workflows/)) ou la CI existante du projet : les contrôles de chaque module. [`tooling.yml`](../.github/workflows/tooling.yml) : suite de régression du hook git | À chaque PR et push sur `{{DEFAULT_BRANCH}}`, filtrés par chemin |
<!-- sdd:endif -->
<!-- sdd:if graphify -->
| Graph graphify déterministe | graphify (`uv tool install "graphifyy[sql]"`, skill via `graphify install --platform claude`) | Carte du code interrogeable ; [`.graphifyignore`](../.graphifyignore) exclut `.claude/` et `**/*.md` : le graph ne contient que du code (voir [`GRAPHIFY.md`](GRAPHIFY.md)) | Toujours ; pour chercher dans la doc : grep / lecture directe |
<!-- sdd:endif -->
<!-- sdd:if caveman -->
| caveman | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | Réponses compressées (~-75 % de tokens), status line | Par choix du développeur, au niveau utilisateur |
<!-- sdd:endif -->
<!-- sdd:if cockpit -->
| claude-mods | [ghislain95/claude-mods](https://github.com/ghislain95/claude-mods) | Mods de l'app desktop : cockpit OpenSpec, messages en cartes, bandeau de session, tâches de fond | App desktop uniquement, au niveau utilisateur |
<!-- sdd:endif -->
<!-- sdd:fill: contrôles automatiques propres au projet déjà en place (test d'architecture, lint d'import, garde de migrations…) — ou rien si aucun -->

### Idées intégrées dans les agents (sans nouveau skill)

- **Baisse de qualité masquée** (idée : addyosmani `constraint-driven-development`) → `code-reviewer` :
  nouveau test désactivé ou sauté, suppression d'avertissement (`@SuppressWarnings`, `# type: ignore`,
  `@ts-ignore`, `eslint-disable`), assertion affaiblie, seuil ou timeout relevé, `catch` silencieux,
  `continue-on-error` en CI = BLOQUANT sauf justification écrite.
- **Décisions sourcées** (idée : addyosmani `source-driven-development`) → `architect` et règle
  `design` de `openspec/config.yaml` : une décision qui dépend d'une librairie cite sa source **à la
  version épinglée du repo**, sinon elle est marquée « non vérifiée ».
- **Ajouter → migrer → retirer** (idée : mattpocock `to-tickets`) → `architect` et règle `tasks` de
  `openspec/config.yaml` : un changement à large rayon se découpe en trois temps, chacun avec un
  build vert.
- **Les faits sont le travail de l'agent** (idée : mattpocock `grilling`) → `product-owner` : au
  cadrage, on ne demande jamais à l'utilisateur ce que le code, les specs ou le graph peuvent dire.
- **Passe adversariale** → `architect` et [`CLAUDE.md` §3](../CLAUDE.md) : avant `/opsx:ff` d'un
  change structurant, on tente de casser la proposition (hypothèses fragiles, alternatives
  ignorées, coûts cachés, conflits avec un ADR).
- **Ordre testé selon le contrat** → `tester` : une assertion d'ordre seulement si la spec impose
  un ordre ; sinon comparaison sans ordre, ou fixture dans le désordre pour un test de tri.

## 3. Différés : à reconsidérer quand le besoin apparaît

| Outil | Pourquoi pas maintenant | Déclencheur |
|---|---|---|
<!-- sdd:if ui -->
| impeccable (pbakaus) | Bon pack design général, mais il télécharge un binaire natif, installe des hooks par projet et fait doublon avec d'autres skills UI | Refonte visuelle : à tester **à la place** d'un autre pack UI, pas en plus |
| addyosmani `/webperf` | Audit Lighthouse / Core Web Vitals | Mise en production publique d'un front web |
<!-- sdd:endif -->
<!-- sdd:if graphify -->
| Passe sémantique graphify sur la doc | Aucun backend exploitable sans clé API (voir [`GRAPHIFY.md`](GRAPHIFY.md)) | Clé API d'un modèle bon marché disponible |
<!-- sdd:endif -->
<!-- sdd:fill: outils repérés pendant sdd-init mais pas installés, avec leur déclencheur — ou supprimer la ligne -->

## 4. Écartés

| Outil | Raison |
|---|---|
| Plugins mattpocock / addyosmani entiers | Collisions avec superpowers ; `implement` de mattpocock **committe tout seul** ; le cycle d'Addy duplique OpenSpec |
| `grill-me` / `grilling` | Doublon de `brainstorming` et du cadrage `product-owner` |
<!-- sdd:if ui -->
| taste-skill | Son `SKILL.md` exclut explicitement « dashboards, data tables, multi-step product UI » |
| `minimalist-ui` | Ses interdits (pas d'Inter, pas d'ombres, pas d'icônes Lucide) se battent avec la plupart des design systems existants |
| anti-ai-slop (hallmark & co) | Pas de source de référence ; générateurs de pages marketing |
<!-- sdd:endif -->
| Playwright MCP, agent-browser | Doublons du navigateur intégré de l'app et de Claude in Chrome. À revoir seulement pour de l'E2E scripté (Playwright test, pas MCP) |
| `find-skills` | `npx skills find <requête>` fait la même chose |
| Garde d'architecture CI par `grep` | Un vrai test d'architecture (ArchUnit, import-linter, dependency-cruiser…) fait mieux et tourne avec les tests |
| Proxy « économiseur de tokens » qui réécrit les sorties shell (`git`, `grep`…) | Étude JetBrains : +7,6 % de coût en effort bas (p=0,004), aucun gain en effort haut ; économies auto-déclarées gonflées car Claude Code tronque déjà les sorties. Sorties corrompues constatées : `git log` sans les 2 derniers commits, `grep` à 0 résultat sur un diff non vide |
| Routage automatique requête par requête vers un modèle moins cher | Comportement en plein tour non documenté ; on garde le routage explicite par agent |

## 5. Modèles et sessions

- **Tous les agents tournent en `model: {{AGENT_MODEL}}`**, écrit explicitement dans chaque
  `.claude/agents/*.md` plutôt qu'hérité : une session lancée sur un modèle moins cher ne dégrade
  pas silencieusement un agent.
- **`/compact` ou `/sdd-core:passation` ?** `/compact` garde la forme de la conversation, impasses
  comprises. Préférer la passation + session neuve dès qu'on change de sujet ou après un debug
  laborieux.
- **Messagerie entre sessions** (`SendMessage` / `ListAgents`, natif) : possible, mais la passation
  couvre le besoin plus simplement.
