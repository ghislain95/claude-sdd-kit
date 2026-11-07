# Glossaire

Le vocabulaire partagé du domaine, pour l'équipe et pour les agents : un terme qui le contredit
pendant un cadrage est challengé. Règle : **un concept = un mot**. Les synonymes vont sous
_Éviter_, et la spec OpenSpec (`openspec/specs/`) l'emporte en cas de conflit. Le glossaire est
tenu via le skill `sdd-core:domain-modeling` : un
terme nouveau ou contesté se tranche avec l'utilisateur, puis s'écrit ici.

## Format

```
**Commande** (`Order`, `order_id`) :
Demande d'achat passée par un client, identifiée par son `order_id`. À l'écran : « commande ».
_Éviter_ : achat (le paiement, pas la demande), panier (avant validation)
_Source_ : `openspec/specs/ordering/spec.md`
```

Règles :

- **Terme canonique en {{DOC_LANG}}** en gras, suivi de son ou ses **identifiants de code** entre
  parenthèses et en backticks. Pas d'identifiant : `(pas d'identifiant)`.
- **Définition = ce que c'EST**, en une ou deux phrases. **Aucun détail d'implémentation** : pas de
  seuil, de table, de migration ni de classe au-delà de l'identifiant. Ces détails vivent dans la
  spec, `MODULES.md` ou le code.
- **Seulement les termes propres au domaine.** Les concepts généraux de programmation (timeout,
  cache, endpoint) n'ont rien à faire ici.
- `_Éviter_` liste les synonymes écartés ; `_Source_` pointe la spec (ou le document, ou le fichier
  de code) qui fait foi.
- Termes **groupés par thème** (un `###` par thème, sous `## Termes`).
- Un conflit non résolu n'est pas tranché en silence : il est marqué `⚠️ À arbitrer` dans l'entrée
  et listé sous [À arbitrer](#à-arbitrer).

## Termes

<!-- sdd:fill: amorce tirée du code — les entités/agrégats/value objects métier, enums de statut et noms d'écrans récurrents. Un `###` par thème. Chaque entrée au format ci-dessus, `_Source_` = le fichier de code qui la définit (pas encore de spec). Deux noms pour un même concept trouvés dans le code → entrée marquée `⚠️ À arbitrer`. Pas plus de ~20 termes : les plus centraux. -->

## À arbitrer

<!-- sdd:fill: liste des conflits de vocabulaire trouvés pendant la rétro-doc (terme, variantes observées avec fichiers, recommandation) — ou « Aucun conflit relevé. » -->
