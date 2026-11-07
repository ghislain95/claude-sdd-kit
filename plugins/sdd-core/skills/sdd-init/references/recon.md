# Rétro-documentation — checklist

But : décrire le projet **tel qu'il est**, avec une preuve pour chaque affirmation, assez précisément
pour que les règles et les agents générés ensuite soient justes. Pas de jugement de valeur, pas de
« devrait » : ce qui est souhaitable va dans le backlog, pas dans la rétro-doc.

## 1. Détecter les modules et les commandes

Cherche les fichiers de dépendances et de build, à toute profondeur (hors `node_modules`, `vendor`,
`target`, `dist`, `build`, `.venv`) :

| Écosystème | Fichiers | Commandes (à lire, pas à deviner) |
|---|---|---|
| JS / TS | `package.json`, `pnpm-workspace.yaml`, `turbo.json`, `nx.json` | `scripts` (`test`, `lint`, `type-check`, `build`) ; gestionnaire = lockfile présent |
| Python | `pyproject.toml`, `setup.cfg`, `requirements*.txt`, `tox.ini`, `noxfile.py` | `[tool.pytest]`, `[tool.ruff]`, `[tool.mypy]`, scripts `uv`/`poetry`/`hatch` |
| JVM | `pom.xml`, `build.gradle(.kts)`, `settings.gradle` | `./mvnw test`, `./gradlew check` ; version JDK (`maven.compiler.release`, toolchain) |
| Go | `go.mod`, `go.work` | `go test ./...`, `go vet`, `golangci-lint` si config |
| Rust | `Cargo.toml` (workspace) | `cargo test`, `cargo clippy`, `cargo fmt --check` |
| .NET | `*.sln`, `*.csproj` | `dotnet test`, `dotnet format --verify-no-changes` |
| Ruby | `Gemfile`, `Rakefile` | `bundle exec rspec`, `rubocop` |
| PHP | `composer.json` | `scripts`, `phpunit`, `phpstan` |
| Autres | `Makefile`, `justfile`, `Taskfile.yml`, `docker-compose*.yml`, `Dockerfile` | cibles déclarées |

**Source de vérité des commandes, dans l'ordre** : la CI (`.github/workflows`, `.gitlab-ci.yml`,
`Jenkinsfile`, `azure-pipelines.yml`…) > les scripts du projet > le README. Si la CI et les scripts
divergent, note l'écart (il ira dans le rapport) et retiens ce que la CI lance.

**Module** = unité avec son propre fichier de dépendances, testable seule. Un monorepo JS avec
`apps/*` et `packages/*` : un module par app, et les packages partagés regroupés si petits.

## 2. Répartir la recon

Un sous-agent `Explore` par module (+ un transverse), lancés **dans le même message**. Donne à
chacun : le chemin du module, les sections du §3 à remplir, la consigne « chaque affirmation cite
`fichier:ligne` ; ce que tu ne peux pas prouver, écris-le dans *à confirmer* », et « si
`graphify-out/graph.json` existe, interroge `graphify query/explain/path` avant de grep ».

## 3. Ce que chaque rapport doit contenir

### Par module
1. **Identité** : rôle du module en une phrase, point(s) d'entrée (`main`, serveur HTTP, CLI,
   worker, handler serverless, bundle front).
2. **Stack** : langage + version, framework(s) + version épinglée, base(s) de données, broker,
   ORM / client, outil de migration (→ option `migrations`), lib de test.
3. **Structure** : arborescence des 2 premiers niveaux du code, avec le rôle de chaque dossier.
4. **Architecture observée** : couches et sens des dépendances (qui importe qui — vérifie par
   échantillonnage d'imports, pas au nom des dossiers), où vit la logique métier, où vivent les
   adaptateurs (HTTP, DB, file, externe), règles d'architecture **déjà outillées** (ArchUnit,
   import-linter, dependency-cruiser, eslint boundaries, modules Go internes…).
5. **Contrats exposés** : routes HTTP / GraphQL / gRPC, topics, événements, CLI, schéma de BDD
   (dossier de migrations), avec leur fichier de définition.
6. **Conventions** : nommage, gestion d'erreurs, logs, config / secrets (variables d'env,
   fichiers), validation des entrées, formatage et lint (configs présentes).
7. **Tests** : types (unitaires, intégration, e2e, BDD), emplacement, conventions de nommage,
   fixtures, ce qui est mocké ; commande et **résultat réel** de la ligne de base.
8. **Vocabulaire du domaine** : entités, agrégats, états, rôles, statuts — tels que nommés dans
   le code (ils amorcent le glossaire).
9. **Points chauds** : fichiers les plus modifiés (`git log --format= --name-only | sort | uniq -c
   | sort -rn | head -20`), plus gros fichiers, TODO/FIXME notables.
10. **À confirmer** : ce qui semble vrai sans preuve.

### Transverse
- CI : jobs, déclencheurs, filtres de chemins, ce qu'ils lancent.
- Infra : Docker / compose, IaC, scripts de déploiement, environnements.
- Docs existantes : README, `docs/`, ADR, CONTRIBUTING — ce qu'elles disent **et** là où elles
  contredisent le code.
- Historique git : convention de commits déjà utilisée (`git log --oneline -30`), nommage des
  branches, merge vs squash.
- Sécurité : où vivent les secrets, `.env` committés par erreur (signaler, ne pas afficher la valeur).

## 4. Transformer la recon en règles

| Trouvé | Devient |
|---|---|
| Règle respectée partout et outillée (test d'archi, lint) | Règle non-négociable dans `CLAUDE.md` §5, avec le nom du contrôle |
| Règle respectée partout, pas outillée | Règle non-négociable + ligne de backlog « outiller cette règle » |
| Règle respectée avec exceptions | `CODING_RULES.md` du module, exceptions listées ; pas en non-négociable |
| Convention implicite, divergente selon les endroits | « à confirmer » → question à l'utilisateur en porte 1 |
| Choix structurant visible (framework, BDD, auth, archi) | ADR rétro-documentée |
| Dette, code mort, TODO majeur | Backlog `docs/ROADMAP.md` |
| Risque domaine (argent, santé, données perso, sécurité, temps réel) | `{{DOMAIN_RISKS}}` + règle `proposal` d'`openspec/config.yaml` |
