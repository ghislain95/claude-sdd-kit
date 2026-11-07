---
name: passation
description: Écrit un document de passation pour reprendre le travail dans une session neuve (/clear ou nouvelle conversation) sans traîner les impasses du contexte actuel. Fichier dans .claude/passation/ + copie dans le presse-papier si disponible.
argument-hint: "[objectif de la prochaine session]"
disable-model-invocation: true
allowed-tools: Write, Bash(mkdir -p .claude/passation), Bash(date *), Bash(command -v *), Bash(LC_ALL=en_US.UTF-8 pbcopy *), Bash(LC_ALL=en_US.UTF-8 pbpaste), Bash(LC_ALL=en_US.UTF-8 pbpaste *), Bash(wl-copy *), Bash(wl-paste *), Bash(xclip *), Bash(cmp *), Bash(echo OK), Bash(git status *), Bash(git log *), Bash(git branch *), Bash(openspec list), Bash(openspec list *)
---

# Passation

Pourquoi : `/compact` résume la conversation, mais en garde la forme. Les impasses, les
hypothèses fausses et les debugs ratés restent dedans. Une passation repart de zéro avec
seulement ce qui compte. La session suivante doit pouvoir reprendre **exactement** là où on
en est, sans relire cette conversation.

Si `$ARGUMENTS` est fourni, il décrit l'objectif de la prochaine session : adapter tout le
document à cet objectif (ce qui ne le sert pas sort).

## 1. Vérifier avant d'écrire (pas de mémoire seule)

- `git status --short`, `git log --oneline -5` et `git branch --show-current` pour l'état réel.
- `openspec list` si un change OpenSpec est en cours.
- Toute affirmation « c'est fait » doit être confirmée par un fichier, un test lancé ou un
  commit. Si ce n'est pas vérifiable maintenant, elle est marquée **supposé**.

## 2. Écrire le fichier

Chemin : `.claude/passation/AAAA-MM-JJ-HHMM-<sujet-kebab>.md` (dossier gitignoré ; `mkdir -p` si
absent). L'heure locale (heures + minutes, sans séparateur) départage plusieurs passations du même
jour : la lire avec `date +%Y-%m-%d-%H%M`, jamais de mémoire. Prose dans la langue des docs du
projet (`CLAUDE.md` §Langue ; français par défaut). Identifiants, chemins et commandes tels quels.
Si `.claude/passation/` n'est pas encore gitignoré, le signaler à l'utilisateur (ne pas éditer
`.gitignore` soi-même pendant une passation).

Structure fixe. Une section vide s'écrit « — » ; on ne la supprime pas.

```md
# Passation — <sujet> (<AAAA-MM-JJ HH:MM>)

> Session suivante : lis ce document, reformule-moi l'objectif et la prochaine étape,
> puis **attends mon GO** avant d'agir.

## Objectif
<1–2 phrases : ce qu'on cherche à obtenir, et pourquoi.>

## Où on en est
- Change OpenSpec : `<id>` — étape du cycle : cadrage | passe adversariale | ff | apply | review | verify | commit | archive | post-archive (ou « aucun »)
- Branche : `<branche>` — état git : <propre | N fichiers modifiés non commités : lesquels>
- <2–4 puces d'état factuel>

## Décisions prises
- <décision> — pourquoi : <raison> — ✅ validée par l'utilisateur | 🟡 proposée, pas validée

## Tenté et raté (ne pas refaire)
- <tentative> → <pourquoi ça a échoué / ce que ça a appris>

## Faits établis
- ✔ vérifié : <fait> (preuve : `<fichier:ligne>` | `<commande>` | commit `<sha>`)
- ? supposé : <fait non vérifié>

## Fichiers clés
- `<chemin>` — <rôle en une ligne>

## Questions ouvertes (pour l'utilisateur)
- <question>

## Prochaine étape
1. <action concrète et immédiate>
2. …

## Outils suggérés
- <skill / agent / commande> — <pour quoi faire>

## Mode de travail impératif
- <Règles de langue du projet, reprises de `CLAUDE.md` §Langue.>
- Cadrage **avec** l'utilisateur : objectif d'abord, peu de questions, un exemple concret
  chacune. Proposal validé par lui **avant** `/opsx:ff`. Une fois le cadrage validé, mener le
  change jusqu'au bout (back, front, tests, docs) **sans demander de GO entre les tranches** ;
  ne s'arrêter que pour une vraie décision ou un trou de design.
- Review `code-reviewer` sur le diff non commité avant `/opsx:verify`.
- Git : selon `docs/CONTRIBUTING.md` §2 et le niveau d'autonomie de `CLAUDE.md` (commit seul,
  jusqu'à la PR, ou jusqu'à la fusion) — branche `<type>/<change-id>`, jamais sur la branche
  protégée, Conventional Commits sujet + corps, scope = id du change. Ordre : review →
  `/opsx:verify` → commit(s) d'implémentation → `/opsx:archive` + post-archive → commit d'archive
  → PR → fusion (si autorisée : CI verte + review sans BLOQUANT/MAJEUR). Le hook
  `block-git-writes.sh` impose la partie mécanique ; les conditions de fusion relèvent de la
  discipline de l'agent.
- <Pièges d'environnement constatés dans la session (version de runtime, variable d'env,
  port…) — ex. « l'outil de build exige une version précise du runtime, le shell par défaut en a
  une autre ».>
- Si `graphify-out/` existe : rafraîchir le graph (`graphify check-update .`) avant de s'y fier.
```

## Règles de contenu

- **Ne pas recopier ce qui existe déjà** (proposal, design, tasks, specs, ADR, commits,
  diffs) : pointer par chemin. La passation contient ce qui n'est écrit **nulle part
  ailleurs** : décisions orales, impasses, hypothèses, intentions.
- **Impasses = section la plus précieuse.** Un debug raté non consigné sera refait.
- **Marquer les statuts honnêtement.** Une décision évoquée mais pas confirmée par
  l'utilisateur est 🟡.
- Masquer les secrets (clés, mots de passe, tokens, URLs signées) et les données personnelles
  (aucune donnée réelle d'utilisateur, de client ou de patient).
- Dense : viser 40–120 lignes. Pas de récit chronologique de la session.

## 3. Livrer

1. Presse-papier (optionnel, selon ce qui est installé — `command -v pbcopy wl-copy xclip`) :
   - macOS : `LC_ALL=en_US.UTF-8 pbcopy < <chemin>`. **Le préfixe `LC_ALL` est obligatoire** : le
     shell de l'agent n'a pas de locale, et `pbcopy` lit alors l'UTF-8 comme du MacRoman (« é »
     devient « √© »). Vérifier l'aller-retour : `LC_ALL=en_US.UTF-8 pbpaste | cmp -s - <chemin> && echo OK`.
   - Linux Wayland : `wl-copy < <chemin>` puis `wl-paste | cmp -s - <chemin> && echo OK`.
   - Linux X11 : `xclip -selection clipboard < <chemin>` puis
     `xclip -selection clipboard -o | cmp -s - <chemin> && echo OK`.
   - Aucun outil, ou vérification en échec : ne pas annoncer « copié » ; ce n'est pas une erreur,
     le chemin du fichier suffit.
2. Répondre en 3 lignes max : le chemin du fichier, l'état du presse-papier (« copié (vérifié) » ou
   « non copié »), et la phrase à coller si l'utilisateur préfère pointer le fichier :
   `Lis .claude/passation/<fichier>.md et reprends exactement où on en était.`

Ne lancer aucun autre travail : la passation clôt la session.
