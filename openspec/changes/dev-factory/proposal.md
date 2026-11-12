# Proposal — dev-factory

## Why

The owner wants the agent to carry a change from an approved proposal all the way to production without
losing quality, and wants every future project to start with that workflow already in place. Today the
pieces are scattered and inconsistent: `claude-sdd-kit` packages a spec-driven workflow with a git
autonomy level set **once per project**, `claude-mods` holds the desktop mods in a second repository,
and the two real projects (geomni, wifisense) run hand-maintained copies that have drifted from the kit
and from each other (two guardrails with contradictory rules, one-PR versus two-PR delivery, merge
allowed in one project and forbidden in the other). Autonomy cannot be granted safely per project: what
decides whether a human must look is the change itself — whether it alters what the user sees and does,
and whether its effect in production can be undone.

## What Changes

### One catalog, `claude-toolbox`

- `claude-sdd-kit` is renamed `claude-toolbox` (repository and marketplace `name`, history kept) and
  becomes the single home of every Claude tool: workflow plugins, standalone skills, desktop mods.
  `claude-mods` is folded into it and archived.
- One plugin per usage: anything usable outside the spec-driven workflow is its own plugin (first one:
  `handoff`, the former `sdd-core:passation`); workflow plugins declare dependencies on them.
- Compatibility for one version: the `.claude/passation/` folder the mods parse is kept, the version
  check accepts the old `sdd-kit: installed` marker and the new one, and the rename procedure is
  rehearsed on a scratch configuration before publishing.
