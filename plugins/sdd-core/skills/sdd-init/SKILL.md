---
name: sdd-init
description: Installs the SDD workflow (OpenSpec + specialised agents + mandatory review + git guardrails + CI) in the current project, whatever the language — first reverse-documents the actual code, then generates CLAUDE.md, agents, OpenSpec rules, hook and CI from what was observed. Also `--refresh` to resync an installed project with a newer version of the kit.
argument-hint: "[--refresh]"
disable-model-invocation: true
---

# sdd-init — install the SDD workflow in a project

You install, in the current repository, the workflow described in the kit's `GUIDE.md`: spec-driven
development with OpenSpec, specialised sub-agents, mandatory review before verify, post-archive,
a mechanical git guardrail and CI. The process is **the same from one project to the next**; the
rules, however, **come out of the project's own code** — never from another project, never from a
guess.

This folder (the "base directory" given when the skill is invoked) contains:
- `templates/` — templates to fill in; the convention is in [`templates/VARIABLES.md`](templates/VARIABLES.md) (read it first);
- `references/recon.md` — the reverse-documentation checklist;
- `references/adoption.md` — projects that already have a `CLAUDE.md`, agents or OpenSpec, and the `--refresh` mode.

`$ARGUMENTS` contains `--refresh` → go straight to `references/adoption.md` §3.

## Principles (hold them for the whole install)

1. **Facts are your job.** Never ask the user what the code, the CI, the dependency files or the git
   history can tell you. You only ask for **choices**.
2. **Observed ≠ wished for.** A "non-negotiable" rule only goes into `CLAUDE.md` if it is verified in
   the code (cite `file:line`) **or** decided by the user. Everything else goes under "to confirm" in
   the final report.
3. **A mechanical rule becomes a check**, not an instruction: if a rule can be verified by a linter,
   an architecture test or CI, propose that check (a backlog line in `docs/ROADMAP.md`) instead of
   only writing prose.
4. **Nothing is overwritten without being read.** An existing target file → `references/adoption.md`.
5. **Few, but right.** An agent, skill or section that doesn't serve this project is not generated
   (e.g. no `devops` agent without Docker or CI; no `full-stack-dev` with a single module).
6. **Verify before concluding**: every check command written into a file has been run at least once
   during the install, and its result is in the report.

## Phase 0 — Pre-flight

1. `git rev-parse --show-toplevel` (not a git repository → offer `git init`, otherwise stop),
   `git status --short` (dirty tree → ask whether to go on: the install is committed separately),
   `git branch --show-current`, default branch (`git symbolic-ref refs/remotes/origin/HEAD` or, failing
   that, the local `main`/`master`), remote (`git remote -v` → GitHub remote? → option `github`; GitHub
   remote or `.github/workflows/` present → option `ci`). Today's date: `date +%F` (→ `{{INSTALL_DATE}}`).
