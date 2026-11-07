# Roadmap

> **Statut** : <!-- sdd:fill: état en une ligne + date de la dernière resynchronisation avec le code ({{INSTALL_DATE}} à l'installation) -->
> **Public** : ingénieurs (agents Claude compris), product owner, reviewers.
> **Objectif** : <!-- sdd:fill: objectif de la prochaine version, tiré du README / des docs / issues existantes ; sans source : « À confirmer par le product owner. » — ne pas poser de question pour ça -->

Pour le contexte produit, lire d'abord [`ARCHITECTURE.md`](ARCHITECTURE.md) et [`GLOSSARY.md`](GLOSSARY.md).

La roadmap est le **vivier** du workflow : un epic/ticket = un futur change OpenSpec
(`/opsx:new`) ; une idée différée = une ligne « Backlog — chantiers flaggés », pas un souvenir de
session.

---

## Vision

<!-- sdd:fill: 3-5 lignes tirées du README et des docs existantes : ce que le produit permet, pour qui ; sans source : « À confirmer par le product owner. » (ne rien inventer, ne pas poser de question) -->

## Hors-scope

<!-- sdd:fill: ce qui n'est explicitement pas visé par cette version — ou « À définir avec le product owner. » -->

## Phasage

### Ordre retenu le {{INSTALL_DATE}}

<!-- sdd:fill: ordre des epics s'il existe déjà (docs, issues) ; sinon « À définir avec le product owner. » — toute décision qui le modifie sera datée ici -->

## État d'avancement ({{INSTALL_DATE}})

Décompte des tickets cochés `✅` sur le nombre de tickets du tableau de chaque epic. Légende : ✅ livré · 🟡 partiel (ticket ouvert) · ⬜ non commencé.

| EPIC | Titre | État | Tickets livrés | Reste notable |
|---|---|---|---|---|
<!-- sdd:fill: une ligne par epic réel (issues, backlog existant) ; aucun → supprimer le tableau et écrire « Aucun epic pour l'instant : le premier cadrage (`/opsx:new`) en créera un. » -->

---

<!-- sdd:fill: epics réels s'il en existe (issues, backlog existant), chacun au format : `## EPIC n — titre`, **User story** « En tant que … je peux … afin de … », tableau **Tickets** (# | Description | Taille S/M/L), **Dépendances**. Aucun → rien ici. Les fonctionnalités DÉJÀ présentes dans le code ne deviennent pas des tickets : elles sont décrites dans ARCHITECTURE.md -->

---

## Backlog — chantiers flaggés (hors epics)

Chantiers identifiés en cours de route, pas encore rattachés à un epic. Chacun
devient un change OpenSpec à cadrer (`/opsx:new`) quand il est priorisé.

| Chantier | Description | Taille | Origine |
|---|---|---|---|
<!-- sdd:fill: dette ou trous repérés pendant la rétro-doc (TODO/FIXME significatifs, tests absents sur un module critique, contrôle d'architecture manquant…), une ligne chacun, Origine = « sdd-init (AAAA-MM-JJ) » — ou une ligne « — | Aucun chantier relevé | — | — » -->

---

## Process de mise à jour de cette roadmap

- Chaque ticket complété est coché ou retiré. Cocher = préfixer la description par `✅` et citer le change qui l'a livré (« — livré par `<change-id>` (date) »), au post-archive (`CLAUDE.md` §3). Une ligne « Backlog — chantiers flaggés » close est retirée.
- Légende des préfixes :
  - `✅` livré : `` | 1.1 | ✅ <description> — livré par `<change-id>` (AAAA-MM-JJ) | M | ``. La date est le **préfixe du dossier** `openspec/changes/archive/` (convention uniforme, vérifiable). Sans change archivé (hotfix, outillage) : `` livré par `<hash court>` (date du commit) ``. Une réserve éventuelle (test ignoré hors CI, double de test…) se met en fin de ligne : ` — réserve : …` ; on ne coche que si le comportement promis existe.
  - `🟡` partiel : `` | 3.2 | 🟡 <description> — partiel : livré par `<id>` (date) ; reste : <ce qui manque> | M | ``. Un `🟡` n'est jamais « presque coché » : c'est un ticket encore ouvert, dont la ligne dit exactement ce qui reste.
  - Aucun préfixe = non fait ; si utile, suffixe ` — ⚠️ <constat>` (sans coche).
  - Un écart entre le texte d'un ticket et le code livré se corrige dans la ligne, de façon compacte : `(réel : …)`.
- À chaque coche, recompter le tableau « État d'avancement » (tickets `✅` sur le nombre de tickets de l'epic) et mettre à jour sa date.
- Tenir à jour l'« Ordre retenu » de la section Phasage : toute décision qui le modifie y est datée.
- Chaque nouveau ticket suit le format `EPIC X — # — Description — Taille (S/M/L)`.
- Toute évolution majeure d'epic = ADR dans `docs/adr/` puis mise à jour ici.
- L'agent `product-owner` est le gardien de la cohérence métier de ce document.
