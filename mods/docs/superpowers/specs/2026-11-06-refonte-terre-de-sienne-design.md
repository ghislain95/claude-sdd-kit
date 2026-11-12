# Refonte « Terre de Sienne » des 4 mods — conception

> Statut : validée en conversation le 2026-11-06 (maquettes : `.superpowers/brainstorm/86171-1793958251/content/terre-de-sienne-v3.html`).
> Dépôt local, **jamais de commit** (l'utilisateur garde le dépôt en local).

## 1. Intention

L'utilisateur veut une interface « magnifique » pour ses mods Claude Code : moderne, avec du relief, des animations et de belles couleurs. Il ne veut pas se contenter de ranger le code. Il a choisi la direction **Terre de Sienne** (ocre chaud, terre brûlée, crème) et veut qu'elle **suive le thème clair ou sombre de l'app** (il travaille en clair aujourd'hui). Sa consigne : « n'hésite pas sur les animations, le relief ».

Ce chantier termine aussi le découpage de l'ancien mod unique en 4 mods :

| Mod | Rôle | Actif |
|---|---|---|
| `session-hud` | la bande au-dessus du prompt **et le fond animé de la fenêtre** | partout |
| `background-tasks` | le panneau « En arrière-plan » (services, workflows, agents) | partout |
| `conversation-cards` (nouveau) | les cartes du fil (questions, rapport, QA, bloc cockpit, commits), les cartes d'outils, le spinner, la consigne de format | partout |
| `openspec-cockpit` | le panneau OpenSpec seul, allégé | projets OpenSpec |

## 2. Objectifs, non-objectifs, anti-objectifs

