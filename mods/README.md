# claude-mods

Claude Code mods (function-hook plugins) for the desktop app: a session band, the background tasks, Claude's
messages as cards, and an OpenSpec cockpit. The repository is a marketplace named `local-mods`.

| Mod | What it does |
|---|---|
| [`session-hud`](session-hud/README.md) | Every project: the band above the prompt (context, cost or rate limit, time, tools, model, background count) and the window's animated Terre de Sienne backdrop (`/fond`) |
| [`background-tasks`](background-tasks/README.md) | Every project: the « En arrière-plan » pane (`/arriere-plan`): services with their port, workflow runs with phases and agents |
| [`conversation-cards`](conversation-cards/README.md) | Every project: Claude's messages as cards (questions, reports, QA, cockpit block, commits), compact tool rows, the context in the spinner, the display contract (`/cartes`) |
| [`openspec-cockpit`](openspec-cockpit/README.md) | OpenSpec projects only: the dashboard pane (ring, cycle timeline, next action, groups, decisions, ritual, handoff), gate alerts, status line |

All four share one theme, **Terre de Sienne** (ochre, burnt earth, cream), in light and dark following the app.
Its tokens and SVG drawings live in `shared/sienne.ts`; `scripts/sync-shared.sh` copies `shared/` into each mod.

## Install from GitHub

At the prompt of a Claude Code session, one line per mod (answer `y` to add the marketplace, then pick a scope):

```
/plugin install session-hud --marketplace ghislain95/claude-mods
/plugin install background-tasks --marketplace ghislain95/claude-mods
/plugin install conversation-cards --marketplace ghislain95/claude-mods
/plugin install openspec-cockpit --marketplace ghislain95/claude-mods
```

From a shell:

```bash
for mod in session-hud background-tasks conversation-cards openspec-cockpit; do
  claude plugin install "$mod" --marketplace ghislain95/claude-mods
done
```

## Install from a local clone (to edit the mods)

```bash
claude plugin marketplace add ~/dev/workspace/claude/claude-mods
for mod in session-hud background-tasks conversation-cards openspec-cockpit; do
  claude plugin install "$mod@local-mods" --scope user
done
```

The marketplace is read in place: edit a mod here, then run `/reload-plugins` (or start a
new session). Check and test a mod before using it:

```bash
claude plugin validate ~/dev/workspace/claude/claude-mods/openspec-cockpit
claude plugin test ~/dev/workspace/claude/claude-mods/openspec-cockpit
```

Requires a Claude Code build that knows mods (2.1.29x+, the desktop app's).

## Developing

Edit the files in `shared/`, never their copies under `<mod>/hooks/shared/`. To try the mods in a session that
hot-reloads its own mods folder:

```bash
scripts/dev-sync.sh <session-id>
```
