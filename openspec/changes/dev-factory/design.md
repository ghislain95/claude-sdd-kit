# Design — dev-factory

## Context

See `proposal.md` for the why and the owner decisions. Constraints that shape the approach:

- **GitHub Free, private projects.** geomni (and wifisense) have no rulesets, no branch protection, no
  auto-merge; the agent acts with the owner's token. Merge protection is therefore client-side; the
  server-side barrier is the deploy pipeline (proposal, decision 1). The toolbox itself is public, so
  rulesets are available to it for free.
- **Existing assets.** The kit (`sdd-core` 0.2.0) already has `sdd-init` with an adoption mode and a
  `--refresh` (`references/adoption.md`), the perl guardrail (`block-git-writes.{sh,pl,test.sh,conf}`,
  197 cases) and a version-check session hook. The mods (`claude-mods`) are function-hook plugins with a
  `shared/` folder synced into each mod by `scripts/sync-shared.sh`, already listed in the kit's catalog
  through `git-subdir` sources.
- **geomni specifics.** Squash-only merges; `deploy-backend.yml` deploys on push to `main` filtered on
  `backend/**`; Vercel deploys the front on every push; a daily ETL scheduler runs repository code;
  path-filtered CI workflows; a Python guardrail (55 cases) with rules the kit lacks (REST merge
  endpoint, branch tracking `main`, `--force-with-lease`).
- **Owner's working mode.** Sequential agents, one heavy build at a time, normal or high effort.

## Goals / Non-Goals

**Goals:**
- Every rule the specs state is either checked mechanically or explicitly documented as honour-based.
- One source per fact: triggers, deployment profile and harness settings live in one project folder
  read by the hook, the CI checks and the skills alike.
- The owner's interventions are clicks and short chat answers, never commands.

**Non-Goals:**
- Defending against an agent that deliberately circumvents the hook (out of reach without GitHub Pro).
- Rewriting the mods; they only move.
- Supporting forges other than GitHub.

## Decisions

### D1 — Catalog layout and the fold of claude-mods

```
claude-toolbox/
  .claude-plugin/marketplace.json     name "claude-toolbox", every entry with a category
  plugins/sdd-core/                   workflow (sdd-init, review harness skills, templates)
  plugins/sdd-ui/                     optional UI skills
  plugins/handoff/                    skills/passation (former sdd-core:passation)
  plugins/local-qa/                   QA environment skill (usable outside SDD)
  mods/<mod>/ , mods/shared/, mods/scripts/   the four mods, unchanged inside
  openspec/                           the toolbox's own specs
```

`claude-mods` is imported with `git subtree add --prefix=mods` so its history is kept; catalog entries
switch from `git-subdir` to `./mods/<mod>`. **Why subtree:** keeps history without a tool the owner
lacks (`git filter-repo`) and leaves no submodule to fetch. Alternative rejected: submodule (Claude
Code fetches it, two repos to keep in sync — the very drift we remove).

`local-qa` is its own plugin because preparing a QA environment is useful outside the spec-driven
workflow (rule "one plugin per usage"); `sdd-core` depends on `handoff` and `local-qa`.

### D2 — Rename procedure

1. Rehearse on a scratch `CLAUDE_CONFIG_DIR`: add `sdd-kit` from a local clone, install, then switch
   to the renamed catalog and record what Claude Code does (re-add, plugin data kept or lost).
2. `gh repo rename claude-toolbox` (owner confirmation — outward-facing; GitHub keeps a redirect).
3. Marketplace `name` → `claude-toolbox`; README install prompt and every hard-coded
   `marketplaces/sdd-kit` path updated.
4. Install marker becomes `claude-toolbox: installed <version>`; `check-kit-version.sh` accepts both
   markers for one minor version.
5. `claude-mods` repository: README points to `claude-toolbox`, then archived (owner confirmation).
   The owner's `local-mods` directory marketplace is replaced by the local clone of `claude-toolbox`.

### D3 — The project's factory folder `.sdd/`

One versioned folder per project, read by the hook, the CI and the skills:

| File | Content |
|---|---|
| `.sdd/triggers.yaml` | intent and irreversible triggers (path globs, content regexes), plus the non-waivable gate-machinery list |
| `.sdd/deployment.yaml` | deploy targets (trigger, rollback command, probes), scheduled jobs (schedule, code paths) |
| `.sdd/harness.yaml` | angles per risk, mechanical tools available, budget (minutes, tokens), effort |
| `.claude/hooks/block-git-writes.conf` | guardrail settings (stays next to the hook it configures) |

The gate-machinery list always includes `.sdd/**`, `.claude/hooks/**`, `.claude/settings.json`,
`.github/**`, `.gitattributes`, `.gitmodules`, `openspec/config.yaml`, `vercel.json` and every
`classification.yaml` touched outside a framing pull request (amended after the lot 3a review, D5).
**Why one folder:** the adversarial pass showed rules scattered across CLAUDE.md, hook and CI drift
apart; a single folder is the one place the gate-machinery trigger has to protect.

