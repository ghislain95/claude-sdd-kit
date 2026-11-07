<!-- sdd:note: instancié une fois par module dans {{MODULE_PATH}}/docs/CODING_RULES.md. Chaque règle est tirée du code réel (pattern majoritaire observé, config de lint/format, test d'architecture) — jamais d'une « bonne pratique » générique absente du code. Une règle observée seulement en partie (pattern minoritaire) est notée « tendance, à confirmer ». Supprimer une section sans contenu observable plutôt que d'inventer, puis renuméroter les sections. -->
# Règles de code — `{{MODULE_NAME}}`

**Ces règles sont strictes.** Toute dérogation est justifiée explicitement dans la PR (ou le `design.md` du change).

Stack : {{MODULE_STACK}} — versions épinglées dans `{{MODULE_DEPS_FILE}}`.

---

## 1. Style architectural

<!-- sdd:fill: style observé ({{ARCH_STYLE}} pour ce module) en 2-4 puces, et ce qu'il N'EST PAS (ex. « pas de DDD canonique avec bounded contexts formels »). Un « ❌ Ne jamais… » sur la réorganisation non demandée -->

## 2. Structure — source de vérité

<!-- sdd:fill: liste FERMÉE des packages/dossiers racine du module (ex. `src/<pkg>/{a,b,c}`), avec la règle « ne pas inventer de nouveau package racine : discussion + mise à jour de MODULES.md avant tout code ». Renvoi vers MODULES.md -->

## 3. Conventions internes

<!-- sdd:fill: arborescence type d'un package/feature telle qu'observée (ex. model/ service/ repository/ api/), en bloc de code, avec le rôle de chaque dossier -->

## 4. Séparation domaine / adaptateurs

<!-- sdd:fill: ce qui est interdit dans les adaptateurs (contrôleurs HTTP, handlers de messages, jobs, CLI) : aucune logique métier ; dépendances interdites du domaine vers les frameworks ; où vit la logique (nom des services). Citer le contrôle automatique s'il existe (test d'architecture, lint d'import) avec son fichier, sinon « non outillé » -->

## 5. Frontières (API, messages, UI)

<!-- sdd:fill: règles observées aux frontières : DTO/schémas de validation, format d'erreur, codes de statut, sérialisation, gestion de l'auth au niveau adaptateur. Pour un module UI : composants vs pages, état, accès données -->

<!-- sdd:if migrations -->
## 6. Persistance

<!-- sdd:fill: ORM/driver, outil et dossier de migrations, règles observées (transactions, requêtes filtrées par tenant, pas de génération auto de schéma), « une migration appliquée n'est jamais modifiée » -->
<!-- sdd:endif -->

## 7. Style de code

<!-- sdd:fill: outils de format/lint et leur config (fichier), conventions de nommage observées, typage (strict ? `any`/ignore tolérés ?), règles d'import -->

## 8. Logs

<!-- sdd:fill: librairie de log, niveaux utilisés, ce qui ne doit jamais être loggé (secrets, tokens, données personnelles, payloads complets en info) -->

## 9. Gestion d'erreurs

<!-- sdd:fill: exceptions/erreurs métier typées ? handler global ? validation aux frontières ? isolation des erreurs par message dans un consommateur ? fail fast vs fallback -->

## 10. Tests

- Tests : {{MODULE_TEST_KINDS}}. Stratégie détaillée : [`TESTING_STRATEGY.md`](TESTING_STRATEGY.md).
- Contrôle complet, identique à la CI : `{{MODULE_CHECK}}`.
<!-- sdd:fill: 2-3 règles de test propres au module (ex. pas de contexte applicatif complet pour de la logique pure) -->

## 11. Langue

- Code, identifiants, commentaires inline techniques : **{{CODE_LANG}}**.
- Documentation Markdown : **{{DOC_LANG}}**.

## 12. Garde-fous critiques

Quand on décrit, modifie ou génère du code dans ce module :

1. Toujours partir de la **structure existante**.
2. **Ne jamais** inventer un domaine ou un package racine manquant.
3. **Ne jamais** réorganiser l'architecture sans demande explicite.
4. **Ne jamais** mettre de logique métier dans un adaptateur.
<!-- sdd:fill: garde-fous propres au module et au domaine ({{DOMAIN_RISKS}}) -->