**Objectifs**
- Un seul thème, Terre de Sienne, décliné en clair et en sombre, partagé par les 4 mods. Nord et Argile disparaissent.
- Un fond animé derrière la conversation (halos qui dérivent et grain léger), sous le verre dépoli de l'app desktop.
- Du relief et du mouvement dans chaque mod : dégradés, liseré clair, ombres portées, pulsations, anneaux qui se remplissent, barres qui poussent, reflets qui balaient une carte en attente, cartes qui montent en fondu.
- `conversation-cards` sorti du cockpit, avec ses tests. Le cockpit est allégé : les sections Session et Agents/workflows sont retirées.
- Les 4 mods sont installés à la fin (choix de l'utilisateur : **après** la refonte).

**Non-objectifs**
- Aucune fonction nouvelle, hormis le fond. Ce que chaque mod sait faire aujourd'hui, il le fait encore.
- Le terminal garde son rendu texte actuel : la refonte vise desktop et VS Code, là où `Svg` existe.
- La consigne de format reste à 3 règles. On adapte le rendu au texte des agents, jamais l'inverse.

**Anti-objectifs (ce serait un échec même si « ça marche »)**
- Une interface illisible dans l'un des deux thèmes, par exemple un texte crème sur fond crème.
- Du mouvement qui fatigue : seul le fond bouge en continu, et lentement. Le reste anime une arrivée ou un état « en cours ». Tout s'arrête sous `prefers-reduced-motion`.
- Revenir aux pièges connus : un redessin à chaque appel d'outil, qui fait perdre les clics ; des boutons dans des listes longues, qui font redescendre le panneau.
- Dégrader ce que disent les agents des autres conversations : les cartes ne remplacent un message que si elles le reconnaissent avec certitude, comme aujourd'hui.

## 3. Contraintes techniques (API des mods, build 2.1.317)

- `Box` : couleurs de fond et de bordure, `borderStyle`, survol (`hover`), positionnement absolu. **Pas de dégradé, d'ombre ni d'arrondi libre.**
- `Svg` : document SVG complet (≤ 131 072 caractères), dessiné comme une image, ou dans un cadre isolé avec `isInteractive`. Les animations CSS et SMIL tournent. C'est **la seule source de relief**. Il faut lui donner une largeur en pixels CSS.
- Largeur : `e.viewport.columns`. Dans un panneau, environ **8,9 px par colonne** (mesuré). Une pièce SVG pleine largeur doit supporter un écart de quelques pixels : ses dégradés s'estompent vers la droite, donc un léger manque de largeur ne se voit pas.
- Fond de fenêtre : `$.ui.backdrop({ id, glass })`, dessiné par un hook `ui.render` sur `{ component: 'Backdrop' }`, sur desktop seulement. Sans `tint`, le verre garde la couleur de panneau de l'app, donc suit le thème. Un `tint` serait une couleur brute, figée : on n'en met pas.
- Clair et sombre :
  - SVG : `@media (prefers-color-scheme: dark)` dans le `<style>` du dessin. Le cockpit le fait déjà pour ses pistes.
  - Éléments natifs : clés de thème (`text`, `subtle`, `success`…) pour le texte. En couleur brute, seulement des accents de ton moyen ou translucides, lisibles sur les deux fonds.
  - **À vérifier tôt** : que `prefers-color-scheme` suit le réglage clair/sombre de l'app, et pas seulement celui de macOS.
- Code partagé : les originaux sont dans `shared/`, recopiés dans `<mod>/hooks/shared/` par `scripts/sync-shared.sh`. On modifie l'original.
- Pièges hérités de la passation, toujours valables :
  - pas de bouton dans les listes longues d'un panneau ;
  - l'état est écrit au rafraîchissement (30 s) ou en fin de tour, jamais par appel d'outil ;
  - sur desktop, le `label` d'un `Button` remplace son contenu, et un texte dans un bouton perd sa couleur ;
  - ce qui doit survivre au rechargement à chaud va dans `$.state` ;
  - le contrat `types/index.d.ts` est autonome, sans aucun `import` ;
  - `find({ text })` cherche une sous-chaîne ;
  - chaque tsconfig a `noEmit`.

## 4. Le système visuel « Terre de Sienne »

### 4.1 Jetons de couleur

| Jeton | Clair | Sombre | Usage |
|---|---|---|---|
| `base` | `#f4ece0` | `#17110d` | fond de la fenêtre (backdrop) |
| `halo1` | `#eab26a` | `#c8693c` | halo haut-gauche |
| `halo2` | `#d98a5c` | `#e0a458` | halo bas-droite |
| `halo3` | `#f0cf9a` | `#7a3b22` | halo central |
| `text` | `#3b2617` | `#f2e7d7` | texte dans les SVG |
| `mute` | `#8a6f58` | `#a08c77` | texte secondaire dans les SVG |
| `accent` | `#b8621f` | `#e8ae62` | accent ocre (bordures, pastilles, chiffres clés) |
| `accent2` | `#d98a3d` | `#f3c47a` | haut des dégradés d'accent |
| `ok` | `#5f9a62` | `#9fd08a` | vert sauge : fini, actif |
| `running` | `#c27a2c` | `#f0b866` | en cours |
| `warning` | `#c9902a` | `#e8c06a` | à surveiller |
| `danger` | `#b4473a` | `#e07a68` | erreur, bloquant |
| `track` | `rgba(122,72,34,.14)` | `rgba(255,230,200,.10)` | pistes des anneaux et des barres |
| `shadow` | `rgba(110,60,20,.22)` | `rgba(0,0,0,.55)` | ombres portées |
| `highlight` | `rgba(255,255,255,.9)` | `rgba(255,255,255,.16)` | liseré clair en haut des pièces |

**Couleurs pour les éléments natifs** : une seule valeur, lisible sur les deux fonds. Accent `#c0702a`, bordure d'accent `rgba(192,112,42,.45)`, fond d'accent `rgba(217,138,61,.12)`, sauge `#6f9f6a`, danger `#c0503f`. Le texte natif reste sur les clés de thème. Le contraste se vérifie sur les deux fonds, cible ≥ 3:1 pour l'accent en gras.

Les jetons vivent dans `shared/sienne.ts` : les valeurs, une feuille `<style>` commune aux SVG (variables CSS, bascule `prefers-color-scheme`, animations, arrêt sous `prefers-reduced-motion`) et les primitives ci-dessous. `shared/palette.ts` (Nord) disparaît. Ses appelants passent à `sienne.ts`.

### 4.2 Primitives SVG (dans `shared/sienne.ts`)

Chacune renvoie une chaîne `<svg …>` autonome, clair et sombre compris :

- `dot(tone, { pulse })` : la pastille d'état. En cours, une onde s'en échappe.
- `ring(fraction, { size, tone, label? })` : un anneau en dégradé qui se remplit à l'affichage, avec un texte au centre en option (« 3/5 »). La grande version (≥ 48 px) a un disque en verre et une ombre portée.
- `bar(width, fraction, { running })` : une barre en dégradé qui pousse. Si `running`, une lueur la parcourt en boucle.
- `ribbon(width, { icon, title, meta?, tone, waiting })` : l'en-tête de carte. Il porte une pastille ou une icône, le titre, une méta alignée à droite, un dégradé qui s'estompe vers la droite et un filet en bas. Si `waiting`, un reflet le balaie et une onde part de la pastille. Le titre est dans le SVG.
- `timeline(width, steps, current)` : la frise des phases. Le trait se trace jusqu'à la phase en cours, qui pulse.
- `check()`, `icon(name)` : petites icônes (commit, rapport, QA, question, outil…) dessinées au trait.
- `backdrop()` : le fond de fenêtre (§ 4.3).

Relief commun : dégradé vertical léger, liseré `highlight` d'un pixel en haut, `feDropShadow` doux. Les identifiants internes des SVG (dégradés, filtres) sont préfixés pour qu'aucun dessin n'emprunte ceux d'un autre.

### 4.3 Le fond animé

- Il appartient à **`session-hud`**, le mod actif partout, pour n'avoir qu'un seul fond. *Choix de conception.* À `session.start`, le mod appelle `$.ui.backdrop({ id: 'sienne' })`, sans `tint`, avec le flou par défaut. Le hook `Backdrop` rend un `Svg` qui couvre la fenêtre (`preserveAspectRatio="xMidYMid slice"`).
- Contenu : la couleur `base`, trois halos flous (`feGaussianBlur`) qui dérivent en 24 à 38 s, en sens et phases décalés, et un grain `feTurbulence` à 7–10 % d'opacité.
- Une commande `/fond` l'allume ou l'éteint. Le choix est gardé dans `$.store`, allumé par défaut. *Choix de conception.*

### 4.4 Mouvement

| Où | Animation | Durée | Quand |
|---|---|---|---|
| Fond | dérive des halos | 24–38 s, en boucle | toujours (coupée sous reduced-motion) |
| Pastille en cours | onde | 1,8–2 s, en boucle | tant que l'état est « en cours » |
| Anneaux | remplissage | 1,4–1,6 s, une fois | à l'affichage |
| Barres | croissance, puis lueur | 1,2 s, puis 1,8 s en boucle | lueur seulement si en cours |
| En-tête de carte en attente | reflet + onde de la pastille | 3,4 s et 2,2 s, en boucle | tant que la question attend une réponse |
| Coche de commit | tracé | 0,6 s, une fois | à l'affichage |
| Frise des phases | tracé, puis pulsation de l'étape en cours | 1,2 s, puis 1,8 s | à l'affichage |

Courbe d'arrivée commune : `cubic-bezier(.23,1,.32,1)`. L'apparition en fondu des cartes vue dans la maquette n'existe pas pour les éléments natifs. Elle reste réservée à ce qui est en SVG (le ruban). *Limite de l'API.*

## 5. Application à chaque mod

### 5.1 `session-hud`
- **Bande** : une rangée native posée sur une « pilule ». Si l'essai du § 7 réussit, la pilule est un SVG en position absolue derrière la rangée, avec dégradé, liseré et ombre. Sinon, c'est une `Box` à bordure arrondie couleur accent et fond d'accent translucide.
- Contenu inchangé : point d'activité (`dot`, qui pulse quand Claude travaille), anneau du contexte (`ring`), coût ou limite, durée, outils et erreurs, modèle, puis à droite le compteur « N en arrière-plan ▴ » en pastille d'accent.
- La liste dépliante au-dessus de la bande garde ses lignes (pastille, nom, `:port`, type), habillée Sienne.
- **Fond** de la fenêtre : § 4.3.

### 5.2 `background-tasks`
- Même structure de panneau. Les titres de section sont en petites capitales `mute`, suivis d'un filet.
- Pastilles `dot` par service ou run. Une barre `bar` par run, qui pousse, avec une lueur s'il tourne. Les phases sont toujours dépliées, sans bouton dans les listes.

### 5.3 `conversation-cards` (nouveau)
- Repris du cockpit (détail au § 6) : cartes de question (Q1…), rapport, QA, bloc cockpit, commit, cartes d'outils, spinner, injection de la consigne de format (`prompt.compose`).
- Chaque carte = `ribbon` SVG (icône + titre + méta, `waiting` pour une question sans réponse) + corps natif. Le corps a une bordure d'accent translucide et, si l'essai réussit, un fond SVG en verre. Sous un message affiché en entier, les cartes restent **compactes** (titres + boutons), comme décidé. Seule la carte de rapport garde le détail.
- La carte de commit se termine par la coche qui se trace.

### 5.4 `openspec-cockpit` (allégé)
- On retire les sections Session et Agents/workflows, les cartes du fil (parties dans `conversation-cards`), Nord, Argile et `/cockpit-theme`.
- Reste le panneau OpenSpec : change courant, prochaine action, progression par groupe, décisions, rituel post-archive. En tête, un grand `ring` « n/m » avec ombre, le nom du change et la phase, puis la `timeline` des phases, puis les sections.

## 6. Découpage cockpit → conversation-cards

Inventaire établi le 2026-11-06 depuis `openspec-cockpit` 0.13.0. Les numéros de ligne renvoient à cette version.

### 6.1 Hooks de `register.tsx`

| Hook | Destination |
|---|---|
| `prompt.compose` (consigne `CONTRACT`) | `conversation-cards`, qui garde sa bascule `contract` |
| `ui.render` AssistantMessage (401-445) | `conversation-cards` |
| `ui.render` ToolUse (447-513) | `conversation-cards` (JSX à sortir dans un `tools.tsx`) |
| `ui.render` UserMessage, ligne de notification de tâche | `conversation-cards` |
| `ui.render` UserMessage, encadré d'alerte de garde-fou | reste dans le cockpit (chaque mod rend `next(e)` sur ce qui n'est pas à lui) |
| `ui.render` Spinner | `conversation-cards`, suffixe réduit à ce que le mod sait seul : pourcentage de contexte via `$.session.usage()`, lu au rafraîchissement. Le nom du change et les agents disparaissent du suffixe. *Choix de conception* : le panneau cockpit et la bande les montrent déjà. |
| `tool.call` (tous) | séparé : `recordToolCall`→`toolTimes` part dans les cartes ; `hasReview` reste dans le cockpit ; `refreshLive`, `activity` et `toolCount` sont supprimés |
| `session.start`, `classic.SessionStart`, `turn.complete`, `prompt.submit`, `session.append`, `ui.render` Pane, outil MCP `status`, commandes `cockpit` et `ou-en-suis-je` | restent dans le cockpit |
| `session.append` → `commitDraft` | reste dans le cockpit (via `commitBlocks`, partagé) |
| enveloppe de thème `ui.render` (382-387), `/cockpit-theme` | supprimées |
| `/cockpit-toggle` | reste dans le cockpit sans les bascules `cards` et `contract`. `conversation-cards` a sa propre commande `/cartes` (`/cartes off`, `/cartes contrat off`). *Choix de conception.* |
| `announceFinishedRuns`, `refreshLive` | supprimés (`background-tasks` annonce déjà les runs) |

