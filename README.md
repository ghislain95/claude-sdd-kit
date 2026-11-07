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

## Contenu

| Plugin | Contenu |
|---|---|
| **`sdd-core`** | `/sdd-core:sdd-init` (rétro-doc + installation du workflow, `--refresh` pour mettre à jour), `/sdd-core:passation`, `/sdd-core:retro`, `sdd-core:domain-modeling`, `/sdd-core:improve-codebase-architecture`, et les templates (agents, `CLAUDE.md`, règles OpenSpec, hook git, CI) |
| **`sdd-ui`** (optionnel) | `web-design-guidelines`, `break-ui`, `emil-design-eng`, `animate`, `review-animations`, `improve-animations` |

Ce que `sdd-init` installe dans le projet : voir [`TUTO.md`](TUTO.md) §3.

## Installation rapide

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
