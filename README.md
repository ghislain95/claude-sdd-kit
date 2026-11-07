# claude-sdd-kit

A **spec-driven** development workflow for Claude Code that you can install in any project, whatever
the language: the OpenSpec cycle, specialised sub-agents, mandatory review, mechanical git
guardrails and CI.

A project's rules can't be copied from another project. So `/sdd-core:sdd-init` starts by
**reverse-documenting the actual code** (modules, stack, CI commands, observed architecture,
vocabulary), and only generates rules and agents from what it has proven.

```
/opsx:new → [adversarial pass] → /opsx:ff → /opsx:apply → code-reviewer → /opsx:verify
         → commit → /opsx:archive → post-archive → PR (+ merge, depending on the autonomy level)
```

## Set up a project with a single prompt

1. Open Claude Code **at the root of the project** (CLI, desktop app or IDE extension).
2. Copy the prompt below and paste it as is.
3. Claude installs the tools and plugins, reverse-documents the code, generates the rules, the
   agents, the git guardrail and the CI, then commits everything on a `chore/sdd-init` branch. It
   only stops you at three points: before installing a tool on your machine, to validate what it
   understood of the code, and for one round of choices (git autonomy, language, options).
4. When it is done, restart Claude Code: the agents, the hook and the `/opsx:*` commands are loaded.

Allow 30 to 90 minutes depending on the size of the project. The same prompt, run again on a project
that is already set up, updates it to the latest version of the kit while keeping your changes.

```text
Install the "sdd-kit" development workflow in this project (https://github.com/ghislain95/claude-sdd-kit): spec-driven development with OpenSpec, specialised agents, mandatory review, git guardrail and CI. Go through the steps in order, without skipping any.

1. Prerequisites — check with Bash: `node -v` (≥ 20), `openspec --version`, `jq --version`, `perl -v`, `gh auth status`, `git status`. For each missing tool, give me the install command (npm install -g @fission-ai/openspec@latest, brew install jq, brew install gh…) and wait for my go-ahead before installing anything on my machine. Without jq, the git guardrail would block every one of your git commands: this one is blocking.

2. Claude Code plugins — run through Bash:
   claude plugin marketplace add anthropics/claude-plugins-official
   claude plugin marketplace add ghislain95/claude-sdd-kit
   claude plugin install sdd-core@sdd-kit
   The first line is needed even if it seems redundant (it is a no-op when the official marketplace is already there): sdd-core depends on superpowers from that marketplace and won't load without it. The install should report "+ 1 dependency: superpowers"; check with claude plugin list that both sdd-core and superpowers are enabled.
   If sdd-core is already installed, update instead: claude plugin marketplace update sdd-kit, then claude plugin update sdd-core@sdd-kit.
   If the project has a web interface, also offer me: claude plugin install sdd-ui@sdd-kit and claude plugin install frontend-design@claude-plugins-official.
   Ask me whether I use the Claude desktop app. If yes, offer the optional desktop mods (OpenSpec cockpit pane, message cards, session band, background-tasks pane): claude plugin install openspec-cockpit@sdd-kit, conversation-cards@sdd-kit, session-hud@sdd-kit, background-tasks@sdd-kit (one command each). If I take them, tick the `cockpit` option in phase 2 of the setup.

3. OpenSpec profile — run `openspec config list`. The workflow needs these workflows: propose, explore, new, continue, apply, ff, sync, archive, bulk-archive, verify, onboard. If any are missing, ask me to run `openspec config profile` in my terminal (it is interactive), pick the custom profile, tick them all, then carry on.

4. Project setup — newly installed plugins only load in the next session, so don't look for /sdd-core:sdd-init now. Read ~/.claude/plugins/marketplaces/sdd-kit/plugins/sdd-core/skills/sdd-init/SKILL.md directly and follow it to the letter, with ~/.claude/plugins/marketplaces/sdd-kit/plugins/sdd-core/skills/sdd-init/ as the base directory (templates/, references/). If the last line of CLAUDE.md contains "sdd-kit: installed", the project is already set up: follow the skill's --refresh mode. Respect its stopping points: the validation gate after the reverse-documentation, and the round of questions in phase 2. Only ask me for choices; anything the code, the CI or git can tell you, look it up yourself. Never work on the main branch.

5. Wrap-up — give me the final report the skill describes, then tell me to restart Claude Code to load the agents, the hook and the /opsx:* commands. Remind me to turn on auto-update for this marketplace (/plugin → Marketplaces → sdd-kit → Enable auto-update): it is off by default for third-party marketplaces, so without it I won't get new versions of the kit. My first step after that will be /opsx:onboard (a first guided cycle) or the first baseline-<domain> change you proposed.

Full guide if needed: ~/.claude/plugins/marketplaces/sdd-kit/GUIDE.md
```