### 6.2 Symboles

- **Vers `conversation-cards/hooks/`** :
  - `cards.tsx` en entier ;
  - de `parse.ts`, le groupe « cartes » (`parseQuestions`, `parseReport`, `cockpitBlock`, `qa*`, `askGroups`, `parseFindings`, `fileRefs`, etc., environ 30 symboles) ;
  - de `logic.ts`, `CONTRACT`, `spinnerSuffix`, `toolCard`, `toolTail` ;
  - de `actions.ts`, le groupe « cartes » (`copyText`, `addToPrompt`, `markQa`, `toggleReportSection`, `openFile`, `summarize`, `insertAnswers`, `notePrompt`, `mergeAnswers`, `ANSWERS_*`).
- **Vers `shared/`** :
  - `commitBlocks`, utilisé par les deux mods, dans un nouveau `shared/commits.ts` ;
  - `cleanMarkdown`, `truncate`, `formatDuration`, qui existent déjà dans `shared/format.ts` : les deux mods les importent de là, et les doublons de `logic.ts` disparaissent.
- **Faits des cartes** (`cardFacts` : noms de changes, commits récents) : `conversation-cards` les collecte lui-même au rafraîchissement (30 s, et en fin de tour), avec un `git log` court et la liste de `openspec/changes/` si elle existe. Le collecteur est petit et vit dans le mod.
- **Restent dans le cockpit** : le groupe « panneau » de `parse.ts`, `logic.ts`, `actions.ts`, `collect.ts` (sans `collectWorkflows`, `collectSessions` ni `collectLive`) et `pane.tsx` (sans les sections Session, Agents et workflows, Autres sessions, ni la section Workflows du panneau texte). `nextAction`, `statusLine` et `summaryMarkdown` perdent leur entrée workflow.
- **Supprimés** :
  - `theme.ts` ;
  - de `svg.ts` : `useSvgTheme`, `tilesSvg`, `activitySvg`, `dotSvg`, `tileColumns`. `headerSvg`, `groupsSvg`, `ringSvg` et `pillsSvg` sont réécrits avec les primitives de `shared/sienne.ts` ;
  - le code mort : `isBandHidden`, `toggleQaNote`, `saveQaNote`, `qaNotes`, `qaEditing`, la bascule `band`.

