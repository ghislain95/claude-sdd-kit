# Contributing

Conventions transverses pour contribuer à {{PROJECT_NAME}}.

---

## 1. Langue

- **Prose** (issues, PRs, docs, commentaires de review) : **{{DOC_LANG}}**.
- **Code** (identifiants, noms de fichiers, commentaires inline techniques), **messages de commit** et **artefacts OpenSpec** : **{{CODE_LANG}}**.
- Pas de mélange de langues dans un même identifiant.

## 2. Git

Règles communes aux humains et aux agents.
<!-- sdd:if autonomy-merge -->
Les agents (sous-agents compris) committent, poussent, ouvrent et fusionnent les PR **eux-mêmes**, en suivant cette section ; le hook décrit plus bas en impose la partie mécanique.
<!-- sdd:endif -->
<!-- sdd:if autonomy-pr -->
Les agents (sous-agents compris) committent, poussent et ouvrent les PR **eux-mêmes** ; la fusion reste humaine. Le hook décrit plus bas impose la partie mécanique.
<!-- sdd:endif -->
<!-- sdd:if autonomy-commit -->
Les agents (sous-agents compris) committent sur la branche du change ; push, PR et fusion restent humains : **l'agent ne pousse jamais**, tout `git push` est bloqué par le hook (`ALLOW_PUSH=0`). Le hook décrit plus bas impose la partie mécanique.
<!-- sdd:endif -->

### Branches
- `{{DEFAULT_BRANCH}}` : branche stable. Elle ne bouge **que par <!-- sdd:if github -->une PR fusionnée<!-- sdd:endif --><!-- sdd:if !github -->une fusion faite par un humain<!-- sdd:endif -->** : jamais de commit ni de push direct, hotfix compris.
- Change OpenSpec : `<type>/<change-id>` — ex. `feat/user-invitations`, `fix/refresh-token-rotation`.
- Hors change : `<type>/<scope>-<desc>` — ex. `fix/api-input-validation`, `docs/roadmap-resync`, `chore/tooling-hook-update`.

`<type>` = le type Conventional Commits principal de la branche ; `<scope>` ∈ { <!-- sdd:fill: noms courts des modules ({{MODULE_NAME}}), plus `docs`, `tooling`, `ci` --> } ; `<desc>` en kebab-case {{CODE_LANG}}.

- Session dans un worktree créé par l'app (nom de branche imposé) : renommer la branche selon la convention avant le premier push (`git branch -m <nom>`).
- Une branche est supprimée après fusion, en local (`git branch -d`)<!-- sdd:if github --> et sur le remote (`git push origin --delete <branche>`)<!-- sdd:endif -->.

