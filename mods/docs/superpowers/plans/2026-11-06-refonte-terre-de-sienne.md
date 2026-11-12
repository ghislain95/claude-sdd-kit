# Refonte « Terre de Sienne » — plan d'implémentation

> **Pour les agents :** sous-skill requis : superpowers:executing-plans (choix : exécution native dans cette session, l'utilisateur a demandé d'enchaîner). Les étapes utilisent des cases `- [ ]`.

**But :** un thème unique Terre de Sienne (clair et sombre), avec fond animé et relief SVG, sur 4 mods. `conversation-cards` est sorti du cockpit et le cockpit est allégé.

**Architecture :** les jetons et les primitives SVG vivent dans `shared/sienne.ts` et sont recopiés dans chaque mod par `scripts/sync-shared.sh`. Chaque mod garde des arbres natifs (`Box`/`Text`/`Button`) pour la structure et le texte. Le relief et le mouvement viennent de pièces `Svg` dimensionnées depuis `e.viewport.columns`. Le fond de fenêtre appartient à `session-hud`.

**Pile :** mods Claude Code (TSX, `register(on)`, build 2.1.317), tests `claude plugin test`, types générés sous `<mod>/.claude-plugin/types/`.

**Spec :** `docs/superpowers/specs/2026-11-06-refonte-terre-de-sienne-design.md`, à lire avec ce plan.

## Contraintes globales

- **Jamais de commit.** L'étape « commit » habituelle est remplacée par : `scripts/dev-sync.sh` puis tests verts.
- Prose en français, code et commentaires en anglais.
- Contrat `types/index.d.ts` autonome, sans aucun `import`. Chaque `tsconfig.json` a `"noEmit": true`.
- Pas de `Button` dans les listes longues d'un panneau. L'état est écrit au rafraîchissement (30 s) ou en fin de tour, jamais par appel d'outil.
- Couleurs des éléments natifs : texte en clés de thème. En couleur brute, seulement ces valeurs : accent `#c0702a`, bordure `rgba(192,112,42,.45)`, fond `rgba(217,138,61,.12)`, sauge `#6f9f6a`, danger `#c0503f`.
- Chaque SVG contient sa bascule `@media (prefers-color-scheme: dark)` et `@media (prefers-reduced-motion: reduce)`. Ses `id` internes sont préfixés et uniques. Taille ≤ 131 072 caractères.
- Pixels par colonne : 8,9 dans un panneau. Dans le fil, la règle actuelle du cockpit reste : `clamp(240, columns*6, 640)`.
- Original partagé dans `shared/`, jamais dans les copies `<mod>/hooks/shared/`.
- Commandes de vérification. `X="$CLAUDE_CODE_EXECPATH"`, puis :
  - `$X plugin test <mod>`
  - `$X plugin validate <mod>`
  - `tsc -p ~/.claude/dev-mods/<session>/<mod>` (copie de dev, types générés)

## Points de vigilance

1. **Accent natif illisible dans un des deux thèmes.** Contraste de `#c0702a` ≥ 3:1 sur `#f4ece0` et sur `#17110d` : test dans la tâche 1.
2. **Fenêtre étroite ou `viewport` absent.** Le ruban et la frise restent ≥ 240 px et ne débordent pas : test dans la tâche 1.
3. **Deux cartes dans un même message.** Les `id` SVG ne se croisent pas (préfixe dérivé de la clé) : test dans la tâche 1.
4. **Un autre plugin pose un fond.** Le hook `Backdrop` de `session-hud` rend `next(e)` si `e.props.plugin !== 'session-hud'` : test dans la tâche 2.
5. **Titre avec `<`, `&` ou guillemets** dans un ruban (titre de question, message de commit). Il est échappé et le SVG reste valide : test dans la tâche 1.

---

### Tâche 0 : essai jetable `sienne-spike` (déjà écrit)

**Fichiers :** `~/.claude/dev-mods/<session>/sienne-spike/` (hors dépôt).