### 6.3 Contrat d'état

- `conversation-cards` déclare :
  - `toolTimes`, `isToolOpen`, `isMessageOpen`, `qaMarks`, `reportOpen`, `briefs`, `cardFacts`, `projectRoot` ;
  - ses bascules `{ cards, contract }`.
- Le cockpit garde `snapshot`, `toggles` (sans `cards`, `contract` ni `band`), `hasReview`, `gateAlerts`, `collapsed`, `commitDraft`, `ritualMarks` et `busy`. Il perd `theme`, `live`, `activity`, `toolCount`, `isBandHidden`, ainsi que les champs `Snapshot.workflows` et `Snapshot.sessions`.
- `$.store` du cockpit : `theme` et `announcedRuns` ne sont plus lus. Les bascules `cards` et `contract` déjà enregistrées sont reprises une fois par `conversation-cards` à sa première session : il lit l'ancienne clé avec `$.store` du cockpit si l'API le permet, sinon les valeurs par défaut (activées) s'appliquent. *Choix de conception.*

### 6.4 Tests (104 aujourd'hui)

| Groupe | Tests | Destination |
|---|---|---|
| Cartes, spinner, outils (`cockpit.test.tsx` 20 : lignes 323, 339, 451, 496, 561, 572, 582, 602, 781, 798, 816, 824, 843, 852, 870, 889, 898, 911, 929, 948 ; `parse.test.ts` 21 ; `v2.test.ts` 3) | 44 | `conversation-cards`, avec `fixtures.ts`. Le test 572 bascule les cartes par `/cartes` au lieu de `/cockpit-toggle`. |
| Panneau OpenSpec (`cockpit.test.tsx` 10 : lignes 250, 273, 288, 375, 405, 421, 435, 614, 738, 760 ; `logic.test.ts` 14 ; `parse.test.ts` 9 ; `v2.test.ts` 1) | 34 | restent dans le cockpit. Le test 288 perd ses vérifications agents, workflows et sessions. |
| Workflows et agents, sur des fonctions déjà dans `shared/workflows.ts` (`logic.test.ts` 7, `parse.test.ts` 5) | 12 | déplacés dans `background-tasks`, qui teste les copies partagées |
| Workflows propres au cockpit (`cockpit.test.tsx` 3, `v2.test.ts` 3) | 6 | supprimés avec leur code |
| Thème Nord/Argile, SVG de thème (`cockpit.test.tsx` 2, `v2.test.ts` 3) | 5 | remplacés par les tests de `shared/sienne.ts` |
| Formatage (`logic.test.ts` 3) | 3 | suivent `shared/format.ts`, côté `conversation-cards` |

