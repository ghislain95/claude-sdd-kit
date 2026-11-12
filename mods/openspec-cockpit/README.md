# openspec-cockpit (v0.14)

Mod Claude Code qui ajoute un panneau OpenSpec à l'app desktop. Il s'active seul dans tout projet qui a `openspec/` ou `.claude/passation/`, et reste muet ailleurs. Ce qui dépend d'un outil du projet n'apparaît que si le projet l'a (voir « Selon le projet »).

Depuis la v0.14, le mod ne fait plus que le panneau, les portes du cycle, la ligne de statut et l'outil `status`. Le reste a sa place dans d'autres mods du même dépôt :
- les cartes du fil, les cartes d'outils, le spinner et la consigne de format sont dans `conversation-cards` ;
- la bande au-dessus du prompt et le fond animé sont dans `session-hud` ;
- le panneau séparé des agents, workflows et services est dans `background-tasks` ; le cockpit en affiche le contenu dans sa propre section.

Thème : Terre de Sienne, en clair ou en sombre selon le thème de l'app. Nord, Argile et `/cockpit-theme` ont disparu.

## Le panneau (barre latérale droite, ouvert seul)

De haut en bas. Chaque section se replie au clic sur son titre, et cet état est mémorisé.

1. **Tête** : un grand anneau rempli au prorata des tâches du change (« 2/4 »), le nom du change, son étape, la branche. Dessous, la **frise des 7 étapes** du cycle : le trait se trace jusqu'à l'étape en cours, qui pulse.
2. **Prochaine action** : la règle du cycle appliquée à l'état réel, avec un bouton.
   - Graph périmé : `graphify update .`.
   - Apply : « groupe N, x/y » et `/opsx:apply`.
   - Clôture : review, puis verify avec la copie du commit, puis archive.
   - Post-archive : le rituel.

   Les pastilles des portes sont dessous.
3. **En arrière-plan** : les mêmes informations que le panneau du mod `background-tasks`, dessinées de la même façon. On y trouve les services que Claude a laissés tourner (avec leur port), les workflows en cours (phases, agents, modèle, tokens), les agents de la session et les runs terminés récemment. Comme l'app range deux panneaux en onglets au lieu de les empiler, le cockpit les affiche lui-même pour qu'on voie tout d'un coup d'œil. Dans un projet OpenSpec, le panneau séparé ne s'ouvre donc plus tout seul.
4. **Progression par groupe** : une ligne par groupe de `tasks.md`, avec une barre qui pousse. Le groupe courant porte une lueur qui le parcourt. Aucun bouton dans cette liste.
5. **Décisions** : ✅ prises, 🟡 choix d'agents à confirmer, ⏳ ouvertes. Elles sont lues dans `verification/owner-points.md` et dans la dernière passation. Un clic préremplit « Sur « … » : ».
6. **Post-archive** : la checklist du rituel.
7. **Passation** : les étapes et le bouton [Reprendre].

## Selon le projet

- **graphify** : la pastille du graph, l'alerte avant `/opsx:new` et `/opsx:apply`, le bouton `graphify update .` et l'étape « graph rafraîchi » du rituel n'existent que si le projet a un `graphify-out/` ou un skill `.claude/skills/graphify`.
- **Backlog** : l'étape « backlog → ✅ SHIPPED » du rituel cherche un fichier `*backlog*.md` à la racine, puis jusqu'à trois niveaux sous `docs/` (sauf `docs/archive`). Sans fichier, l'étape disparaît.
- **Notifications** : leur titre est le nom du dossier du projet.

## Commandes

- `/cockpit` ouvre ou ferme le panneau.
- `/ou-en-suis-je` donne le résumé texte.
- `/cockpit-toggle [statut|portes|panneau] [on|off]` coupe une brique ; le choix est mémorisé.