2. Create the working branch **before any write**: `git switch -c chore/sdd-init`.
3. Tools — check them, and for each missing one give the install command (don't install it without
   the user's go-ahead):

   | Tool | Check | Install | Required |
   |---|---|---|---|
   | Node ≥ 20 + npm | `node -v` | nodejs.org / `brew install node` | yes (OpenSpec) |
   | OpenSpec CLI | `openspec --version` | `npm install -g @fission-ai/openspec@latest` | yes |
   | jq | `jq --version` | `brew install jq` / `apt install jq` | yes (without jq, the hook blocks every `git`/`gh`) |
   | perl | `perl -v` | ships with macOS/Linux | yes (the hook's shell reader) |
   | gh | `gh auth status` | `brew install gh` | with option `github` |
   | uv + graphify | `graphify --version` | `uv tool install "graphifyy[sql]"` | with option `graphify` |

4. Companion plugins: ask the user to run `/plugin` and confirm that `superpowers` and `handoff` are
   installed (the workflow relies on `systematic-debugging`, `verification-before-completion`,
   `test-driven-development`, and the generated rules call `/handoff:passation`). If one is missing:
   `/plugin install superpowers@claude-plugins-official`, `/plugin install handoff@claude-toolbox`.
5. Files that already exist (`CLAUDE.md`, `AGENTS.md`, `.claude/agents/`, `.claude/settings.json`,
   `openspec/`, `docs/`) → note them: they go through `references/adoption.md`.

## Phase 1 — Reverse-documentation (code first)

Follow [`references/recon.md`](references/recon.md). Summary:

1. **Module map**: list the modules (VARIABLES.md §4), their stack and pinned versions, their build /
   test / lint commands **as CI runs them** (or, without CI, as the project's scripts define them).
2. **Parallel recon**: one `Explore` sub-agent ("very thorough") per module, plus one for
   cross-cutting concerns (CI, infra, existing docs, git history) — small project (single module, a
   few thousand lines): do the recon yourself, it is faster. Each returns a report structured
   according to `recon.md` §3, every claim sourced `file:line`. You aggregate.
3. **Baseline**: run each module's check commands. Red → record it as is ("the baseline is red: N
   failing tests"); **fix nothing** during the install.
4. Write the reverse-documentation from the templates:
   - `docs/ARCHITECTURE.md` (`templates/docs/ARCHITECTURE.md`)
   - per module: `<module>/docs/CODING_RULES.md`, `MODULES.md`, `TESTING_STRATEGY.md`
     (`templates/module-docs/`) — single-module repo: straight into `docs/`
   - `docs/GLOSSARY.md`: seeded from the domain names (entities, aggregates, states, roles) found in
     the code — short definitions, marked "to confirm" when inferred
   - `docs/adr/ADR-001-…`: one ADR per **structural decision already taken** and visible in the code
     (choice of framework, database, auth, architecture style), status `Accepted (reverse-documented)`
   - `docs/ROADMAP.md`: goal taken from the README and existing docs (otherwise a "to confirm" line,
     without asking an extra question) + the backlog section fed by what the recon found (notable
     TODO/FIXME, debt, mechanical checks to add)
5. **Validation gate 1** — show the user a short summary: modules, stack, commands and their status,
   5 to 10 observed architecture rules (with evidence), assumed domain risks, points "to confirm".
   They correct it; you only move on to phase 2 once they agree.
6. **Options deduced, not asked**: `multi-module` (≥ 2 modules), `devops` (Docker, IaC or deployment
   scripts — CI alone is not enough), `migrations` (VARIABLES §3), `github`, `ci`, `lean` (single
   module and < ~5,000 lines of code: `wc -l` on source files, tests and dependencies excluded).
   Announce them at gate 1; the user can challenge them.

## Phase 2 — Choices (a single round of questions)

Ask **in one go** (question tool, ≤ 4 questions, each option explained, your recommendation first)
the choices the code cannot settle:

1. **Git autonomy level** — `autonomy-merge` (the agent commits, pushes, opens and merges the PR with
   green CI + a review with no BLOCKER/MAJOR) · `autonomy-pr` (a human merges) · `autonomy-commit`
   (the agent doesn't push). Recommend `autonomy-pr` for a team discovering the workflow,
   `autonomy-merge` for an experienced solo developer. Without a GitHub remote: `autonomy-commit`.
2. **Language** of the docs and replies (English, French, or another one). The templates are written
   in English: with another language, translate the prose as you fill them. Code, commits and
   OpenSpec artifacts stay in English unless explicitly chosen otherwise.
3. **Options** (multi-select): `graphify` (map of the code; offered ticked above ~20k lines, unticked
   below — a small project is faster to read than to query), `graphify-hooks` (only meaningful with
   `graphify`, offered ticked with it: `graphify hook install` puts local git hooks — post-commit,
   post-checkout — that rebuild the graph incrementally; per developer, nothing committed), `ui` (offered ticked if the project has
   a web interface: `sdd-ui` plugin), `work-style` (offered ticked: the kit's way of working in
   `CLAUDE.md` §12 — short framing with examples, autonomy all the way once framing is agreed,
   structured final report, handoff), `caveman` / `cockpit` (display preferences installed at user
   level; `cockpit` = the desktop mods `openspec-cockpit` + `conversation-cards` from the claude-toolbox
   marketplace are installed — offered ticked if `claude plugin list` shows them).
4. **Agent model** (`opus` recommended: the quality of the review and of the adversarial pass depends
   on it; `inherit` to follow the session's model).

`{{DOMAIN_RISKS}}`: propose a wording deduced from the recon and have it validated in the same round
(an "other" option to correct it).

## Phase 3 — Rules, agents, OpenSpec

1. **OpenSpec**:
   - `openspec init --tools claude` (non-interactive). It generates `openspec/` and the `/opsx:*`
     commands + `openspec-*` skills in `.claude/`.
   - The workflow uses the extended set (`new`, `ff`, `continue`, `apply`, `verify`, `sync`,
     `archive`, `bulk-archive`, `explore`, `onboard`, `propose`). `openspec config list`: if any are
     missing, ask the user to run `openspec config profile` in their terminal (interactive), then
     run `openspec update`.
   - Note `openspec --version` (→ `{{OPENSPEC_VERSION}}`, pinned in CI).
   - Replace `openspec/config.yaml` with `templates/openspec/config.yaml` filled in. `context` = a
     **short** summary (≤ 25 lines: pitch, stack, 5 to 8 critical architecture rules, risks,
     languages) that points to the docs for details — it is injected into every artifact, every line
     costs. In English. `rules` kept, `# sdd:if` blocks resolved.
   - **No massive reverse-spec.** Specs are born with changes. In the final report, propose 1 to 3
     `baseline-<domain>` changes for the most critical domains: `ADDED` spec deltas describing the
     **existing** behaviour, tasks = characterisation tests that pin it. It is the only clean way to
     reverse-spec (specs are never edited by hand). For each, give the ready-to-run command
     (`/opsx:new baseline-<domain>`) and the 3 to 5 behaviours it will pin.
2. **Root files**: `CLAUDE.md` and `AGENTS.md` from `templates/root/` (option `lean`:
   `AGENTS.lean.md`, written under the name `AGENTS.md`).
3. **Process docs**: `docs/CONTRIBUTING.md`, `docs/OPENSPEC_GUIDE.md`, `docs/AGENT_TOOLBOX.md`
   (except with option `lean`), and `docs/GRAPHIFY.md` with option `graphify`, from `templates/docs/`.
4. **Agents** (`templates/agents/` → `.claude/agents/`):
   - always: `product-owner`, `architect`, `code-reviewer`, `tester`, `doc-writer`, `README.md`;
   - `devops` with option `devops` (Docker, IaC, deployment; CI alone doesn't justify it);
   - `module-dev.md` instantiated **once per module** → `.claude/agents/<module>-dev.md`, filled with
     **that module's** stack, rules and commands;
   - `full-stack-dev` only with `multi-module` and when one module consumes the other (API + client).
   - `{{AGENT_MODEL}}` written verbatim in every frontmatter.
5. **Filling** — for each file: variables, `sdd:fill` (content taken from the reverse-documentation,
   never generic: "follow best practices" is forbidden — name the rule and its evidence),
   `sdd:if`/`sdd:endif` resolved (a marker alone on its line goes with its line), `sdd:each`
   expanded, `sdd:note` removed, paths normalised (VARIABLES §4). Translate the prose if the docs are
   not in English. Reverse-documented ADRs follow `templates/docs/adr/ADR-000-template.md`.
6. **Marker**: the last line of `CLAUDE.md` = the install marker (`references/adoption.md` §2) — it is
   what `/sdd-core:sdd-init --refresh` relies on.

## Phase 4 — Guardrails

1. **Git hook**: copy `templates/claude/hooks/block-git-writes.{sh,pl,test.sh,conf}` into
   `.claude/hooks/` (`chmod +x` the `.sh` files), fill in the `.conf` (protected branch, autonomy
   level). `templates/claude/settings.json` → `.claude/settings.json`: the `PreToolUse` hook plus a
   curated `permissions.allow` of safe commands (read-only git, `openspec`, `gh run`/`gh pr`
   read-and-create, graphify queries, the hook test suite). **Add the module checks**: one
   `Bash(<command>)` entry per command of `{{CHECK_COMMANDS}}` / each `{{MODULE_CHECK}}`, written
   exactly as run (plus a `Bash(<command> *)` form when the command takes arguments, e.g. a test
   filter) — without them, every check run asks for permission and "all the way" autonomy stalls.
   Existing `settings.json` → merge: union of the `allow` lists and of the hooks, nothing removed or
   reordered. Run `bash .claude/hooks/block-git-writes.test.sh` → it must end
   with `ALL n CASES OK`.
   ⚠️ From then on the hook is active for you too: `git add` with explicit paths, never on the
   protected branch, long messages through `git commit -F <file>`.
2. **CI** (option `ci`): `templates/github/workflows/{openspec,tooling}.yml` → `.github/workflows/`;
   `checks.yml` → one `checks-<module>.yml` per module; `migrations.yml` with option `migrations` (no
   already-merged migration modified, deleted or renamed). CI already present → only add
   `openspec.yml`, `tooling.yml` (and `migrations.yml`), and check that the existing CI runs the same
   commands as `{{CHECK_COMMANDS}}` (otherwise, report the gap).
3. **Misc files**: `templates/misc/gitignore-additions` → appended to `.gitignore` (no duplicates);
   `templates/misc/worktreeinclude` → `.worktreeinclude`. Option `graphify`:
   `templates/misc/graphifyignore` → `.graphifyignore`, then `graphify update .` and
   `graphify check-update .`; if the `graphify` skill is not in your list of skills, ask the user to
   run `graphify install --platform claude` and then restart the session. Option `graphify-hooks`:
   `graphify hook install`, then `graphify hook status` (both hooks `installed`).
4. `templates/claude/settings.local.example.json` → `.claude/settings.local.example.json` (committed,
   it holds no secret: it documents the token's exact permissions). **Never create
   `settings.local.json` yourself**: in the report, tell each developer to copy the example and put
   their own token in it.
5. Option `ui`: `templates/claude/launch.json` → `.claude/launch.json`, one configuration per UI
   module, filled from the recon (the module's dev-server script: `runtimeExecutable`,
   `runtimeArgs`, `port`). It lets Claude's preview tools start and check the UI. Keep `autoPort:
   true` unless a backend's CORS configuration expects a fixed port (then a fixed port, and say why
   in the report).

## Phase 5 — Checks

Everything must pass; otherwise fix it before delivering:

```bash
grep -rnE '(^|[^$])\{\{[A-Z_]+\}\}|sdd:(fill|if|endif|each|endeach|note)' CLAUDE.md AGENTS.md .claude/agents .claude/hooks .claude/settings.json docs openspec/config.yaml .github .gitignore .worktreeinclude .graphifyignore 2>/dev/null   # empty
openspec validate --all
bash .claude/hooks/block-git-writes.test.sh                      # ALL n CASES OK, whatever the autonomy level
python3 -c "import json; json.load(open('.claude/settings.json'))"
# YAML: the first tool available
for f in openspec/config.yaml .github/workflows/*.yml; do ruby -ryaml -e "YAML.load_file('$f')" 2>/dev/null || python3 -c "import yaml,sys; yaml.safe_load(open('$f'))" || echo "YAML KO: $f"; done
```

plus: every command cited in the "Before finishing" section of `CLAUDE.md` run at least once; every
relative link in the generated files points to an existing file (check them one by one, especially
with `MODULE_PATH=.`); no mention of a stack, tool or domain the project doesn't have.

Then dispatch `code-reviewer` (the project's new agent) on the install diff: its mission = consistency
of the generated rules with the actual code (an unproven rule = 🔴 MAJOR). Fix BLOCKER/MAJOR findings.

## Phase 6 — Delivery

1. Two commits on `chore/sdd-init`, explicit paths:
   - `docs(sdd-init): reverse-document architecture, modules and conventions` (phase 1);
   - `chore(sdd-init): install spec-driven workflow, agents and git guardrails` (phases 3-4).
   Body: what was observed vs decided, test baseline.
2. Depending on autonomy: `autonomy-commit` → stop there; otherwise `git push -u origin chore/sdd-init`
   and `gh pr create`; `autonomy-merge` → merge only with green CI (the hook enforces `--merge`).
3. **Final report** (structured):
   - **Done**: generated files, by phase.
   - **Decisions**: phase 2 choices.
   - **Observed vs to confirm**: proven rules (count); list of "to confirm" items.
   - **Baseline**: check commands and their result, with numbers.
   - **Expected from you**: create `.claude/settings.local.json` (gh token), re-read §5 of
     `CLAUDE.md`, install the optional plugins chosen.
   - **Next step**: `/opsx:onboard` for a first guided cycle, or the first `baseline-<domain>`
     proposed, or `/opsx:new <id>` on the first ticket of `docs/ROADMAP.md`.