### D4 — Classification storage and approval: the framing pull request

Each change gets `openspec/changes/<id>/classification.yaml` (gates, evidence, waived triggers with
reason). **Approval is the owner merging a framing pull request** that carries only the proposal and
its classification. That puts the approved classification on `main` before apply, which is where every
check reads it from, and makes the approval an act on GitHub rather than a chat message.

- Alternatives rejected: approval recorded in the change branch (the PR would certify itself —
  adversarial objection 2); a label or comment (indistinguishable from the agent, who uses the owner's
  token).
- The framing PR touches `openspec/` only: no deploy target picks it up (D7).
- Reclassification during apply: the agent opens a new framing PR amending `classification.yaml`; the
  change PR waits for it.

### D5 — The `merge-conditions` check

A workflow `merge-conditions.yml` triggered by `pull_request_target` (runs the definition on `main`, so
a PR cannot edit its own check) and by `workflow_run` of the project's CI workflows. It never executes
PR code: it fetches the head commit as data and computes the diff against `main`. It sets a commit
status `merge-conditions` on the head commit:

- **success** only when: every CI workflow the diff requires has a successful run on the head commit
  (aggregate gate — the required set is computed from the same path filters, so a PR outside every
  filter is still judged); commit statuses `review-harness` and `opsx-verify` are success on the head
  commit; the diff's trigger hits are all accounted for by the approved classification.
- its **description** lists the open gates: `gates: none`, `gates: intent`, `gates: irreversible`,
  `gates: intent+irreversible`.

`review-harness` and `opsx-verify` statuses are posted by the agent with `gh api` when those steps
pass. They are honour-based (the agent could post them falsely) but mechanical: forgetting them blocks
the merge. Stated as such in the contributing guide.

Amended after the lot 3a review:
- The verdict depends on `main` (triggers, classifications, workflow filters). A `push` to the default
  branch re-judges every open pull request into it, and the description carries the judged base
  (`base <short sha>`); the merge route (D6) refuses when that base is not the current default-branch
  head.
- The status is spoofable (a workflow the PR adds can overwrite it; so can the agent's token). It
  remains the input of the client-side merge rule — against mistakes — and the deploy guard (D7)
  recomputes the verdict instead of reading it.
- Built-in gate machinery covers everything that changes what CI or the check does: `.github/**`,
  `.sdd/**`, `.claude/hooks/**`, `.claude/settings.json`, `.gitattributes`, `.gitmodules`,
  `openspec/config.yaml`, `vercel.json`, and any `classification.yaml` added, modified or deleted
  outside a framing pull request — not only the ones already on `main`.
- A change pull request must touch its own change folder, and the folder and the branch name must
  agree; touching another change's folder is an error. A missing `.sdd/triggers.yaml` on `main` is an
  error, never "defaults only".

### D6 — The guardrail: one perl implementation, one verified merge route

The kit's perl reader is kept (most cases, per-project `.conf`, already in the kit's CI). Added:

- geomni's cases ported as tests: REST merge endpoint `PUT …/pulls/N/merge`, `gh pr merge --auto`,
  branch tracking a protected branch, `--force-with-lease` allowed when `ALLOW_FORCE_WITH_LEASE=1`.
- `MERGE_METHOD=squash|merge|rebase`; `ALLOW_PR_MERGE` and the three autonomy levels are removed (the
  change decides, not the project). **BREAKING** for wifisense's `.conf`, handled by its adoption.
- The single merge route: `gh pr merge <n> --<MERGE_METHOD>`. Before allowing it the hook queries
  GitHub for the PR's head SHA and the `merge-conditions` status of that SHA; it allows only `success`
  with `gates: none`, and blocks when the query fails (fail closed). It also blocks while another PR of
  the repository carries the `in-flight` label (D8).
- geomni's Python guardrail and its `pr.yml` job are removed by geomni's adoption.

Alternative rejected: keep the Python version — fewer cases, no `.conf`, not in the kit's CI.

### D7 — The deploy guard

A script shipped by the kit, `.sdd/bin/deploy-guard.sh <sha>`: finds the PR merged as `<sha>`
(`GET /repos/{o}/{r}/commits/{sha}/pulls`), requires it merged, then **recomputes the verdict itself**
inside the deploy pipeline — `merge_conditions.py match` with the merge commit's first parent as base
and the PR head as head, plus the aggregate CI condition on the PR head — instead of trusting the
`merge-conditions` status. Amended after the lot 3a review: a commit status can be overwritten by any
workflow the pull request adds (every writer is `github-actions[bot]`) and by the agent's own token,
so the status is an input of the client-side merge rule only, never of the server-side barrier. Any
gates pass (an owner-merged gated PR deploys); an `unaccounted` hit, a red or missing required CI run,
or a direct push without a PR exit non-zero.

- geomni `deploy-backend.yml`: first step of the job, plus `concurrency: deploy` so two deploys never
  overlap.
