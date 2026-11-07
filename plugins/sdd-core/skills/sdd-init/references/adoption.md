# Adoption d'un projet déjà outillé, et `--refresh`

## 1. Le projet a déjà des fichiers cibles

Règle : **ce qui existe a été écrit pour une raison.** On fusionne, on n'écrase pas.

| Fichier présent | Conduite |
|---|---|
| `CLAUDE.md` | Lis-le en entier. Garde tout ce qui est propre au projet (règles, contexte, pièges). Ajoute les sections du template qui manquent ; si une section existante contredit le workflow (ex. « commit directement sur main »), signale-la et demande en porte 1 — ne tranche pas seul. |
| `AGENTS.md` (format multi-outils) | Ne le remplace pas : ajoute une section « Équipe d'agents Claude » qui renvoie à `.claude/agents/README.md`. |
| `.claude/agents/<x>.md` | Même nom qu'un template → compare : garde les règles spécifiques de l'existant, ajoute les blocs du template (description UTILISER QUAND, format de sortie, graphify…). Nom différent → garde-le et ajoute-le à la table de routage. |
| `.claude/settings.json` | Fusion JSON : ajoute le hook `PreToolUse` du garde-fou git, ne retire ni ne modifie rien d'autre. |
| `.claude/hooks/*` d'un autre garde-fou git | Montre les deux à l'utilisateur, recommande de n'en garder qu'un (deux hooks contradictoires = blocages incompréhensibles). |
| `openspec/` déjà initialisé | Pas de `openspec init`. `openspec update` pour rafraîchir les commandes. `config.yaml` : fusionne `context` et `rules` (ajoute les règles du template absentes). Les specs existantes ne sont **pas** touchées. |
| `docs/*.md` homonymes | Fusion par section ; ce qui contredit le code observé est signalé dans le rapport (pas corrigé en silence). |
| CI existante | N'ajoute que `openspec.yml` et `tooling.yml` ; ne touche pas aux workflows existants. |

Montre le diff de chaque fichier fusionné dans la porte de validation 1 (résumé : sections
ajoutées / conservées / en conflit).

## 2. Marqueur d'installation

Dernière ligne de `CLAUDE.md` généré :

```markdown
<!-- sdd-kit: installed <version du plugin sdd-core> on <AAAA-MM-JJ> — options: <liste> — autonomy: <niveau> -->
```

Il sert au `--refresh`. Lis la version dans `.claude-plugin/plugin.json` du plugin (deux niveaux
au-dessus de ce skill).

## 3. `/sdd-init --refresh` — resynchroniser avec une nouvelle version du kit

1. Lis le marqueur : version installée, options, autonomie. Absent → ce n'est pas un projet
   installé par le kit : propose une installation complète en mode adoption (§1).
2. Branche `chore/sdd-kit-refresh-<version>`.
3. Pour chaque fichier généré à partir d'un template (`CLAUDE.md`, `AGENTS.md`, `.claude/agents/*`,
   `docs/{CONTRIBUTING,OPENSPEC_GUIDE,AGENT_TOOLBOX,GRAPHIFY}.md`, `openspec/config.yaml`,
   `.claude/hooks/*`, workflows CI du kit) :
   - remplis le **nouveau** template avec les valeurs du projet (relues dans les fichiers actuels,
     pas re-déduites) ;
   - compare au fichier actuel : ce qui diffère vient soit du kit (à appliquer), soit d'une
     modification locale (à garder). En cas de doute sur l'origine d'un écart, garde le local et
     liste-le.
4. Fichiers copiés à l'identique (hook `.sh`/`.pl`/`.test.sh`) : remplacés, puis
   `bash .claude/hooks/block-git-writes.test.sh` ; la `.conf` locale est conservée.
5. Ne touche jamais : `openspec/specs/`, `openspec/changes/`, la rétro-doc (`ARCHITECTURE.md`,
   docs de module, glossaire, ADR, roadmap) — elle appartient au projet.
6. Phase 5 de `SKILL.md` (contrôles), puis un commit `chore(sdd-kit): refresh workflow to <version>`
   avec, dans le corps, ce qui vient du kit et les écarts locaux conservés. Marqueur mis à jour.
