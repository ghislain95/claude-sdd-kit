# Guide — installing and using the SDD workflow with Claude Code

> **The easy way**: copy the prompt from the "Set up a project with a single prompt" section of the
> [`README.md`](README.md) and paste it into Claude Code at the root of your project. Claude does
> §2 and §3 of this guide for you. The rest of the guide is still useful to understand what was
> installed and for day-to-day work (§4 onwards).

This guide starts from a blank machine and goes up to the first delivered change. Allow about 15 min
to set up the machine, then 30 to 90 min for `/sdd-core:sdd-init` on a project (depending on its
size; it works mostly on its own and only asks you things at two points).

---

## 1. The idea in one minute

- **The spec is the source of truth.** Expected behaviour lives in `openspec/specs/<domain>/spec.md`.
  Every change goes through an OpenSpec **change** (`openspec/changes/<id>/`: proposal, spec deltas,
  design, tasks). Specs are never edited by hand: they are updated when the change is archived.
- **Specialised agents** (product-owner, architect, one dev per module, tester, code-reviewer,
  doc-writer, devops) each do one job, with their own context. The main session routes.
- **Review is not optional**: `code-reviewer` reads the diff before `/opsx:verify`, without
  politeness, one line per problem, and hunts for tests "fixed so they pass".
- **Mechanical rules are checks**: a hook blocks dangerous git commands (commit on `main`,
  force-push, `reset --hard`…), and CI validates the specs and runs the tests.
- **Facts are the agent's job**: it only asks you for choices, never for what the code can tell it.

---

## 2. Setting up the machine (once per developer)

### 2.1 Tools

| Tool | Why | Install (macOS; Linux: the `apt` equivalent) |
|---|---|---|
| Claude Code | — | https://claude.com/claude-code (CLI, desktop app or IDE extension) |
| Node ≥ 20 | OpenSpec CLI | `brew install node` |
| OpenSpec | change cycle | `npm install -g @fission-ai/openspec@latest` |
| jq | git hook (without jq, **every** `git`/`gh` command from the agent is blocked) | `brew install jq` |
| gh | PRs, CI | `brew install gh`, then `gh auth login` |
| uv + graphify (optional) | queryable map of the code | `brew install uv`, `uv tool install "graphifyy[sql]"`, then `graphify install --platform claude` (`/graphify` skill) |

Check: `node -v && openspec --version && jq --version && gh auth status`.

### 2.2 Extended OpenSpec profile

The workflow uses every `/opsx:*` command (new, ff, continue, apply, verify, sync, archive,
bulk-archive, explore, onboard, propose). In a terminal:

```bash
openspec config profile
```

Pick the custom profile and tick every workflow. Check with `openspec config list`.

### 2.3 Claude Code plugins

In a Claude Code session (any folder):

```
/plugin marketplace add anthropics/claude-plugins-official
/plugin marketplace add ghislain95/claude-toolbox
/plugin install sdd-core@claude-toolbox
```

`sdd-core` declares `superpowers` (official marketplace) as a dependency: it is installed along with
it **only if the official marketplace is added** (first line, harmless if it already is). Without it,
`sdd-core` installs but refuses to load. Check with `/plugin` that both are enabled.

Then turn on auto-update for the kit — it is **off by default** for third-party marketplaces:
`/plugin` → **Marketplaces** → `claude-toolbox` → **Enable auto-update** (see §6).

Optional:

```
/plugin install sdd-ui@claude-toolbox                     # projects with a web interface
/plugin install frontend-design@claude-plugins-official   # building a UI from scratch
/plugin marketplace add JuliusBrussee/caveman
/plugin install caveman@caveman                    # compressed replies (saves tokens)
```

For the desktop app only, display mods (OpenSpec cockpit pane, message cards, session band,
background-tasks pane), listed in this marketplace and maintained in
https://github.com/ghislain95/claude-mods:

