# Desktop mods

Claude Code mods (function-hook plugins) for the desktop app: a session band, the background tasks, Claude's
messages as cards, and an OpenSpec cockpit. They are plugins of the `claude-toolbox` catalog, category `mod`.
They lived in the `ghislain95/claude-mods` repository until they were folded in here, history included.

| Mod | What it does |
|---|---|
| [`session-hud`](session-hud/README.md) | Every project: the band above the prompt (context, cost or rate limit, time, tools, model, background count) and the window's animated Terre de Sienne backdrop (`/fond`) |
| [`background-tasks`](background-tasks/README.md) | Every project: the « En arrière-plan » pane (`/arriere-plan`): services with their port, workflow runs with phases and agents |
| [`conversation-cards`](conversation-cards/README.md) | Every project: Claude's messages as cards (questions, reports, QA, cockpit block, commits), compact tool rows, the context in the spinner, the display contract (`/cartes`) |
| [`openspec-cockpit`](openspec-cockpit/README.md) | OpenSpec projects only: the dashboard pane (ring, cycle timeline, next action, groups, decisions, ritual, handoff), gate alerts, status line |

All four share one theme, **Terre de Sienne** (ochre, burnt earth, cream), in light and dark following the app.
Its tokens and SVG drawings live in `shared/sienne.ts`; `scripts/sync-shared.sh` copies `shared/` into each mod.

## Install from GitHub

```bash
claude plugin marketplace add ghislain95/claude-toolbox
for mod in session-hud background-tasks conversation-cards openspec-cockpit; do
  claude plugin install "$mod@claude-toolbox"
done
```

## Install from a local clone (to edit the mods)

```bash
claude plugin marketplace add <path to your claude-toolbox clone>
for mod in session-hud background-tasks conversation-cards openspec-cockpit; do
  claude plugin install "$mod@claude-toolbox" --scope user
done
```

A local clone is read in place: edit a mod here, then run `/reload-plugins` (or start a new session). Check and
test a mod before using it, from the clone's root:

```bash
claude plugin validate mods/openspec-cockpit
claude plugin test mods/openspec-cockpit
```

Requires a Claude Code build that knows mods (2.1.29x+, the desktop app's).

## Developing

Edit the files in `shared/`, never their copies under `<mod>/hooks/shared/`. To try the mods in a session that
hot-reloads its own mods folder:

```bash
mods/scripts/dev-sync.sh <session-id>
```