Chaque test qui vérifie une couleur Nord est réécrit pour vérifier le jeton Sienne correspondant.

## 7. Vérifications à faire en premier (essai jetable)

Un mod d'essai, `sienne-spike`, chargé dans cette session, pour vérifier trois points :
1. `prefers-color-scheme` dans un `Svg` suit le thème de l'app : basculer l'app en clair puis en sombre, capturer l'écran.
2. Le fond `Backdrop` en SVG animé s'affiche derrière la conversation, sous le verre, et les animations y tournent.
3. Un `Svg` dans une `Box` en `position: "absolute"` passe **derrière** le contenu natif qui le suit, ce qui permet la pilule et le verre des cartes.

Selon les résultats :
- **Point 1 en échec** : on lit le thème avec `$.config.list()` (ligne `theme`) au rafraîchissement, et on génère le SVG pour ce thème. Une valeur « auto » ou inconnue donne la version à media query. Un changement de thème en cours de session est pris en compte au rafraîchissement suivant (30 s), ce qui suffit. Pour que ce repli ne coûte rien, **chaque primitive prend dès le départ un paramètre optionnel `scheme: 'auto' | 'light' | 'dark'`** (`'auto'` par défaut, media query).
- **Point 2 en échec** : si le fond ne s'affiche pas du tout, on abandonne le fond et `/fond`. S'il s'affiche sans bouger, on le garde fixe. Si le verre l'efface, on augmente l'opacité des halos ou on passe `glass: { opacity }` plus bas. *Choix de conception.*
- **Point 3 en échec** : les corps restent des `Box` à bordure et fond translucide.