- [ ] L'utilisateur active les mods de la session. Capture `screencapture -x`, en ne gardant que la fenêtre Claude (vérifier qu'elle est au premier plan, sinon ne rien capturer et demander).
- [ ] Noter les trois résultats du § 7 de la spec : étiquette CLAIR/SOMBRE (avant et après bascule par l'utilisateur), fond visible et animé, texte natif par-dessus la pilule.
- [ ] Reporter les résultats dans la spec (§ 7, une ligne par point) et appliquer les replis prévus.
- [ ] Supprimer le dossier `sienne-spike`.

### Tâche 1 : `shared/sienne.ts`, outillage de synchro

**Fichiers :**
- Créer : `shared/sienne.ts`, `scripts/dev-sync.sh`, `session-hud/hooks/sienne.test.ts` (teste la copie partagée)
- Modifier : `scripts/sync-shared.sh` (liste des mods : `background-tasks session-hud conversation-cards openspec-cockpit`)

**Interfaces produites :**
```ts
export type Scheme = 'auto' | 'light' | 'dark'
export type Tone = 'ok' | 'running' | 'warning' | 'danger' | 'accent' | 'muted'
export const TOKENS: { light: Record<TokenName, string>; dark: Record<TokenName, string> } // values: spec § 4.1
export const NATIVE: { accent: '#c0702a'; accentBorder: string; accentFill: string; ok: '#6f9f6a'; danger: '#c0503f' }
export function contrast(fg: string, bg: string): number                       // WCAG ratio, hex only
export function styleSheet(scheme?: Scheme): string                            // <style> with CSS vars, keyframes, reduced-motion
export function dot(tone: Tone, o?: { pulse?: boolean; size?: number; scheme?: Scheme }): string
export function ring(fraction: number, o?: { size?: number; tone?: Tone; label?: string; scheme?: Scheme; id?: string }): string
export function bar(width: number, fraction: number, o?: { running?: boolean; scheme?: Scheme; id?: string }): string
export function ribbon(width: number, o: { id: string; icon: IconName | { badge: string }; title: string; meta?: string; tone?: Tone; waiting?: boolean; scheme?: Scheme }): string
export function timeline(width: number, steps: string[], current: number, o?: { scheme?: Scheme; id?: string }): string
export function pills(items: { label: string; tone: Tone }[], o?: { scheme?: Scheme }): { source: string; width: number; height: number }
export function icon(name: IconName, o?: { size?: number; tone?: Tone; draw?: boolean }): string
export type IconName = 'question' | 'report' | 'qa' | 'commit' | 'check' | 'tool' | 'info' | 'warning' | 'cockpit'
export function backdrop(o?: { scheme?: Scheme }): string
export function escapeXml(text: string): string
export function fitText(text: string, maxPx: number, pxPerChar?: number): string
export const MIN_WIDTH = 240
```
`scheme: 'auto'` (par défaut) utilise les variables CSS et le media query. `'light'` et `'dark'` figent les valeurs, pour le repli du § 7.

- [ ] **Écrire `scripts/dev-sync.sh <session-id> [mod…]`** : `rsync -a --delete --exclude .claude-plugin/types --exclude tsconfig.json` de chaque mod vers `~/.claude/dev-mods/<session-id>/<mod>/`, après avoir lancé `scripts/sync-shared.sh`. Ce script remplace l'étape « commit » dans toutes les tâches.
- [ ] **Tests qui échouent** dans `session-hud/hooks/sienne.test.ts` :
  - `accent tokens stay legible on both bases` : `contrast(NATIVE.accent, '#f4ece0') >= 3` et `contrast(NATIVE.accent, '#17110d') >= 3` ;
  - `every drawing carries both schemes and reduced motion` : pour `dot`, `ring`, `bar`, `ribbon`, `timeline`, `backdrop`, la sortie contient `prefers-color-scheme: dark` et `prefers-reduced-motion`. Avec `scheme: 'dark'`, elle contient `#17110d` ou la valeur sombre attendue, sans media query de couleur ;
  - `a ribbon never goes below the minimum width and escapes its title` : `ribbon(100, { id: 'a', icon: 'commit', title: 'a < b & "c"' })` contient `width="240"` et `a &lt; b &amp; &quot;c&quot;`, mais pas `a < b` ;
  - `two drawings never share an id` : `ribbon(400, { id: 'x1', … })` et `ribbon(400, { id: 'x2', … })`, aucun `id="…"` commun ; idem pour `ring`, `bar` et `timeline` avec des `id` distincts ;
  - `a waiting ribbon shimmers, a settled one does not` : `waiting: true` contient `<animate`, `waiting: false` n'en contient pas ;
  - `ring and bar clamp their fraction` : `ring(1.7)` = `ring(1)`, `bar(200, -1)` = `bar(200, 0)` ;
  - `sizes stay under the Svg limit` : `backdrop().length < 131072`.
- [ ] Lancer `$X plugin test session-hud` : les nouveaux tests échouent (module absent).
- [ ] **Implémenter `shared/sienne.ts`.** Valeurs : spec § 4.1. Animations et durées : spec § 4.4. Relief : dégradé vertical, liseré `highlight` d'un pixel, `feDropShadow` doux. Le ruban s'estompe vers la droite. Le fond suit l'essai (halos `feGaussianBlur` 90, dérive 24/31/38 s, grain `feTurbulence` 0,09).
- [ ] `scripts/sync-shared.sh`, puis `$X plugin test session-hud` : tout est vert (8 tests existants + 7 nouveaux).

### Tâche 2 : `session-hud` — fond, `/fond`, bande Sienne

**Fichiers :** modifier `session-hud/hooks/register.tsx`, `session-hud/hooks/gauge.ts` (supprimé : remplacé par `sienne`), `session-hud/types/index.d.ts`, `session-hud/hooks/band.test.tsx`, `session-hud/README.md`.

**Consomme :** `dot`, `ring`, `backdrop`, `NATIVE` (tâche 1). **Produit :** la clé `$.store` `backdrop` (`'on' | 'off'`) et la commande `/fond`.

- [ ] **Tests qui échouent** (`band.test.tsx`) :
  - `the session sets its backdrop at start, and draws only its own` : après `session.start`, un `ui.backdrop` a été vu avec `id: 'sienne'` et sans `tint`. Le rendu `Backdrop` avec `props.plugin: 'session-hud'` donne un `Svg` dont la source contient `feTurbulence`. Avec `props.plugin: 'other'`, il rend le résultat de `next` ;
  - `/fond toggles the backdrop and remembers it` : `/fond`, puis `$.store.get('backdrop') === 'off'` et `ui.backdrop(undefined)` vu. Une nouvelle `session.start` ne pose pas de fond. Un second `/fond` le remet ;
  - `the band wears Sienne` : la source de l'anneau du contexte contient `prefers-color-scheme`. Le compteur « en arrière-plan » a une couleur dans `NATIVE`. Aucune couleur Nord (`#88C0D0`, `#A3BE8C`, `#4C566A`) ne reste dans l'arbre.
- [ ] `$X plugin test session-hud` : échec attendu.
- [ ] **Implémenter.**
  - `session.start` : `$.ui.backdrop({ id: 'sienne' })` si le store ne dit pas `off`.
  - `on('ui.render', { component: 'Backdrop' })` → `<Svg source={backdrop()} alt="fond" />`.
  - `$.command.register({ name: 'fond', description: 'Allume ou éteint le fond animé' })` et son `command.run`.
  - Bande : pilule SVG derrière la rangée si l'essai a validé le point 3 (largeur `columns*8.9-24`, minimum `MIN_WIDTH`), sinon `Box borderStyle="round" borderColor={NATIVE.accentBorder} backgroundColor={NATIVE.accentFill}`.
  - Pastille et anneau via `dot` et `ring`. La liste dépliante est habillée de la même façon.
- [ ] Tests verts, puis `$X plugin validate session-hud`, `scripts/dev-sync.sh`, `tsc -p` sur la copie de dev.
- [ ] **Jalon à l'écran :** capture de la bande et du fond, en clair (et en sombre si l'utilisateur bascule). La montrer.

