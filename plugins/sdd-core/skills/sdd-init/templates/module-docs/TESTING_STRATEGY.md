<!-- sdd:note: instancié une fois par module dans {{MODULE_PATH}}/docs/TESTING_STRATEGY.md. Décrire la façon de tester OBSERVÉE (frameworks, dossiers, fixtures, helpers existants) ; si le module n'a pas ou peu de tests, le dire et proposer la stratégie minimale en la marquant « cible, à valider » + une ligne au Backlog de docs/ROADMAP.md. -->
# Stratégie de test — `{{MODULE_NAME}}`

> Référence de la façon de tester `{{MODULE_PATH}}` ({{MODULE_STACK}}). Toute déviation est justifiée en PR.

---

## 1. Pyramide de tests

| Couche | Outils | Périmètre | Quand l'utiliser |
|---|---|---|---|
<!-- sdd:fill: une ligne par couche observée (intégration, unitaire, e2e, non testé directement), avec outils, périmètre et règle de choix. Indiquer la couche PRIMAIRE (celle où vivent les règles métier) -->

<!-- sdd:fill: règle(s) non négociable(s) observée(s), ex. « jamais de base embarquée : conteneurs avec le moteur de prod » — ou supprimer la ligne -->

## 2. Lancer les tests

```bash
{{MODULE_CHECK}}             # tout, identique à la CI
```

<!-- sdd:fill: commandes pour lancer un seul fichier / un seul test / un tag, et prérequis (Docker, base locale, variables d'env) -->

## 3. Arborescence

<!-- sdd:fill: où vivent les tests, fixtures et helpers (bloc d'arborescence), et convention de nommage des fichiers de test -->

## 4. Du scénario de spec au test

Chaque scénario `#### Scenario:` d'une spec OpenSpec donne **un** test, nommé d'après le scénario, qui suit son GIVEN/WHEN/THEN.

<!-- sdd:fill: comment traduire concrètement un GIVEN/WHEN/THEN dans ce module (Gherkin/Cucumber si présent, sinon test paramétré ou fonction nommée `test_<scenario>`), avec un court exemple dans la stack réelle -->

## 5. Isolation et données

<!-- sdd:fill: comment les tests s'isolent (transaction annulée, nettoyage explicite, base par test, mocks), données aléatoires uniques vs fixes, attente asynchrone (jamais de sleep : outil d'attente utilisé) -->

## 6. Assertions

- Asserter selon le **contrat** : une assertion d'ordre seulement si la spec impose un ordre ; sinon comparaison sans ordre, ou fixture dans le désordre pour tester un tri.
- Une assertion affaiblie, un seuil relevé ou un test désactivé « pour faire passer » est un BLOQUANT en review.
<!-- sdd:fill: niveaux d'assertion utilisés dans le module (statut seul, champs clés, corps complet, invariants en base) et quand choisir lequel -->

## 7. Checklist quand on ajoute une feature

<!-- sdd:fill: 4-7 étapes concrètes dans ce module (créer le fichier de test ici, fixture là, nettoyage, lancement) -->

## 8. Anti-patterns à signaler en review

| ❌ Anti-pattern | ✅ À faire |
|---|---|
| Test désactivé, sauté ou neutralisé sans justification | Corriger la cause, ou justifier par écrit |
| Attente par `sleep` fixe | Outil d'attente avec condition et délai max |
| Assertion d'ordre sans contrat d'ordre | Comparaison sans ordre |
<!-- sdd:fill: anti-patterns propres à la stack et aux helpers du module -->