Le mod d'essai est supprimé ensuite.

**Résultats à l'écran (2026-11-06, app desktop, thème clair)** — vérifiés sur les vrais mods, l'essai ayant été retiré :
1. Clair/sombre : le clair est vérifié ; le sombre reste à voir quand l'utilisateur basculera l'app.
2. Fond : **non dessiné** par cette version de l'app (`isDrawn: false`, pas de couche de fond côté desktop). Le code reste en sommeil, et `/fond` le dit.
3. Couche absolue : une `Box` absolue se peint **par-dessus** ses frères suivants. La pilule de la bande est donc un `Svg` dans le flux, et la rangée passe en absolu au-dessus. Un `Svg` dont `alt` est vide n'est pas dessiné.

**Pendant l'essai**, l'ancien cockpit installé (0.7.0 en cache) dessine encore sa bande et ses cartes Nord. La pilule de l'essai peut donc s'empiler avec cette bande : c'est attendu.

## 8. Tests et vérification

- Tous les tests existants restent verts : 104 dans le cockpit aujourd'hui, à répartir entre `conversation-cards` et `openspec-cockpit` ; 8 dans `session-hud` ; 5 dans `background-tasks`.
- Nouveaux tests pour `shared/sienne.ts` : chaque primitive donne un SVG valide qui contient les deux thèmes et la règle reduced-motion ; les identifiants sont uniques ; la largeur est respectée.
- `claude plugin validate` et `tsc -p` passent pour chaque mod.
- À l'écran (captures `screencapture -x`), en clair **et** en sombre : la bande, le fond, une carte de chaque type, les deux panneaux. Chaque étape est montrée à l'utilisateur.

## 9. Surfaces, façon de travailler, installation

- **Surfaces** :
  - **desktop** : cible vérifiée à l'écran ;
  - **VS Code** : reçoit les mêmes arbres, puisque `Svg` y existe, mais sans fond (le backdrop est réservé au desktop) ; il n'est pas vérifié ;
  - **terminal et mobile** : gardent leur rendu texte actuel, sans travail de style.
- **Bascule clair/sombre** : c'est l'utilisateur qui change le thème de l'app, à la demande. Claude ne touche pas à ses réglages.
- **Rythme** : l'utilisateur a demandé d'enchaîner. Le développement avance donc sans pause. À chaque jalon (palette et fond, `conversation-cards`, cockpit, habillage des deux autres mods), une capture est montrée en clair et, si l'utilisateur bascule, en sombre. On ne s'arrête que sur une vraie décision.
- **Installation finale** : aujourd'hui seul le cockpit est installé, en 0.7.0 dans le cache. Il faut :
  - installer pour la première fois `session-hud`, `background-tasks` et `conversation-cards` ;
  - mettre à jour le cockpit ;
  - ajouter `conversation-cards` à `.claude-plugin/marketplace.json` ;
  - faire un `/reload-plugins` dans les autres sessions.

## 10. Laissé au constructeur
- Les tracés exacts des icônes, les durées à ±20 % et l'opacité du grain, tant que le rendu reste proche de la maquette v3.
- Le découpage interne de `shared/sienne.ts` en plusieurs fichiers s'il dépasse environ 400 lignes.