### Tâche 3 : `background-tasks` — habillage, tests de workflows

**Fichiers :** modifier `background-tasks/hooks/pane.tsx`, `background-tasks/hooks/register.tsx`, `background-tasks/hooks/pane.test.tsx`. Créer `background-tasks/hooks/workflows.test.ts` (12 tests déplacés : `logic.test.ts` workflows 4 et chiffres d'agents 3, `parse.test.ts` traces de workflow 5, importés désormais de `./shared/workflows`).

**Consomme :** `dot`, `bar`, `ring`, `NATIVE` (tâche 1).

- [ ] Déplacer les 12 tests, avec leurs imports réécrits vers `./shared/workflows` et `./shared/format`. `$X plugin test background-tasks` : 5 + 12 tests verts. Ils testent du code existant et doivent passer tels quels.
- [ ] **Test qui échoue** `the pane wears Sienne` : les sources des pastilles et des barres contiennent `prefers-color-scheme`. Une barre de run en cours contient `<animate` ou `animation:`. Les titres de section sont en `size="caption"` et en majuscules. Aucune couleur Nord ne reste.
- [ ] **Implémenter** : remplacer `NORD`/`dotSvg`/`barSvg`/`ringSvg` de `shared/palette` par ceux de `sienne`. Le titre de section est suivi d'un filet natif (`Box` hauteur 0, `borderStyle="single"`, bordure haute seulement, si l'API le permet ; sinon pas de filet).
- [ ] Tests verts, `validate`, `dev-sync`, `tsc`.
- [ ] Supprimer `shared/palette.ts` une fois que plus aucun mod ne l'importe (`grep -rn "shared/palette" */hooks/*.ts*` ne renvoie rien). Relancer `sync-shared.sh`.

