# Convention des templates sdd-init

Les templates ne sont **pas** rendus par un moteur : c'est Claude (skill `sdd-init`) qui les remplit
à partir de la rétro-documentation du projet cible. La convention ci-dessous rend le remplissage
vérifiable : à la fin, `grep -rnE '(^|[^$])\{\{[A-Z_]+\}\}|sdd:(fill|if|endif|each|endeach|note)' <fichiers générés>` doit être vide.

Les templates sont rédigés en **français**. Si le projet choisit des docs en anglais, Claude traduit la
prose au remplissage (identifiants, chemins et commandes inchangés).

## 1. Valeurs simples — `{{NOM}}`

| Variable | Contenu | Exemple |
|---|---|---|
| `{{PROJECT_NAME}}` | Nom du projet | `Billing` |
| `{{PROJECT_PITCH}}` | 1 à 2 phrases : ce que fait le produit, pour qui | `API de facturation pour PME…` |
| `{{DOMAIN_RISKS}}` | Ce qui coûte cher quand ça casse dans ce domaine (à signaler explicitement) | `double facturation, perte de paiement, fuite de données client` |
| `{{STACK_SUMMARY}}` | Stack en une ligne par module | `api : Python 3.12 / FastAPI / SQLAlchemy / Alembic` |
| `{{DEFAULT_BRANCH}}` | Branche protégée | `main` |
| `{{REPO_SLUG}}` | `owner/name` GitHub (vide si pas de remote GitHub) | `acme/billing` |
| `{{DOC_LANG}}` | Langue des docs Markdown et des réponses, **nommée** dans cette langue (prose lisible : « en français ») | `français` |
| `{{CODE_LANG}}` | Langue du code, des commits, des artefacts OpenSpec, nommée dans la langue des docs | `anglais` |
| `{{INSTALL_DATE}}` | Date de l'installation, `AAAA-MM-JJ` (lue avec `date +%F`) | `2026-11-07` |
| `{{AGENT_MODEL}}` | Modèle écrit dans chaque agent (`opus`, `sonnet`, `inherit`) | `opus` |
| `{{CHECK_COMMANDS}}` | Les contrôles de la CI, tous modules, sous leur forme **lançable en local** (même outil, mêmes arguments ; seul l'exécutable peut différer, ex. `python` en CI → `python3` en local — l'écart est alors écrit à côté) | `uv run pytest && uv run ruff check .` |
| `{{OPENSPEC_VERSION}}` | Sortie de `openspec --version` à l'installation, épinglée en CI | `1.16.1` |
| `{{MIGRATION_PATHS}}` | Globs des dossiers de migrations (option `migrations`), pour `migrations.yml` | `migrations/**` |
| `{{ARCH_STYLE}}` | Style d'architecture observé (pas souhaité : observé) | `monolithe modulaire, couches api/service/repository` |

## 2. Sections à rédiger — `<!-- sdd:fill: <consigne> -->`

Un commentaire HTML qui porte une consigne. Claude le **remplace** par du contenu tiré du code
réel (rétro-doc), jamais inventé. Ce qui n'est pas vérifiable dans le code est marqué
« à confirmer » et listé dans le rapport final de `sdd-init`.

```markdown
## Règles non-négociables
<!-- sdd:fill: règles d'architecture observées (couches, dépendances interdites, packages racine) -->
```

## 3. Blocs optionnels — `<!-- sdd:if <option> -->` … `<!-- sdd:endif -->`

Gardés (sans les marqueurs) si l'option est active, supprimés sinon. Pas d'imbrication.
`<!-- sdd:if !<option> -->` pour l'inverse. Un bloc peut aussi être **en ligne**, dans une phrase :
`… lancer les tests<!-- sdd:if graphify --> puis `graphify update .`<!-- sdd:endif -->.`
Dans un fichier YAML ou de config, les marqueurs sont en commentaire (`# sdd:if graphify` … `# sdd:endif`).

**Un marqueur seul sur sa ligne disparaît avec sa ligne** (pas de ligne vide laissée à sa place :
elle casserait un tableau Markdown ou une liste).