### Commits — Conventional Commits
```
<type>(<scope>): <description impérative et courte>

<corps descriptif : ce qui change + les décisions clés>
```
Types : `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `build`, `ci`.

**Scope**
- Un commit qui appartient à un **change OpenSpec** a pour scope **l'id du change** : `feat(user-invitations): …`, `chore(user-invitations): …`.
- Sinon, le scope est le **module** (`<module>`, `<module>/<sous-domaine>`), ou `docs`, `ci`, `tooling` (outillage de dev/agents hors change : hooks, skills).

**Message = sujet + corps descriptif, toujours, en {{CODE_LANG}}.** Sujet impératif et court ; le corps dit ce qui change (quoi) et les décisions clés ; jamais le one-liner seul. Aucune attribution Claude : ni trailer `Co-Authored-By`, ni mention « Generated with Claude Code ».

**Règles d'un commit**
- Un commit = une tranche cohérente (un module, les tests, la doc…) ; pas de commit « wip ».
- Staging par **chemins explicites** (`git add <chemins>`) : jamais `git add -A` / `.` / `-u`, ni `git commit -a` — un commit n'embarque que ce qu'on a décidé d'y mettre.
- Avant un commit de **code** : contrôles du module touché au vert (les mêmes commandes que la CI) et review `code-reviewer` faite sur le diff. Avant tout commit qui touche `openspec/` : `openspec validate --all`.
- Jamais de réécriture : pas d'`--amend`, pas de `rebase`, pas de `reset` vers une révision, pas de force-push. Une erreur se corrige par un nouveau commit.
- Un message long ou qui cite des commandes (`--amend`, `` `git pull` ``…) : l'écrire dans un fichier et passer `git commit -F <fichier>` (`gh pr create --body-file <fichier>`), plutôt qu'un `-m`.

### Séquence d'un change OpenSpec
Le même ordre que le cycle de [`CLAUDE.md`](../CLAUDE.md) §3, sur la branche `<type>/<change-id>` :
1. `docs(<id>): …` — cadrage : proposal, puis deltas, design, tasks (un ou deux commits).
2. `/opsx:apply` → review `code-reviewer` du diff → `/opsx:verify` OK → `feat|fix|…(<id>): …`, un commit par tranche cohérente d'implémentation.
3. `/opsx:archive` + post-archive → `chore(<id>): archive change, sync specs, post-archive`.
<!-- sdd:if autonomy-merge -->
4. Push de la branche, PR, fusion (ci-dessous).
<!-- sdd:endif -->
<!-- sdd:if autonomy-pr -->
4. Push de la branche, PR (ci-dessous) ; fusion humaine.
<!-- sdd:endif -->
<!-- sdd:if autonomy-commit -->
4. L'agent s'arrête au dernier commit ; un humain pousse, ouvre la PR s'il y a un remote, et fusionne.
<!-- sdd:endif -->

Hors change (hotfix, outillage, doc) : même chemin en plus court — branche `<type>/<scope>-<desc>`, review `code-reviewer` si du code change, commit(s)<!-- sdd:if !autonomy-commit -->, PR<!-- sdd:endif --><!-- sdd:if autonomy-merge -->, fusion<!-- sdd:endif -->.

### Ce que le hook impose
Le hook [`.claude/hooks/block-git-writes.sh`](../.claude/hooks/block-git-writes.sh) (enregistré dans [`.claude/settings.json`](../.claude/settings.json)) bloque, pour un agent (sous-agents compris) :
- `commit`, `merge`, `revert`, `cherry-pick` sur une branche protégée. La branche est celle du dossier où la commande s'exécute vraiment : le `cwd`, puis chaque `cd`/`pushd`/`popd` et `git -C <dossier>` (un sous-shell rend le dossier à sa sortie), et un `git switch|checkout <branche>` placé plus tôt dans la même commande — vers une branche protégée, compté tout de suite ; vers une autre branche, seulement si la commande suivante est chaînée par `&&` (un switch qui échoue arrête la chaîne). Un dossier ou une branche impossible à résoudre (`$VAR`, `$(…)`, `cd -`, dossier inexistant) compte comme protégé : écrire des chemins littéraux, et faire `git worktree add <dossier>` dans un appel séparé du `cd <dossier>` qui suit ;
- tout push d'une branche protégée (y compris via `HEAD`, `@` ou une référence `$…` quand on est dessus), un push sans remote **et** branche explicites (`git push -u origin <branche>`), le force-push (`--force*`, `-f`, `+refspec`, `--mirror`, `--all`)<!-- sdd:if autonomy-commit --> — et ici **tout** `git push` (`ALLOW_PUSH=0`)<!-- sdd:endif --> ;
- `pull` sans `--ff-only`, avec rebase, ou, sur une branche protégée, d'une autre branche qu'elle-même ;
- la réécriture d'historique : `rebase`, `commit --amend`, `reset` vers une révision, `branch -f`, `am`, `commit-tree`, `filter-branch` ;
- le staging en masse : `add -A` / `.` / `./` / `..` / `*` / `-u`, `commit -a` ;
- ce qui jette du travail : `reset --hard`, `clean -f/--force`, `checkout .`/`-f`, `switch --discard-changes`, `restore .`, `stash drop/clear`, `branch -D`/`-M` ;
- `--no-verify` ;
- `gh pr merge` autrement qu'en `--merge` (pas de `--squash`, `--rebase`, `--admin`, `--auto`)<!-- sdd:if !autonomy-merge -->, et ici **tout** `gh pr merge` (`ALLOW_PR_MERGE=0`)<!-- sdd:endif -->.

**Réglages** — [`.claude/hooks/block-git-writes.conf`](../.claude/hooks/block-git-writes.conf) (committé, lu par le hook s'il existe) :

| Clé | Défaut | Effet |
|---|---|---|
| `PROTECTED_BRANCHES` | `main\|master` | Branches protégées, séparées par `\|` (ici `{{DEFAULT_BRANCH}}`) |
| `ALLOW_PUSH` | `1` | `1` : l'agent pousse sa branche (jamais une branche protégée) ; `0` : tout `git push` bloqué (un humain pousse) |
| `ALLOW_PR_MERGE` | `1` | `1` : `gh pr merge --merge` permis à l'agent ; `0` : tout `gh pr merge` bloqué (fusion humaine) |

Avant les contrôles, la commande est lue comme le shell la lit : échappements, commentaires `#` et corps de heredoc cités sont écartés, et les chaînes entre guillemets qui contiennent des espaces (messages, corps de PR) sont neutralisées — leur texte n'est jamais lu comme une option ou une commande. Ce que le shell exécute (`$(…)`, accents graves, y compris dans des guillemets doubles ou un heredoc non cité) reste contrôlé.

Tests : `bash .claude/hooks/block-git-writes.test.sh`<!-- sdd:if ci -->, lancés aussi en CI à chaque modification du hook ([`tooling.yml`](../.github/workflows/tooling.yml))<!-- sdd:endif -->.<!-- sdd:if !lean --> Détail : [`AGENT_TOOLBOX.md`](AGENT_TOOLBOX.md).<!-- sdd:endif --> C'est un **garde-fou contre l'erreur, pas un bac à sable** (`sh -c "…"`, `eval` volontaires non couverts) ; sans protection de branche côté serveur, la règle « `{{DEFAULT_BRANCH}}` ne bouge que par <!-- sdd:if github -->une PR<!-- sdd:endif --><!-- sdd:if !github -->une fusion humaine<!-- sdd:endif --> » repose sur ce hook et sur cette discipline. Sans `jq`, le hook bloque toute commande `git`/`gh` jusqu'à son installation.

