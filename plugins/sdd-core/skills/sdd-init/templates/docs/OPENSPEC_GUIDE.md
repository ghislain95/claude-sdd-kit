# {{PROJECT_NAME}} — Guide OpenSpec (SDD)

> Guide pratique du workflow Spec Driven Development sur {{PROJECT_NAME}}.
> Public : développeur (humain ou agent) travaillant dans Claude Code.
> Référence amont : [OpenSpec](https://github.com/Fission-AI/OpenSpec), [`CLAUDE.md`](../CLAUDE.md), [`AGENTS.md`](../AGENTS.md).

---

## 1. Les concepts en 30 secondes

- **`openspec/specs/<domaine>/spec.md`** — la **source de vérité** : comment le
  système se comporte *aujourd'hui*. Jamais éditée à la main.
- **`openspec/changes/<change-id>/`** — un **change** = une évolution proposée,
  dossier autonome : `proposal.md` (pourquoi), `specs/` (deltas : quoi),
  `design.md` (comment), `tasks.md` (étapes).
- **Delta** — un change déclare `ADDED` / `MODIFIED` / `REMOVED` Requirements
  relatifs aux specs actuelles, sans les réécrire.
- **Archive** — `/opsx:archive` fusionne les deltas dans `openspec/specs/` et
  archive le change. Seul moment où les specs bougent : la boucle est
  auto-alimentée.
- **`openspec/config.yaml`** — le contexte projet et les règles de rédaction injectés
  dans chaque artefact (proposal, specs, design, tasks).

Les specs naissent **au fil des changes** : un domaine existant sans spec reçoit la sienne
par le premier change qui le touche (le delta `ADDED` décrit alors le comportement actuel
qu'il touche, pas tout le domaine). Pas de rétro-spec massive : elle coûte cher et périme vite.

## 2. « J'ai envie de… » → quoi faire

| Envie | Action |
|---|---|
| Implémenter un epic/ticket de la roadmap | `/opsx:new <change-id>` puis cycle complet (§3) |
| Une feature pas encore cadrée | `/opsx:new <change-id>` — `product-owner` cadre avec toi |
| Explorer une idée sans m'engager | `/opsx:explore` |
| Corriger un bug qui contredit une spec | `/opsx:new fix-<bug>` |
| Hotfix trivial (< 30 min, comportement spécifié intact) | Implémentation directe sur une branche `fix/…`, pas de change |
| Reprendre un change en cours | `/opsx:continue` ou `/opsx:apply` |
| Vérifier l'implémentation vs specs | `/opsx:verify` |
| Terminer un change livré | `/opsx:archive` |
| Corriger une spec (typo, précision) | Un petit change (`/opsx:new fix-spec-<domaine>`, delta `MODIFIED`) puis `/opsx:archive` — `/opsx:sync` ne fait que reporter dans `specs/` les deltas d'un change **existant** ; jamais d'édition manuelle de `specs/` |
| Découvrir le cycle sur un vrai exemple | `/opsx:onboard` |

## 3. Le cycle complet d'une feature

```
/opsx:new <change-id> → /opsx:ff → /opsx:apply → /opsx:verify → /opsx:archive
```

Avec l'équipe d'agents (routage : [`CLAUDE.md`](../CLAUDE.md) §8, détail : [`AGENTS.md`](../AGENTS.md)) :

1. **Cadrage** — `product-owner` : `proposal.md` (intent, scope, non-goals,
   critères testables), epic de la roadmap référencé.
1b. **Passe adversariale** — si le change est structurant, `architect` tente de casser le
   proposal ; les objections sont résolues dans le proposal avant `/opsx:ff`.
2. **Design** — `architect` : spec deltas (Given/When/Then, traduisibles 1:1 en tests) +
   `design.md` (module d'appartenance, migration oui/non, frontières de couches, décisions
   sourcées à la version épinglée).
3. **Implémentation** — `<module>-dev`<!-- sdd:if multi-module --> / `full-stack-dev`<!-- sdd:endif --> : `tasks.md` coché au fur et à
   mesure ; `tester` vérifie : 1 scénario de delta = 1 test.
4. **Vérification** — `code-reviewer` sur le diff, puis `/opsx:verify` (conformité aux deltas,
   tests réellement exécutés).
5. **Archivage** — commit(s) d'implémentation par l'agent sur la branche du change (Conventional
   Commits, [`CONTRIBUTING.md`](CONTRIBUTING.md) §2), `/opsx:archive`, post-archive (`doc-writer`
   vérifie que `docs/` ne contredit pas les specs fusionnées), commit `chore(<id>)` ; enfin<!-- sdd:if github --> push, PR et fusion<!-- sdd:endif --><!-- sdd:if !github --> fusion par un humain<!-- sdd:endif -->
   selon le niveau d'autonomie de [`CONTRIBUTING.md`](CONTRIBUTING.md) §2.

**Hygiène de contexte** : un contexte frais par phase (`/clear`, ou `/sdd-core:passation` puis
nouvelle session) — les artefacts portent la mémoire.

## 4. Règles de rédaction des specs et deltas

- **SHALL ou MUST sur la première ligne** du texte de chaque requirement
  (le validateur ne lit que la première ligne physique pour ce contrôle).
- Comportement **observable uniquement** : endpoints, événements, commandes, formats
  d'échange, codes d'erreur. Pas de noms de classes (→ `design.md`).
- Scénarios `#### Scenario:` en GIVEN/WHEN/THEN, traduisibles 1:1 en tests.
- Couvrir les cas d'erreur (entrée invalide, doublon, droits insuffisants, ressource
  inconnue, limite atteinte), pas seulement le nominal.
- Tout en **{{CODE_LANG}}** (comme le code et les tests).
- Le futur ne va pas dans les specs : un epic non implémenté = un futur change
  (l'intention vit dans [`ROADMAP.md`](ROADMAP.md)).
- Tout impact sur {{DOMAIN_RISKS}} doit être explicite dans le proposal.

## 5. CLI utile

```bash
openspec validate --all     # avant chaque commit touchant openspec/
openspec list               # changes en cours
openspec status             # état des artefacts d'un change
openspec update             # après un upgrade du package npm (régénère /opsx:* et skills)
```

La version du CLI est épinglée en CI (`.github/workflows/openspec.yml`) : la monter **en même
temps** en local et en CI, volontairement.

## 6. Pièges connus

- ❌ Éditer `openspec/specs/` à la main → uniquement archive/sync. Seule exception : la section
  `## Purpose` (les deltas ne la portent pas), corrigée dans le commit d'archive du change qui la
  rend fausse (`CLAUDE.md` §3). La CI (`.github/workflows/openspec.yml`) refuse un diff de
  `openspec/specs/` sans `openspec/changes/`.
- ❌ SHALL/MUST repoussé en 2ᵉ ligne par un retour à la ligne → validation KO.
- ❌ Implémenter un contrat absent des specs → c'est un change qui manque.
- ❌ Dévier du `design.md` sans le mettre à jour.
- ❌ Oublier `/opsx:archive` après livraison → les specs dérivent.
- ❌ Croire que `/opsx:verify` termine le travail : il **audite**, il ne commit ni n'archive.
- ❌ Committer ou pousser sur `{{DEFAULT_BRANCH}}` → jamais : tout passe par une branche et <!-- sdd:if github -->une PR<!-- sdd:endif --><!-- sdd:if !github -->une fusion humaine<!-- sdd:endif -->
  ([`CONTRIBUTING.md`](CONTRIBUTING.md) §2).
