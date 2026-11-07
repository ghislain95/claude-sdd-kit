# Architecture système — {{PROJECT_NAME}}

> Rétro-documentation : ce document décrit l'architecture **observée dans le code** au
> <!-- sdd:fill: date AAAA-MM-JJ et commit court de la rétro-doc -->, pas une cible. Ce qui n'a pas
> pu être vérifié est marqué « à confirmer ». Le comportement fait foi dans `openspec/specs/` ;
> ce document décrit la **structure**.

---

## 1. Vue d'ensemble

{{PROJECT_PITCH}}

<!-- sdd:fill: schéma ASCII ou Mermaid des composants (modules, bases, files de messages, services externes) et de leurs flux principaux, tiré du code et des fichiers de config/déploiement -->

## 2. Modules

| Module | Chemin | Stack | Rôle | Docs |
|---|---|---|---|---|
<!-- sdd:each module -->
| `{{MODULE_NAME}}` | `{{MODULE_PATH}}` | {{MODULE_STACK}} | <!-- sdd:fill: rôle en une phrase --> | [`CODING_RULES`](../{{MODULE_PATH}}/docs/CODING_RULES.md) · [`MODULES`](../{{MODULE_PATH}}/docs/MODULES.md) |
<!-- sdd:endeach -->

Style d'architecture observé : **{{ARCH_STYLE}}**.

## 3. Contrats externes

<!-- sdd:fill: les interfaces observables du système, par type — API HTTP (préfixes, versionnage, format d'erreur, auth), messages/événements (topics, files, schémas), CLI, fichiers importés/exportés, webhooks. Pour chacun : où il est défini dans le code (fichier:ligne). Pas l'inventaire complet des endpoints : les familles et les conventions. Les contrats détaillés naîtront dans openspec/specs/ au fil des changes. -->

## 4. Modèle de données

<!-- sdd:fill: entités métier principales et leurs relations (schéma court), bases utilisées, outil de migration et dossier des migrations, règles transverses observées (ex. multi-tenant : toute requête filtre par tenant ; suppression logique) -->

## 5. Flux critiques

<!-- sdd:fill: 2 à 4 parcours de bout en bout qui portent {{DOMAIN_RISKS}} (ex. une commande de l'API au paiement), en étapes numérotées avec le fichier de chaque étape -->

## 6. Sécurité

<!-- sdd:fill: authentification (mécanisme, durée de vie, stockage), autorisation (rôles et où ils sont définis), validation des entrées, gestion des secrets (variables d'env, fichiers ignorés) — tel qu'observé -->

## 7. Environnements et exécution

<!-- sdd:fill: comment on lance le projet en local (commandes exactes), dépendances d'infra (conteneurs, compose), variables d'environnement requises (noms seulement, jamais de valeurs), environnements de déploiement connus -->

## 8. Décisions structurantes

Les décisions qui ont façonné cette architecture sont dans [`adr/`](adr/).

<!-- sdd:fill: liste des ADR créés par sdd-init pour les décisions implicites observées (ex. choix du framework, du style de persistance, du monorepo), une ligne chacun avec lien -->

## 9. Zones à confirmer

<!-- sdd:fill: ce que la rétro-doc n'a pas pu établir avec certitude (code mort apparent, intention d'un module, config contradictoire), une ligne chacun — ou « Rien à confirmer. » -->