**Restent à l'utilisateur**, hors git : les décisions de cadrage, tout engagement de dépense, toute action irréversible sur la prod ou sur des données.

<!-- sdd:if !github -->
### Fusion
- Pas de remote GitHub : la branche est relue (`code-reviewer` sans BLOQUANT ni MAJEUR ouvert ; pour un change, `/opsx:verify` OK et change archivé), puis **un humain** la fusionne dans `{{DEFAULT_BRANCH}}` en merge commit (`git merge --no-ff <branche>`).
<!-- sdd:endif -->
<!-- sdd:if github -->
### Pull Requests
- Titre = sujet du commit principal.
- Description en {{DOC_LANG}} : contexte, choix techniques, impact, tests effectués<!-- sdd:if ui -->, captures d'écran<!-- sdd:endif -->. Aucune attribution Claude.
- 1 PR = 1 sujet (un change OpenSpec, ou un correctif). Hors change, pas de mélange de modules sans raison.
- CI verte obligatoire : les workflows de [`.github/workflows/`](../.github/workflows/). Ils sont filtrés par chemin : une PR qu'aucun ne concerne (doc seule, par exemple) ne déclenche aucun check — la condition est alors remplie, à condition que les vérifications locales aient tourné.
- Review : la revue `code-reviewer` du diff est obligatoire ; elle tient lieu d'approbation quand le développeur est seul sur le dépôt.
<!-- sdd:endif -->
<!-- sdd:if autonomy-merge -->
- **Un agent fusionne lui-même** seulement si : CI verte, review `code-reviewer` sans BLOQUANT ni MAJEUR ouvert, et — pour un change OpenSpec — `/opsx:verify` OK et change archivé sur la branche. Sinon il s'arrête et demande à l'utilisateur.
- Fusion en **merge commit** (ni squash ni rebase), titre `<sujet> (#N)` : `gh pr merge <n> --merge --subject "<sujet> (#<n>)"`.
- Après fusion, dans le checkout principal : `git switch {{DEFAULT_BRANCH}} && git pull --ff-only`, puis suppression de la branche (`git branch -d <branche>`, `git push origin --delete <branche>`). Depuis un worktree, `{{DEFAULT_BRANCH}}` est déjà extraite ailleurs : supprimer seulement la branche distante ; la branche locale et le worktree se nettoient depuis le checkout principal (`git worktree remove` puis `git branch -d`).
<!-- sdd:endif -->
<!-- sdd:if autonomy-pr -->
- L'agent ouvre la PR, donne son lien et l'état de la CI, puis s'arrête : **un humain fusionne**, en merge commit.
<!-- sdd:endif -->
<!-- sdd:if github -->
- Accès : `gh` doit voir le dépôt. Côté agents, un token limité au dépôt peut être posé en `GH_TOKEN` dans `.claude/settings.local.json` (gitignoré, copié dans les worktrees par [`.worktreeinclude`](../.worktreeinclude)). **Jamais dans `settings.json`, qui est committé.** Sans accès,<!-- sdd:if !autonomy-commit --> l'agent pousse la branche et donne à l'utilisateur le lien d'ouverture de la PR<!-- sdd:endif --><!-- sdd:if autonomy-commit --> l'utilisateur pousse la branche et ouvre la PR lui-même<!-- sdd:endif -->.
<!-- sdd:endif -->

## 3. Style de code

<!-- sdd:each module -->
### `{{MODULE_PATH}}` ({{MODULE_STACK}})
- Voir [`{{MODULE_PATH}}/docs/CODING_RULES.md`](../{{MODULE_PATH}}/docs/CODING_RULES.md).
<!-- sdd:fill: 2-3 règles phares du module, tirées de son CODING_RULES.md -->
<!-- sdd:endeach -->

## 4. Tests

<!-- sdd:each module -->
- **`{{MODULE_PATH}}`** : {{MODULE_TEST_KINDS}} — `{{MODULE_CHECK}}`. Voir [`TESTING_STRATEGY.md`](../{{MODULE_PATH}}/docs/TESTING_STRATEGY.md).
<!-- sdd:endeach -->

## 5. Documentation

- Toute fonctionnalité ajoutée met à jour le README du module concerné si l'API publique change.
- Toute évolution d'un contrat observable **naît dans les spec deltas** du change OpenSpec (`openspec/changes/<id>/specs/`) ; la doc de `docs/` est mise à jour ensuite, au post-archive (`doc-writer`).
- Si un concept métier nouveau apparaît : entrée dans [`GLOSSARY.md`](GLOSSARY.md).
- Une décision structurante (techno, contrat transverse, style d'architecture) : un ADR dans [`adr/`](adr/).

## 6. Sécurité

- Jamais de secret commité (`.env.local`, secrets CI, `.claude/settings.local.json`).
- Validation stricte de toute entrée externe.
<!-- sdd:fill: règles de sécurité observées propres au projet (auth, rate-limit, données sensibles à ne pas logger) -->