```
/plugin install openspec-cockpit@claude-toolbox
/plugin install conversation-cards@claude-toolbox
/plugin install session-hud@claude-toolbox
/plugin install background-tasks@claude-toolbox
```

If you install them, tick the `cockpit` option when `sdd-init` asks: it adds to `CLAUDE.md` the
display contract the cards and the cockpit read.

Restart the session: `/sdd-core:sdd-init` should show up in the list of commands.

---

## 3. Installing the workflow in a project

Open Claude Code **at the root of the repository** (clean git tree preferably), then:

```
/sdd-core:sdd-init
```

### What happens

| Phase | What Claude does | What you do |
|---|---|---|
| 0. Pre-flight | Checks the tools, creates the `chore/sdd-init` branch, spots files that already exist | Confirm `superpowers` is installed |
| 1. Reverse-documentation | One sub-agent per module reads the code: stack, CI commands, real architecture, conventions, vocabulary. Runs the tests (baseline). Writes `docs/ARCHITECTURE.md`, the module docs, the glossary, reverse-documented ADRs, the roadmap | **Gate 1**: read the summary (observed rules, points to confirm) and correct it |
| 2. Choices | A single round of questions | Git autonomy level, language, options, agent model |
| 3. Rules | `openspec init`, `CLAUDE.md`, `AGENTS.md`, agents (one dev per module), `openspec/config.yaml`, process docs | — |
| 4. Guardrails | Git hook + its config, `.claude/settings.json`, CI workflows, `.gitignore` | — |
| 5. Checks | No template marker left, `openspec validate --all`, hook tests, review of the setup by the new `code-reviewer` agent | — |
| 6. Delivery | Two commits (`docs(sdd-init)`, `chore(sdd-init)`), PR depending on the autonomy level, final report | Read the report, create your `.claude/settings.local.json` |

### Git autonomy levels

| Level | The agent… | For whom |
|---|---|---|
| `autonomy-commit` | commits on the change branch; you push and open the PR | getting started, repo without GitHub |
| `autonomy-pr` | commits, pushes, opens the PR; **a human merges** | teams (recommended to start with) |
| `autonomy-merge` | also merges, but only with green CI and a review with no BLOCKER/MAJOR | experienced solo developer |

The level is enforced mechanically by `.claude/hooks/block-git-writes.conf` (`ALLOW_PUSH`,
`ALLOW_PR_MERGE`) — you can change it at any time by editing that file.

### After the setup

- Create `.claude/settings.local.json` (gitignored) from `.claude/settings.local.example.json` if
  `gh` needs a token dedicated to the repo. **Never commit this file.**
- Re-read the "Non-negotiable rules" section of `CLAUDE.md`: each rule cites its evidence; remove the
  ones that don't suit you.
- With the `graphify` option: each developer runs `graphify hook install` once in the project (local
  git hooks that keep the graph fresh after each commit or checkout; `.git/hooks/` is not shared).
- After a few sessions, run `/fewer-permission-prompts`: it reads your real usage and adds the
  safe, frequent commands to the project's allowlist (`sdd-init` already put a curated one and the
  module checks in `.claude/settings.json`).
- Run `/opsx:onboard` for a first guided cycle on real code.

---

## 4. Day to day

### A feature

```
/opsx:new <change-id>     framing: product-owner writes proposal.md (intent, scope, non-goals)
                           → structural change (new contract, migration, cross-cutting choice):
                             the architect tries to break the proposal before going on
/opsx:ff                  architect: spec deltas + design.md + tasks.md
/opsx:apply               the dev agents carry out the tasks, tests included
                           → code-reviewer reads the uncommitted diff (mandatory)
/opsx:verify              does the implementation match the specs?
                           → commit feat(<id>) on the feat/<id> branch
/opsx:archive             the deltas are merged into openspec/specs/
                           → post-archive: roadmap, doc impact, spec Purpose, graph
                           → commit chore(<id>), PR
```