### Tâche 4 : `conversation-cards` — sortir les cartes du cockpit (sans rien changer à l'affichage)

**Fichiers :**
- Créer `conversation-cards/` :
  - `.claude-plugin/plugin.json` (`name`, `version` `0.1.0`, `description`, `types`) ;
  - `hooks/hooks.json`, `tsconfig.json` (copie de celui de `session-hud`), `types/index.d.ts`, `README.md` ;
  - `hooks/register.tsx`, `hooks/cards.tsx` (déplacé), `hooks/tools.tsx` (rendu ToolUse sorti de `register.tsx:447-513`) ;
  - `hooks/parse.ts` (groupe « cartes » de la spec § 6.2), `hooks/actions.ts` (groupe « cartes »), `hooks/logic.ts` (`CONTRACT`, `spinnerSuffix`, `toolCard`, `toolTail`, `ToolCard`) ;
  - `hooks/facts.ts` (collecteur de `cardFacts`), `hooks/fixtures.ts` (déplacé), `hooks/cards.test.tsx`, `hooks/parse.test.ts`, `hooks/tools.test.ts`.
- Créer `shared/commits.ts` (`commitBlocks` et son type, déplacés depuis `openspec-cockpit/hooks/parse.ts`).
- Modifier `.claude-plugin/marketplace.json` (ajout de `conversation-cards`).