- Vercel: `ignoreCommand` in `vercel.json` runs the guard (exit 0 = skip) and also skips when the
  commit has no frontend change. It needs a read-only fine-grained token in Vercel's environment
  (owner action).
- A refused deploy alerts the owner: failed workflow notification for the backend; for Vercel, the
  skipped build plus a GitHub issue opened by a `push` workflow that runs the same guard.

### D8 — Serialisation and rollback

- After merging, the agent puts the `in-flight` label on the merged PR; the hook refuses any other
  merge while one exists. The label is removed when verification passes or rollback completes.
  Client-side, like the rest of the merge protection; the deploy `concurrency` group is the
  server-side half.
- Verification window: `.sdd/deployment.yaml` scheduled jobs whose code paths intersect the diff extend
  verification until their next run has succeeded.
- Rollback: run each affected target's `rollback` command from `.sdd/deployment.yaml` (geomni:
  `gcloud run services update-traffic … --to-revisions=<previous>=100`, Vercel: promote the previous
  production deployment), then `git revert` on a `revert/<id>` branch. The revert PR carries a
  classification `revert-of: <id>` with both gates closed, which the check accepts only if the diff is
  the exact inverse of the merged change; its harness is limited to that verification.

### D9 — Review harness as skills

`sdd-core/skills/review-<angle>` (eight skills) plus `review-harness`, the orchestrator the session
runs after apply:

- Bug hunting delegates to Claude Code's `/code-review` and security to `/security-review` instead of
  re-implementing them; the other angles are written for the kit.
- Angle selection from `.sdd/harness.yaml` and the diff; agents run **sequentially**; one combined
  adversarial verifier per round checks every BLOCKER/MAJOR (owner's light mode), not one agent per
  finding.
- Mechanical backing per angle is declared in `.sdd/harness.yaml` (e.g. geomni: ArchUnit, ESLint,
  build size; mutation: absent until PIT/Stryker are added — a backlog line, not part of this change).
- Report written to `openspec/changes/<id>/review.md` (rounds, findings, refutations, angles not run),
  then the `review-harness` status is posted.

### D10 — `local-qa` environment

- Inventory: `docker ps` with compose labels (`com.docker.compose.project`, working dir) and
  `lsof -iTCP -sTCP:LISTEN` with each process's cwd, mapped to project and worktree.
- Started services are recorded in `.claude/qa/started.json` of the worktree; cleanup stops exactly
  those.
- Reuse rule: same project and no pending migration → reuse; pending migration → an isolated database
  under a compose project named after the worktree.
- The QA brief is a message in the conversation (rendered as a QA card by `conversation-cards`): link,
  3–6 points of gesture and expected result, captures.

### D11 — `sdd-init`: new generated files, adoption table, three-way refresh

- Templates added: `.sdd/*.yaml`, `merge-conditions.yml`, `deploy-guard.sh`, the `in-flight` label,
  contributing guide section "what is enforced where".
- Adoption mode starts with a mapping table (existing file/section → kit file/section → keep / merge /
  replace), approved by the owner before any write.
- Marker records the version; `--refresh` fetches that version's templates from the toolbox's git tag
  `sdd-core-v<version>` as the merge base. No template copy is stored in projects.

## Risks / Trade-offs

- [Merge protection is client-side] → deploy guard server-side; contributing guide states the limit;
  GitHub Pro + App stays a backlog line.
- [`review-harness`/`opsx-verify` statuses are honour-based] → they prevent omission, not lies; the
  review report is in the PR for audit.
- [`pull_request_target` runs with write token] → the workflow never checks out PR code into a run
  path; it reads blobs with `git show`; reviewed under the gate-machinery trigger.
- [Framing PR adds a step] → it replaces the chat GO, it is one click, and it makes the approval
  checkable.
- [Vercel guard needs a token in Vercel] → read-only, scoped to the repository; owner creates it once.
- [Stricter irreversible gate means more owner merges on backend changes] → accepted by the owner
  (proposal decision 2); revisited with evidence later.
- [Rename breaks existing `sdd-kit` installs] → rehearsal, compatibility markers for one version,
  README notice.

## Migration Plan

Lots as in the proposal. Lot 1 also protects the toolbox's own `main` with a GitHub ruleset (free, the
repository is public) requiring the toolbox's `merge-conditions`. Until lot 3 ships, the owner merges
every PR. geomni's adoption (lot 4) lands as a `chore/sdd-init` PR the owner merges; the first real
geomni change after it is the pilot, followed end to end. wifisense follows once the pilot is verified.
Rollback of the whole change: geomni's previous `.claude/` and workflows are restored by reverting the
adoption PR; the toolbox keeps the `sdd-kit` compatibility markers.

## Open Questions

- Exact Vercel CLI command to promote the previous deployment from the agent's machine, to be settled
  when writing geomni's `.sdd/deployment.yaml`.
- Whether the `in-flight` label should also be checked by the deploy guard; decided after the pilot.