You can just say "I want to be able to export invoices as CSV": the session routes to
`product-owner` and starts the cycle. It always announces the chosen agent ("Routing → `architect`
because…").

### A bug

`<module>-dev` reproduces it and finds the root cause → `tester` writes the failing test → fix →
`code-reviewer`. Trivial bug (< 30 min, specified behaviour intact): no OpenSpec change, but a
`fix/<scope>-<desc>` branch and a PR like everything else.

### Session hygiene

| Situation | Tool |
|---|---|
| Long session, change of topic, polluted context | `/handoff:passation [next goal]`, then `/clear` — preferred over `/compact` |
| Fuzzy or disputed domain term | the `domain-modeling` skill updates `docs/GLOSSARY.md` |
| Every ~5 changes, never in the middle of one | `/sdd-core:improve-codebase-architecture` |
| Failed session, painful post-archive | `/sdd-core:retro` (improves the agent's environment, not the code) |
| UI review (with `sdd-ui`) | `/sdd-ui:web-design-guidelines <files>`, `sdd-ui:break-ui` |

---

## 5. The git guardrail

The `PreToolUse` hook reads every Bash command from the agent (sub-agents included) the way the
shell reads it, and blocks in particular:

- commit / merge / revert / cherry-pick on a protected branch; any push of a protected branch;
  push without an explicit remote and branch; force-push;
- history rewriting (`rebase`, `commit --amend`, `reset` to a revision…);
- sweeping stages (`git add -A`, `git add .`, `commit -a`) — the agent stages explicit paths;
- anything that throws work away (`reset --hard`, `clean -f`, `checkout .`, `stash drop`, `branch -D`);
- `--no-verify`; `gh pr merge` other than `--merge` (and depending on `ALLOW_PR_MERGE`).

Known false positives: a `$(…)` that really runs a forbidden git command, even inside a commit
message → use `git commit -F <file>`; `mkdir x && cd x && git commit` → two calls.

Tests: `bash .claude/hooks/block-git-writes.test.sh` (also run in CI by `tooling.yml`).
It is a guard against mistakes, not a sandbox.

---

## 6. Updating

**The plugin.** With auto-update on (§2.3), Claude Code checks the marketplace in the background
during a session and tells you when a new version is installed (`/reload-plugins` or a restart
applies it). Without auto-update, by hand:

```
/plugin marketplace update claude-toolbox
/plugin update sdd-core@claude-toolbox
```

When you open a session in a project set up with an older kit, `sdd-core` shows a one-line notice:
that is the cue for the project update below.

A new version only reaches you when its `version` number changes: see [`CHANGELOG.md`](CHANGELOG.md).

**Each project.** A plugin update does not touch the files already generated in your projects. In each installed
project: `/sdd-core:sdd-init --refresh` (or the install prompt of the README again). It compares the generated files
with the new version of the templates, applies what comes from the kit, **keeps your local
changes**, and never touches the specs, the changes or the reverse-documentation.

---

## 7. Known pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| Every `git` command from the agent is blocked | `jq` missing | `brew install jq` |
| `sdd-core` shows "failed to load" in `/plugin` | its dependency `superpowers` is missing (official marketplace not added) | `/plugin marketplace add anthropics/claude-plugins-official`, then `/plugin install superpowers@claude-plugins-official` |
| `/opsx:ff` or `/opsx:verify` unknown | minimal OpenSpec profile | §2.2, then `openspec update` in the project |
| The agent answers about code that no longer exists | stale graphify graph | `graphify update .` (`--force` after deleting or renaming files) |
| An agent makes up a rule | rule missing from the reverse-documentation | fix `CLAUDE.md` or the module's `CODING_RULES.md`: those are what the agents read |
| Skills fire out of context | too many skills installed | uninstall what you don't use (`/plugin`): every description enters every session |
| Two sessions on the same checkout mix their files | shared working tree | one session per worktree, or name the paths to commit explicitly |