**Interfaces produites :**
- État `conversation-cards` : `toolTimes`, `isToolOpen`, `isMessageOpen`, `qaMarks`, `reportOpen`, `briefs`, `cardFacts`, `projectRoot`, `toggles: { cards: boolean; contract: boolean }`, `contextPercent: number | null`.
- `collectFacts($, root): Promise<CardFacts>` : `git log -n 20 --format=%s` et noms des sous-dossiers de `openspec/changes/` (s'il existe). Appelé à `session.start`, toutes les 30 s et à `turn.complete`. N'écrit que si la valeur change.
- Commande `/cartes` : `/cartes` affiche l'état, `/cartes off|on`, `/cartes contrat off|on`. Les bascules sont gardées dans `$.store` sous `toggles`, activées par défaut. `$.store` étant propre à chaque plugin, l'ancien réglage du cockpit n'est pas repris : c'est le repli prévu au § 6.3 de la spec.
- Section `prompt.compose` : id `conversation-cards:contract`, texte `CONTRACT` inchangé.

- [ ] **Déplacer les 44 tests** de la spec § 6.4 avec `fixtures.ts`, sans toucher leurs assertions, sauf : plugin `conversation-cards` au lieu de `openspec-cockpit`, `/cartes off` au lieu de la bascule du cockpit (test 572), spinner qui n'attend plus que le contexte (test 323 : l'assertion sur l'étape et les agents disparaît, celle sur le contexte reste).
- [ ] `$X plugin test conversation-cards` : échec attendu (mod absent).
- [ ] **Déplacer le code** (§ 6.1-6.3 de la spec). `register.tsx` ne garde que : `session.start` (racine du projet, facts, commandes, horloge 30 s), `prompt.compose`, `tool.call` (`toolTimes` bufferisé, écrit au rafraîchissement), `ui.render` AssistantMessage, ToolUse, UserMessage (notification de tâche seulement, sinon `next(e)`), Spinner. `cleanMarkdown`, `truncate` et `formatDuration` viennent de `./shared/format`, `commitBlocks` de `./shared/commits`. Une `projectRoot` est toujours fixée (le mod est actif partout) : la racine git, sinon le `cwd`.
- [ ] Tests verts : 44, plus 3 de formatage à recopier depuis `logic.test.ts` vers `parse.test.ts` du nouveau mod (ils testent `shared/format`). `validate`, `dev-sync`, `tsc`.
- [ ] Le cockpit **n'est pas encore touché** à cette étape. Le vérifier : ses 104 tests restent verts. Pendant que les deux tournent dans la session de dev, les cartes risquent d'apparaître deux fois : charger `conversation-cards` seulement à la tâche 6 (`dev-sync.sh <session> conversation-cards openspec-cockpit` ensemble).

### Tâche 5 : `conversation-cards` — habillage Sienne

**Fichiers :** modifier `conversation-cards/hooks/cards.tsx`, `conversation-cards/hooks/tools.tsx`, `conversation-cards/hooks/cards.test.tsx`.

**Consomme :** `ribbon`, `icon`, `pills` (remplace `pillsSvg`), `NATIVE` (tâche 1).

- [ ] **Tests qui échouent** (`cards.test.tsx`) :
  - `each card opens on a ribbon` : pour chaque fixture (question, rapport, QA, commit, bloc cockpit), le premier enfant de la carte est un `Svg` dont la source contient le titre attendu échappé. Q1 a `badge: 'Q1'` ;
  - `an unanswered question shimmers until answered` : avant réponse, la source du ruban contient `<animate`. Après `insertAnswers`, elle n'en contient plus ;
  - `a commit card draws its check` : la source contient le chemin de coche avec `stroke-dashoffset` animé ;
  - `cards under a whole message stay compact` : sous un message affiché en entier, une carte n'a que le ruban et des boutons, sans répéter de texte du message (même règle qu'aujourd'hui, assertion reprise) ;
  - `no Nord colour survives in a card tree` : aucune des 7 valeurs `NATIVE.nord` de l'ancien `theme.ts`.
- [ ] **Implémenter** : un helper `cardFrame(els, key, ribbonOpts, body)` dans `cards.tsx`. Il rend une `Box` colonne avec `borderStyle="round"`, `borderColor={NATIVE.accentBorder}`, `overflow="hidden"`, puis le `Svg` du ruban, de largeur `clamp(240, columns*6, 640)` et d'`id` égal à la clé de la carte, puis le corps. Si l'essai a validé le point 3, le corps reçoit un fond verre SVG en absolu. Tous les `questionCard`, `commitCard`, `qaBlock`, `decisionsBlock`, etc. passent par `cardFrame`. Les cartes d'outils prennent une icône (`tool`) et une pastille d'état (`dot`).
- [ ] Tests verts, `validate`, `dev-sync`, `tsc`.

### Tâche 6 : `openspec-cockpit` allégé

**Fichiers :**
- Modifier `openspec-cockpit/hooks/register.tsx`, `parse.ts`, `logic.ts`, `actions.ts`, `collect.ts`, `pane.tsx`, `svg.ts`, `types/index.d.ts`, `.claude-plugin/plugin.json` (version `0.14.0`).
- Supprimer : `cards.tsx`, `theme.ts`, `fixtures.ts`.
- Tests : supprimer ou réduire `cockpit.test.tsx`, `logic.test.ts`, `parse.test.ts` et `v2.test.ts` selon la spec § 6.4.

- [ ] **Retirer les tests** partis ou supprimés (§ 6.4). Le test 288 perd ses assertions agents, workflows et sessions.
- [ ] **Retirer le code** (§ 6.1-6.3) :
  - hooks des cartes, spinner, ToolUse, ligne de notification ;
  - consigne, enveloppe de thème, `/cockpit-theme` ;
  - `refreshLive`, `announceFinishedRuns` ;
  - atomes et types `live`, `activity`, `toolCount`, `isBandHidden`, `theme`, `Snapshot.workflows`, `Snapshot.sessions` ;
  - bascules `cards`, `contract`, `band` ;
  - code mort (`toggleQaNote`, `saveQaNote`, `qaNotes`, `qaEditing`) ;
  - sections Session, Agents et workflows, Autres sessions ;
  - entrée workflow de `nextAction`, `statusLine` et `summaryMarkdown`.

  `commitBlocks` vient désormais de `./shared/commits`.
- [ ] `$X plugin test openspec-cockpit` : 34 tests verts. `grep -n "useSvgTheme\|recolor\|NORD\|argile" openspec-cockpit/hooks/*.ts*` : rien.
- [ ] `validate`, `dev-sync.sh <session> conversation-cards openspec-cockpit`, `tsc` pour les deux.
- [ ] **Jalon à l'écran :** une réponse de Claude avec carte Q1 et carte de commit (la réponse de ce tour peut servir), plus le panneau cockpit encore à l'ancien dessin. La montrer.

### Tâche 7 : `openspec-cockpit` redessiné

**Fichiers :** modifier `openspec-cockpit/hooks/pane.tsx`, `svg.ts` (réduit à des adaptateurs vers `sienne`, ou supprimé si plus rien ne s'y rattache), `cockpit.test.tsx`.

**Consomme :** `ring`, `timeline`, `bar`, `pills`, `dot` (tâche 1).

- [ ] **Tests qui échouent** :
  - `the pane opens on a large ring and the phase timeline` : le premier `Svg` du panneau riche est un anneau de 64 px dont le libellé vaut `"<fait>/<total>"` des tâches du change. Le suivant est une `timeline` dont `current` est l'index de `cycleStep` ;
  - `group progress uses growing bars` : chaque groupe de tâches a un `bar` dont la fraction vaut `done/total` ;
  - `no Nord colour survives in the pane`.
- [ ] **Implémenter** :
  - En-tête : `Box` ligne avec `ring(…, { size: 64, label })` et une colonne native (nom du change en `weight="semibold"`, phase en `dimColor`, prochaine action en `NATIVE.accent`). La largeur se calcule avec `columns*8.9`.
  - Puis la `timeline` des étapes `CYCLE`.
  - Puis les sections existantes (groupes, décisions, rituel, passation), avec un titre en petites capitales.
  - Pas de bouton dans les listes de groupes.
- [ ] Tests verts, `validate`, `dev-sync`, `tsc`.
- [ ] **Jalon à l'écran :** le panneau cockpit en clair (et en sombre si l'utilisateur bascule). Le montrer.

### Tâche 8 : documentation, mémoire, installation

**Fichiers :** modifier `README.md` (tableau des 4 mods, installation, `/fond`, `/cartes`), `openspec-cockpit/README.md` (allégé), `conversation-cards/README.md`. Mémoire : `reference_openspec_cockpit_mod.md` (projet demo) et une nouvelle mémoire dans ce projet (thème Sienne, découpage, `dev-sync.sh`).

- [ ] Rédiger les README et la mémoire.
- [ ] Tous les tests : `for m in session-hud background-tasks conversation-cards openspec-cockpit; do $X plugin test $m; done`. Totaux attendus : session-hud ≥ 18, background-tasks ≥ 18, conversation-cards ≥ 52, openspec-cockpit ≥ 37.
- [ ] **Demander à l'utilisateur** le feu vert pour l'installation, qui modifie sa configuration utilisateur. Ensuite :
  - `claude plugin marketplace update local-mods` ;
  - `claude plugin install <mod>@local-mods --scope user` pour `session-hud`, `background-tasks` et `conversation-cards` ;
  - mise à jour de `openspec-cockpit` ;
  - `claude plugin list` pour vérifier ;
  - dire à l'utilisateur de faire `/reload-plugins` dans ses autres sessions.
- [ ] Supprimer les copies de dev de cette session une fois les mods installés, pour ne pas les charger deux fois.
