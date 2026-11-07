# claude-sdd-kit

Un workflow de développement **spec-driven** pour Claude Code, installable dans n'importe quel
projet, quel que soit le langage : cycle OpenSpec, sous-agents spécialisés, review obligatoire,
garde-fous git mécaniques et CI.

Les règles d'un projet ne se copient pas d'un autre projet. `/sdd-core:sdd-init` commence donc par
**rétro-documenter le code réel** (modules, stack, commandes de la CI, architecture observée,
vocabulaire), et ne génère les règles et les agents qu'à partir de ce qu'il a prouvé.

```
/opsx:new → [passe adversariale] → /opsx:ff → /opsx:apply → code-reviewer → /opsx:verify
         → commit → /opsx:archive → post-archive → PR (+ fusion selon le niveau d'autonomie)
```

## Installer le workflow dans un projet, en un seul prompt

1. Ouvre Claude Code **à la racine du projet** (CLI, app desktop ou extension IDE).
2. Copie le prompt ci-dessous et colle-le tel quel.
3. Claude installe les outils et les plugins, rétro-documente le code, génère les règles, les agents,
   le garde-fou git et la CI, puis committe le tout sur une branche `chore/sdd-init`. Il ne t'arrête
   qu'à trois moments : avant d'installer un outil sur ta machine, pour valider ce qu'il a compris du
   code, et pour une série de choix (autonomie git, langue, options).
4. À la fin, redémarre Claude Code : les agents, le hook et les commandes `/opsx:*` sont chargés.

Compte de 30 à 90 minutes selon la taille du projet. Le même prompt, relancé sur un projet déjà
installé, le met à jour avec la dernière version du kit en gardant tes modifications.

```text
Installe dans ce projet le workflow de développement « sdd-kit » (https://github.com/ghislain95/claude-sdd-kit) : spec-driven development avec OpenSpec, agents spécialisés, review obligatoire, garde-fou git et CI. Déroule les étapes dans l'ordre, sans en sauter.

1. Prérequis — vérifie avec Bash : `node -v` (≥ 20), `openspec --version`, `jq --version`, `perl -v`, `gh auth status`, `git status`. Pour chaque outil manquant, donne-moi la commande d'installation (npm install -g @fission-ai/openspec@latest, brew install jq, brew install gh…) et attends mon accord avant d'installer quoi que ce soit sur ma machine. Sans jq, le garde-fou git bloquerait toutes tes commandes git : c'est bloquant.

2. Plugins Claude Code — lance via Bash :
   claude plugin marketplace add ghislain95/claude-sdd-kit
   claude plugin install sdd-core@sdd-kit
   claude plugin install superpowers@claude-plugins-official
   S'ils sont déjà installés, mets-les à jour à la place : claude plugin marketplace update sdd-kit, puis claude plugin update sdd-core@sdd-kit.
   Si la marketplace officielle est inconnue : claude plugin marketplace add anthropics/claude-plugins-official, puis relance l'install.
   Si le projet a une interface web, propose-moi aussi : claude plugin install sdd-ui@sdd-kit.

3. Profil OpenSpec — lance `openspec config list`. Le workflow a besoin de ces workflows : propose, explore, new, continue, apply, ff, sync, archive, bulk-archive, verify, onboard. S'il en manque, demande-moi de lancer `openspec config profile` dans mon terminal (c'est interactif), choisis le profil personnalisé, coche-les tous, puis reprends.

4. Installation dans le projet — les plugins installés ne seront chargés qu'à la prochaine session, donc ne cherche pas /sdd-core:sdd-init maintenant. Lis directement ~/.claude/plugins/marketplaces/sdd-kit/plugins/sdd-core/skills/sdd-init/SKILL.md et suis-le à la lettre, avec ~/.claude/plugins/marketplaces/sdd-kit/plugins/sdd-core/skills/sdd-init/ comme dossier de base (templates/, references/). Si la dernière ligne de CLAUDE.md contient « sdd-kit: installed », le projet est déjà installé : suis le mode --refresh du skill. Respecte ses points d'arrêt : la porte de validation après la rétro-documentation, et la série de questions de la phase 2. Ne pose que des choix ; tout ce que le code, la CI ou git peuvent te dire, cherche-le toi-même. Ne travaille jamais sur la branche principale.

5. Fin — donne-moi le rapport final prévu par le skill, puis dis-moi de redémarrer Claude Code pour charger les agents, le hook et les commandes /opsx:*. Mon premier pas ensuite sera /opsx:onboard (premier cycle guidé) ou le premier change baseline-<domaine> que tu m'auras proposé.

Guide complet si besoin : ~/.claude/plugins/marketplaces/sdd-kit/TUTO.md
```

Ce que le prompt change sur ta machine, hors du projet : il ajoute le catalogue `sdd-kit` et active
les plugins `sdd-core` et `superpowers` dans `~/.claude/settings.json`, donc pour tous tes projets.
`sdd-core` ne contient que des skills : aucun hook, agent ni serveur MCP. `superpowers` ajoute en
plus un hook de début de session qui charge son guide d'usage des skills. Pour retirer le kit :
`claude plugin uninstall sdd-core@sdd-kit` puis `claude plugin marketplace remove sdd-kit`.

## Contenu

| Plugin | Contenu |
|---|---|
| **`sdd-core`** | `/sdd-core:sdd-init` (rétro-doc + installation du workflow, `--refresh` pour mettre à jour), `/sdd-core:passation`, `/sdd-core:retro`, `sdd-core:domain-modeling`, `/sdd-core:improve-codebase-architecture`, et les templates (agents, `CLAUDE.md`, règles OpenSpec, hook git, CI) |
| **`sdd-ui`** (optionnel) | `web-design-guidelines`, `break-ui`, `emil-design-eng`, `animate`, `review-animations`, `improve-animations` |

Ce que `sdd-init` installe dans le projet : voir [`TUTO.md`](TUTO.md) §3.

## Installation à la main (sans le prompt)

Dans Claude Code :

```
/plugin marketplace add ghislain95/claude-sdd-kit
/plugin install sdd-core@sdd-kit
/plugin install superpowers@claude-plugins-official
```

Puis, dans le projet à outiller :

```
/sdd-core:sdd-init
```

Le guide complet (prérequis, ce qui se passe, usage au quotidien, pièges) est dans [`TUTO.md`](TUTO.md).

## Provenance

Extrait du workflow du projet WifiSense, puis généricisé. Les skills vendorisés gardent leur
`LICENSE` et un `SOURCE.md` (dépôt d'origine, modifications). Le hook git est adapté de
`mattpocock/skills` (`git-guardrails-claude-code`, MIT).