| Option | Active quand |
|---|---|
| `graphify` | l'utilisateur a choisi la carte du code graphify |
| `ui` | le projet a une interface web (active aussi le plugin `sdd-ui`) |
| `migrations` | le schéma de base évolue par fichiers versionnés appliqués dans l'ordre : un outil (Flyway, Alembic, Prisma, Rails, golang-migrate…) **ou** des fichiers SQL numérotés (`001_….sql`). Un schéma recréé à chaque démarrage ou généré par l'ORM n'en est pas |
| `caveman` | l'utilisateur a choisi le mode caveman |
| `cockpit` | l'utilisateur a installé les mods desktop `claude-mods` (contrat d'affichage) |
| `autonomy-merge` | l'agent committe, pousse, ouvre **et fusionne** la PR (CI verte + review propre) |
| `autonomy-pr` | l'agent committe, pousse et ouvre la PR ; un humain fusionne |
| `autonomy-commit` | l'agent committe sur la branche ; push et PR par un humain |
| `github` | remote GitHub présent : PR, `gh`, fusion via GitHub. Sans remote → textes « fusion faite par un humain » |
| `ci` | les workflows du kit sont générés : remote GitHub **ou** `.github/workflows/` déjà présent |
| `work-style` | l'équipe adopte le mode de travail du kit (`CLAUDE.md` §12 : cadrage court, jusqu'au bout, rapport structuré, passation) |
| `multi-module` | ≥ 2 modules |
| `devops` | Docker / compose, IaC ou scripts de déploiement présents (une CI seule ne suffit pas) |
| `lean` | module unique **et** moins de ~5 000 lignes de code : jeu de fichiers réduit (pas d'`AGENT_TOOLBOX.md`, `AGENTS.md` réduit à un renvoi) |

Exactement une option `autonomy-*` est active.

## 4. Répétition par module — `<!-- sdd:each module -->` … `<!-- sdd:endeach -->`

Le bloc est dupliqué pour chaque module détecté, avec :

| Variable | Contenu |
|---|---|
| `{{MODULE_NAME}}` | nom court, kebab-case (`api`, `web`, `worker`) |
| `{{MODULE_PATH}}` | dossier relatif à la racine |
| `{{MODULE_STACK}}` | langage, framework, versions épinglées |
| `{{MODULE_CHECK}}` | commande de contrôle du module, forme locale de ce que lance la CI (même règle que `{{CHECK_COMMANDS}}`) |
| `{{MODULE_TEST_KINDS}}` | types de tests utilisés (`pytest unitaires + intégration`, `Vitest + Playwright`) |
| `{{MODULE_DEPS_FILE}}` | fichier où les versions sont épinglées (`pyproject.toml`, `package.json`, `pom.xml`) |
| `{{MODULE_TRIGGERS}}` | mots-clés de déclenchement de l'agent du module, pour sa `description` (ex. `endpoint, service, migration, worker`) |

Un repo à module unique a `{{MODULE_PATH}}` = `.` : ses docs de module vont dans `docs/`. Après
remplissage, **normalise les chemins** : `./docs/x` → `docs/x`, `../.././docs/x` → `../../docs/x`,
`.././docs/x` → `../docs/x`, et vérifie que chaque lien relatif pointe sur un fichier existant.

Un **module** = un ensemble déployable ou testable seul, avec son propre fichier de dépendances
(monorepo : un par app/package significatif ; repo simple : un seul module, le repo).

## 5. Consignes de génération — `<!-- sdd:note: … -->`

Une consigne pour `sdd-init` (ex. « ne générer que si ≥ 2 modules »), **toujours supprimée** du
fichier généré. Placée avant un frontmatter YAML, elle le casse si elle reste : la phase 5 de
`sdd-init` la cherche explicitement.

## 6. Fichiers conditionnels et par module

Fichiers entiers conditionnés (signalés par un `sdd:note` en tête) : `docs/GRAPHIFY.md` et
`misc/graphifyignore` → option `graphify` ; `github/workflows/*` → option `ci` ;
`github/workflows/migrations.yml` → `ci` **et** `migrations`.
`root/AGENTS.lean.md` remplace `root/AGENTS.md` (généré sous le nom `AGENTS.md`) avec `lean` ;
`docs/AGENT_TOOLBOX.md` → sauf `lean` ; `agents/devops.md` → `devops` ;
`agents/full-stack-dev.md` → `multi-module` et un module consomme l'autre (API + client).

`github/workflows/checks.yml` est instancié **une fois par module** en
`.github/workflows/checks-{{MODULE_NAME}}.yml` (filtre de chemins propre au module).

Attention : les workflows contiennent des expressions GitHub `${{ … }}` — ce ne sont **pas** des
variables du kit. Le contrôle final ignore les `{{` précédés de `$`.


Les templates de `module-docs/` et `agents/module-dev.md` sont instanciés **une fois par module** :
`<MODULE_PATH>/docs/CODING_RULES.md`, `.claude/agents/<MODULE_NAME>-dev.md`, etc.
