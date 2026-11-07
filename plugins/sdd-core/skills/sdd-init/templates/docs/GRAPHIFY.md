<!-- sdd:note: fichier généré SEULEMENT si l'option graphify est active ; sinon ne pas le créer (et ne pas le lier depuis CLAUDE.md ni AGENT_TOOLBOX.md) -->
# Graphify — carte du code interrogeable

> Outil de **lecture/navigation** du code pour les assistants IA (Claude Code). Transforme le repo en **knowledge graph** local et interrogeable. **Pas une source de vérité** : `openspec/specs/` reste la vérité comportementale ; graphify n'écrit rien dans les specs, ne décide rien, ne code rien.

## Pourquoi

Sur un codebase de taille réelle, répondre à « qui appelle X », « qu'est-ce qui relie le module A au module B », « qu'est-ce qui casse si je touche ce type » coûte beaucoup de grep et de lecture. Graphify répond via un graphe (nœuds = symboles, arêtes = calls/imports/inherits, citées `file:line`), avec nettement moins de tokens que le grep aveugle — à mesurer sur ce repo avec `graphify benchmark` (ordre de grandeur constaté sur d'autres projets : ~5×).

Parsing **tree-sitter AST**, local et déterministe, **zéro appel réseau** pour le code. Les docs/PDF/images ne passeraient que par une passe sémantique (LLM), **qui ne tourne pas ici** : voir [Pourquoi la passe sémantique ne tourne pas](#pourquoi-la-passe-sémantique-ne-tourne-pas).

## Prérequis (une fois par dev / CI)

```bash
uv tool install "graphifyy[sql]"   # l'extra [sql] capte aussi les fichiers SQL (migrations, schémas)
graphify --version                  # doit afficher une version
graphify install --platform claude  # installe le skill /graphify au niveau utilisateur (pas dans le repo)
```

Désinstaller : voir [Retrait complet](#retrait-complet).

## Construire / rafraîchir le graph

Le graph vit dans `graphify-out/` (**gitignored**, jamais committé — volumineux et volatil).

```bash
# build initial, code-only (AST local, aucun coût API)
graphify extract . --code-only

# refresh incrémental (ré-extrait seulement les fichiers changés, AST-only)
graphify update .

# le graph est-il périmé vs les fichiers ?
graphify check-update .

# après un GROS refactor / des suppressions : forcer le re-scan
# (sinon des nœuds « fantômes » du code supprimé subsistent)
graphify update . --force
```

**Exclusions** : un `.graphifyignore` (committé, syntaxe `.gitignore`) retire le bruit et rend le graph **déterministe**.

| Exclu | Raison |
|---|---|
| Lockfiles | Énormes, faible valeur |
| `.claude/` | Outillage agent : la doc des skills n'a rien à faire dans le graph du code |
| `**/*.md` | Sans passe sémantique, un markdown ne produit que des nœuds de **titres**, sans arête vers le code ; ajoutés au gré des commits, ils forment un index partiel arbitraire, plus trompeur qu'une absence. Pour chercher dans la doc : grep / lecture directe (`openspec/specs/` reste la vérité) |
| `graphify-out/` | Le graph lui-même |
<!-- sdd:fill: exclusions propres à la stack (stories, code généré, fixtures volumineuses…) avec leur raison — ou rien -->

Les **tests sont gardés** (contexte usage/impact utile). Les dossiers de build déjà dans `.gitignore` sont exclus d'office (respecté par graphify).

> **Après toute modification de `.graphifyignore`, relancer `graphify update . --force`.** Un
> `update` incrémental seul laisse subsister des nœuds fantômes.

## Interroger

```bash
graphify query "<question>"          # traversée BFS pour une question libre (régler avec --budget / --context)
graphify path "<A>" "<B>"            # plus court chemin (relations, cycles) — «no directed path» = découplage réel
graphify explain "<symbole>"         # un nœud + ses voisins, cités file:line + type d'arête (EXTRACTED/INFERRED)
graphify affected "<X>"              # traversée inverse : qui est impacté par X
graphify god-nodes                   # hubs architecturaux (nœuds les plus connectés)
graphify benchmark graphify-out/graph.json   # réduction de tokens mesurée
```

Visualisation : `graphify-out/graph.html` (`--no-viz` au build si > 5000 nœuds). Rapport : `graphify cluster-only . --no-label` génère `GRAPH_REPORT.md` sans coût LLM.

## Place dans le workflow OpenSpec

Le cycle OpenSpec (voir [`CLAUDE.md` §3](../CLAUDE.md)) **ne change pas**. Graphify s'insère en **lecture** à trois moments :

1. **Recon (pré-change)** — interroger le graph (`explain`/`path`/`affected`/`query`) **avant** de lancer des agents d'exploration ou de grep. Lire ensuite les fichiers **ciblés** pointés.
2. **Cadrage / architecture** — `path "<A>" "<B>"` pour vérifier cycles et impact **avant** de proposer un design ; `god-nodes` pour les hubs concernés.
3. **Implémentation** — retrouver un précédent/pattern via `explain`/`query`.

**Fraîcheur = priorité**, portée par la session principale ([`CLAUDE.md` §10](../CLAUDE.md)), pas par les agents :

| Moment | Commande |
|---|---|
| Avant le recon de `/opsx:new` | `graphify update .` puis `graphify check-update .` — cadrer sur un graph périmé produit un proposal faux |
| Avant `/opsx:apply` | `graphify check-update .` ; périmé → `graphify update .` |
| Après `/opsx:archive` | `graphify update . --force` si le change a **supprimé ou renommé** des fichiers, sinon `graphify update .` ; puis `check-update .` |

Après une modif de code notable en cours de tâche : `graphify update .`. Quand on **dispatche un
agent** sur du code, lui rappeler d'interroger le graph **dans le prompt de dispatch** : sa
définition le dit déjà, mais le prompt est le seul levier fiable. Un agent qui doit lancer ces
commandes a besoin de l'outil `Bash`.

**Filet opt-in per-dev** : `graphify hook install` (local, non committé — `.git/hooks/` ne se
partage pas) reconstruit le graph en incrémental après chaque commit ou checkout, en AST seul donc
sans coût API. Il s'ajoute aux trois points ci-dessus sans les remplacer : il ne couvre pas le
`--force` après suppressions.

## Choix d'intégration (assumés)

- **Skill installé au niveau utilisateur** (`graphify install --platform claude`, une fois par dev), **pas committé** dans `.claude/skills/` : il suit la version du CLI de chacun. **Config partagée, pas le graph** : `.graphifyignore` est committé, `graphify-out/` est gitignored et régénéré.
- **Pas de hook graphify committé.** L'auto-nudge (`graphify hook-guard` sur chaque Read/Grep/Bash) est non-bloquant mais **fréquent** et pointe un chemin absolu **non portable**. Un dev qui le veut : `graphify claude install --project` en local — ⚠️ il modifie `.claude/settings.json`, qui est committé (il porte le hook du garde-fou git) : ne pas ajouter cette modification au commit. Retrait : `graphify claude uninstall`.
- **Pas de `watch`** par défaut (éviter les rebuilds incessants).

## Limites

- Un graph **périmé** induit en erreur → toujours refresh + `check-update` avant de s'y fier.
- **La doc n'est pas dans le graph**, garanti par `.graphifyignore` (`**/*.md`), pas par le flag `--code-only` → pas de lien code↔spec.
- La recherche texte libre (`query`) s'évase parfois ; les commandes structurelles (`explain`/`path`/`affected`/`god-nodes`) sont plus tranchantes.
- `god-nodes` remonte par construction les classes utilitaires de test : ce ne sont pas des hubs d'architecture.

### Pourquoi la passe sémantique ne tourne pas

Constats faits sur d'autres projets (graphify 0.9.x), à re-vérifier si la version change :

- `--backend claude` exige `ANTHROPIC_API_KEY`. **Ce n'est pas la CLI** : le nom induit en erreur.
- `--backend claude-cli` passe par la CLI, mais `claude -p` refuse le jeton OAuth de l'abonnement
  (`401 OAuth access token has expired`, même juste après une connexion) ; il veut une clé API.
- `--backend ollama` fonctionne mais est inexploitable en local sur un modèle moyen (quelques
  fichiers en plusieurs dizaines de minutes).

⚠️ Les extras se cumulent explicitement : `uv tool install "graphifyy[sql,ollama]"`. Installer
`[ollama]` seul **désinstalle `[sql]`** et casse silencieusement l'extraction des migrations SQL.

**Preuve que la passe ne tourne pas** : tous les nœuds et arêtes de `graph.json` portent
`_origin: "ast"`.

## Retrait complet

```bash
graphify uninstall                 # retire le skill de toutes les plateformes détectées
rm -rf graphify-out                # supprime le graph local
uv tool uninstall graphifyy        # retire l'outil
```
