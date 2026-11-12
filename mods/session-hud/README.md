# session-hud

Mod Claude Code actif dans tous les projets : une ligne au-dessus du prompt.

De gauche à droite : un point qui pulse quand Claude travaille, l'anneau et le pourcentage du contexte (vert, puis ambre à 60 %, rouge à 85 %), le coût de la session ou, sans coût, la limite d'usage la plus haute, la durée de la session, le nombre d'appels d'outils et d'erreurs, le modèle. À droite, « ⚙ N en arrière-plan » quand des tâches tournent encore (services, workflows, agents) ; un clic ouvre le panneau du mod `background-tasks`.

La bande ne se redessine qu'au rafraîchissement (30 s) et en fin de tour, jamais à chaque appel d'outil. Dans le terminal, elle tient sur une ligne de texte.

Sur desktop, le mod pose aussi le fond de la fenêtre, en Terre de Sienne, clair ou sombre selon le thème de l'app. On y voit la couleur de base, trois halos flous qui dérivent lentement et un grain léger, sous les panneaux en verre dépoli de l'app. `/fond` l'éteint ou le rallume, et le choix est gardé d'une session à l'autre. Le mouvement s'arrête quand le système demande de réduire les animations.
