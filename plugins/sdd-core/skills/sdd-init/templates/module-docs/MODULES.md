<!-- sdd:note: instancié une fois par module dans {{MODULE_PATH}}/docs/MODULES.md. Inventaire tiré du code : un `##` par package/dossier racine, rien d'inventé. Rester à la granularité « rôle + types/services clés + règles propres » (une dizaine de lignes par package au plus) : le détail fin vit dans le code et naîtra dans les specs. -->
# Modules — `{{MODULE_NAME}}`

Index des packages/dossiers racine de `{{MODULE_PATH}}`. Cette page est la **source de vérité de la structure** — toute évolution passe ici d'abord.

> Règle stricte : **ne pas inventer de nouveau package racine** sans validation. Voir [`CODING_RULES.md`](CODING_RULES.md).

Liste exhaustive : <!-- sdd:fill: liste des packages racine en backticks, séparés par des virgules -->

---

<!-- sdd:fill: pour chaque package racine, une section :

## `<package>` — <rôle en quelques mots>

- `<type ou fichier clé>` — <ce qu'il porte>.
- `<service clé>` — <responsabilité>, <règle métier notable>.
- Dépend de : `<packages>` ; ne dépend jamais de : `<packages>` (si observable).
- ⚠️ <dette ou ambiguïté observée, à confirmer> (si besoin).
-->

## Démarrage

<!-- sdd:fill: point d'entrée du module (fichier), commande de lancement locale, configuration requise (noms des variables d'env, jamais de valeurs) -->