What the prompt changes on your machine, outside the project: it adds the `sdd-kit` marketplace and
enables the `sdd-core` and `superpowers` plugins (plus `sdd-ui`, `frontend-design` and the desktop
mods if you accept them) in `~/.claude/settings.json`, so for all your projects. `sdd-core` holds
skills and one session-start hook: it only speaks in a project set up with an older kit (see
[Staying up to date](#staying-up-to-date)), takes a few milliseconds and stays silent everywhere
else. `superpowers` adds a session-start hook that loads its guide to using skills; the desktop mods
change the desktop app's display. To remove the kit:
`claude plugin uninstall sdd-core@sdd-kit`, then `claude plugin marketplace remove sdd-kit`.
Context cost: `sdd-core`'s skill descriptions add about 400 tokens to every session
(`claude plugin details sdd-core@sdd-kit` shows the breakdown).

## Contents

| Plugin | Contents |
|---|---|
| **`sdd-core`** | `/sdd-core:sdd-init` (reverse-documentation + workflow install, `--refresh` to update), `/sdd-core:passation`, `/sdd-core:retro`, `sdd-core:domain-modeling`, `/sdd-core:improve-codebase-architecture`, and the templates (agents, `CLAUDE.md`, OpenSpec rules, git hook, CI) |
| **`sdd-ui`** (optional) | `web-design-guidelines`, `break-ui`, `emil-design-eng`, `animate`, `review-animations`, `improve-animations` |
| **Desktop mods** (optional, desktop app only) | `openspec-cockpit`, `conversation-cards`, `session-hud`, `background-tasks` — listed in this marketplace, maintained in [`ghislain95/claude-mods`](https://github.com/ghislain95/claude-mods) |

What `sdd-init` installs in the project: see [`GUIDE.md`](GUIDE.md) §3.

## Manual install (without the prompt)

In Claude Code:

```
/plugin marketplace add anthropics/claude-plugins-official
/plugin marketplace add ghislain95/claude-sdd-kit
/plugin install sdd-core@sdd-kit
```

`superpowers` comes with it as a declared dependency, provided the official marketplace is added
(first line; harmless if it already is).

Then, in the project to set up:

```
/sdd-core:sdd-init
```

The full guide (prerequisites, what happens, day-to-day use, pitfalls) is in [`GUIDE.md`](GUIDE.md).

## Staying up to date

There are two levels, and both matter:

1. **The plugin on your machine.** Auto-update is **off by default** for third-party marketplaces
   like this one. Turn it on once: `/plugin` → **Marketplaces** → `sdd-kit` → **Enable
   auto-update**. Claude Code then checks in the background during a session and tells you when a
   new version is ready (`/reload-plugins` or a restart applies it). Without auto-update:
   `claude plugin marketplace update sdd-kit && claude plugin update sdd-core@sdd-kit`.
2. **Each project you set up.** The files `sdd-init` generated (CLAUDE.md, agents, hook, CI…) are
   copies: a new kit version doesn't change them. In each project, run the install prompt again (or
   `/sdd-core:sdd-init --refresh`): it applies what comes from the kit and keeps your local edits.
   You don't have to remember it: when you open a session in a project set up with an older kit,
   `sdd-core` shows a one-line notice (and Claude mentions it in its first reply).

What changed in each version: [`CHANGELOG.md`](CHANGELOG.md). Publishing a version (maintainers):
[`MAINTAINING.md`](MAINTAINING.md).

## Credits

Vendored skills keep their upstream `LICENSE` and a `SOURCE.md` (upstream repository, commit,
changes): `mattpocock/skills`, `emilkowalski/skills`, `vercel-labs/agent-skills`. The git guardrail
hook is adapted from `mattpocock/skills` (`git-guardrails-claude-code`, MIT).