- **BREAKING**: the marketplace name changes from `sdd-kit` to `claude-toolbox`; existing installs
  (including the owner's `local-mods`) must re-add the catalog.
- The toolbox's own `main` is production for its users (auto-update): it declares its own irreversible
  triggers (guardrail and hook templates, `sdd-init`, `marketplace.json`, the version-check hook).

### Deployment profile, per project

A generated, per-project file states what merging deploys and how (geomni: `deploy-backend.yml` to Cloud
Run, Vercel for the front), the platform rollback commands (previous Cloud Run revision, previous Vercel
deployment), the post-deploy probes, and the scheduled jobs that run merged code later. Classification
and delivery both read it.

### Risk classification per change

Every proposal carries a classification, proposed by the agent with its evidence and approved by the
owner with the proposal. It opens zero, one or two human gates:

- **Intent gate** — the change visibly alters a business gesture, a screen or the feel of the product
  (front-end or not: scoring, colour ramps, taxonomy and classifier change what the map shows). The
  owner runs a short QA (3 to 6 points, before/after captures) prepared after the agent's own QA, one
  QA per change, before merge.
- **Irreversible gate** — the owner gives a merge go, without QA. A change is *revertible* only if it is
  code only: no schema change, no change to a stored format (database, cache, browser storage,
  published edition), no rollout step after merge, no cost or quota consumption. Everything else opens
  this gate. geomni's trigger list (first version, evolving): any Flyway migration; any stored-format
  change; publication of a territorial edition; ETL replay; infrastructure (bucket, secret, CORS,
  scheduler); removal or reshaping of a consumed public endpoint; anything that consumes paid quota or
  database capacity. A migration is fixed forward, never reverted.
- **Gate machinery is always gated**: a change to the triggers, the approved classification, the hooks,
  the agent settings or the CI workflows opens the irreversible gate.
- Technical risk opens no gate: it raises review depth, measured thresholds written in the proposal and
  post-deploy checks.
- **Mechanical check, both gates, asymmetric**: path- and content-based triggers for both gates are read
  from the base branch, never from the pull request. A diff that hits a trigger opens its gate unless
  the approved classification explicitly waived it; a hit the classification did not account for blocks
  the merge.

### Autonomous delivery

- With no gate open, the change merges when a single always-running aggregate CI job is green, the
  review harness reports no BLOCKER or MAJOR, `/opsx:verify` passes and the mechanical check agrees.
  These conditions are one `merge-conditions` CI check, read from `main`.
- Merge method per project (geomni: squash).
- **Serialisation**: at most one change between merge and verified production at a time; the next
  merge waits.
- Two pull requests: PR 1 (the change), post-deploy verification, PR 2 (archive and post-archive), so
  `openspec/specs/` only receives behaviour verified in production.
- **Verification window**: it includes the next run of any scheduled job that executes the changed
  code; otherwise those code paths are an irreversible trigger.
- **Rollback** on failed verification: platform rollback first (deployment profile), then a git revert
  merged under the same server-side conditions, an alert to the owner with a diagnosis, and a fix
  change.
- The agent merges only through the guardrail's verified route; a gated pull request is merged by the
  owner, whose click is the go or the passed QA. Every deploy target refuses a commit that did not come
  from a merged pull request with `merge-conditions` green (deploy guard).
- The owner receives a final report: what shipped, what the harness found and fixed, what to look at
  in production.

### Review harness, default for every project

- One reviewer skill per angle: spec conformance, project conventions and architecture, bug hunting,
  tests (scenario coverage and mutation), security, performance, interface, sourced claims.
- Each opinion is backed by a mechanical check where one exists: executable architecture rules, lint,
  measurements, mutation testing scoped to the changed classes. Where the tooling is absent (geomni has
  no PIT or Stryker yet), the angle says so instead of pretending.
- Each finding is adversarially verified before it is fixed.
- The fix loop stops at zero BLOCKER/MAJOR or after three rounds, then escalates to the owner.
- Depth follows technical risk, within an explicit time and token budget. Sequential agents, one heavy
  build at a time, normal or high effort; never an ultracode-scale fan-out.
- The adversarial pass on the proposal becomes systematic, scaled to the change.

### One git guardrail

The kit ships one guardrail that filters commands only: the kit's perl reader (197 cases) extended with
geomni's cases (REST merge endpoint, branch tracking `main`), with merge method and
`--force-with-lease` as per-project settings, and one merge route allowed only after it has queried
GitHub for `merge-conditions`. It is a guard against mistakes, not a security boundary; the server-side
barrier is the deploy guard.

### Projects consume the kit

geomni migrates first (pilot), then wifisense, through `sdd-init` in **adoption mode** with an explicit
file-by-file mapping (their rules live in other files and languages than the templates). The marker
records the template version so later refreshes can do a three-way merge.

### Local QA environment

The owner's intent QA runs locally, before merge (a Vercel preview cannot work for geomni: the preview
front talks to the production backend, and the edition bucket's CORS only allows production origins).
Several projects and agents run in parallel on the same machine, so the agent prepares the QA
environment without disturbing them:

- It inventories what already runs — containers, listening ports, dev servers, which project and
  worktree each belongs to — and never stops or restarts anything it did not start itself.
- It reuses what is compatible (the project's shared Docker services, an already running backend of the
  same project) and starts only what is missing, on free ports.
- It hands the owner a QA brief: the link to open, then for each point the gesture to make and the
  expected result, with before/after captures from its own QA.
- After the QA it stops only what it started.

## Owner decisions (2026-11-12)

1. **Server-side enforcement** — geomni is a private repository on GitHub Free (no rulesets, no branch
   protection, no auto-merge), and the agent acts with the owner's token: any token able to push a
   change branch can also write `main`, and the owner's approvals cannot be told apart from the
   agent's. Without GitHub Pro, merge protection is **client-side and guards against mistakes**: a
   `merge-conditions` check read from `main`, a guardrail that queries it before allowing the agent's
   merge, gated pull requests merged by the owner's own click. The **server-side barrier is a deploy
   guard**: no deploy target ships a commit that did not come from a merged pull request with
   `merge-conditions` green. GitHub Pro with a GitHub App identity for the agent becomes a backlog line.
2. **Migrations and rollback** — any migration and any stored-format change opens the irreversible gate.
3. **Intent QA** — locally, before merge (above). A per-PR backend for phone QA becomes a backlog line.

## Capabilities

### New Capabilities

- `toolbox-catalog`: catalog name, plugin-per-usage rule, categories, dependencies, versioning and update
  notice, desktop mods as plugins, the toolbox's own release triggers.
- `deployment-profile`: per-project description of what deploys on merge, rollback commands, probes,
  scheduled jobs.
- `change-risk-classification`: classification in the proposal, intent and irreversible gates, the
  revertible definition, per-project triggers, gate-machinery rule, the mechanical check.
- `autonomous-delivery`: merge conditions and their server-side enforcement, merge serialisation, the
  two-PR delivery, verification window, rollback and alert, final report.
- `local-qa-environment`: inventory of running services across projects, reuse versus start on free
  ports, never stopping what the agent did not start, the owner QA brief (link, gestures, expected
  results, captures), cleanup.
- `review-harness`: reviewer angles, mechanical backing, adversarial verification, bounded fix loop,
  depth and budget.
- `git-guardrail`: command filtering only, per-project settings, test suite.
- `project-setup`: `sdd-init`, adoption mode, `--refresh` with recorded template version.

### Modified Capabilities

None — the toolbox has no specs yet.

## Non-goals

- No change to geomni's or wifisense's product behaviour; only their agent environment and CI change.
- No submission to Anthropic's plugin directory.
- No owner QA on technical changes: technical risk is answered by automation, never by a gate.
- No grouped QA across several changes.
- No ultracode-scale orchestration as a requirement of the workflow.

## Delivery in lots

1. Restructure — rename, fold `claude-mods` in, extract `handoff` with compatibility, OpenSpec and the
   toolbox's own release triggers. No behaviour change for projects.
2. Review harness — so that lot 3's merge condition exists when lot 3 ships.
3. Deployment profile, classification, gates, mechanical check, server-side merge, serialisation,
   rollback, report.
4. Migration — geomni (pilot, adoption mode), then wifisense.

Until lot 3 is in place, merges stay with the owner.

## Impact

- GitHub: `ghislain95/claude-sdd-kit` renamed (redirect kept), `ghislain95/claude-mods` archived —
  outward-facing, done with the owner's confirmation.
- Users of the public `sdd-kit` marketplace must re-add it under its new name.
- geomni: `.claude/` (agents, hook, settings), `CLAUDE.md` §1, `AGENTS.md` git section, CI (aggregate
  gate job, `merge-conditions` check, deploy guard in `deploy-backend.yml` and Vercel's ignored build
  step), the Python guardrail and its CI job replaced; merging deploys without the owner when no gate
  is open.
- wifisense: same, second; its merge method and guardrail settings move to per-project configuration.
