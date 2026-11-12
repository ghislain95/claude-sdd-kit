# Tasks

Lot 1 = groups 1–3, lot 2 = group 4, lot 3 = groups 5–8, lot 4 = groups 9–10. One pull request per
lot; the owner merges every pull request until group 8 has shipped.

## 1. Fold claude-mods into the toolbox

- [x] 1.1 Import `claude-mods` with `git subtree add --prefix=mods` keeping its history — verify: the subtree merge's second parent carries the mods' commits (`git log <merge>^2`)
- [x] 1.2 Switch the four mod entries of `marketplace.json` from `git-subdir` to `./mods/<mod>`, add `category` to every entry, drop the nested `mods/.claude-plugin` catalog — verify: `claude plugin validate .` passes
- [x] 1.3 Make `mods/scripts/sync-shared.sh` and `dev-sync.sh` work from their new location — verify: running sync leaves `git status` clean on an unchanged tree, and each mod's `claude plugin test` gives the same result as in `claude-mods` (pre-existing failures: `"ui.notify" is not an event`, tracked separately)
- [x] 1.4 Install the four mods from the local clone in a scratch config dir — verify: `claude plugin list` shows them enabled

## 2. Extract handoff and local-qa as plugins

- [x] 2.1 Move `sdd-core/skills/passation` to `plugins/handoff/skills/passation`, with its own `plugin.json` (category `skill`); keep the output folder `.claude/passation/` — verify: `handoff` installs alone in a scratch config and lists the `passation` skill; the skill still writes into `.claude/passation/`, the folder the mods read
- [x] 2.2 `local-qa` plugin: not created empty here — a plugin with a placeholder skill would install a skill that does nothing; it is created with its implementation in 8.5
- [x] 2.3 Declare `handoff` as a dependency of `sdd-core` (`local-qa` added in 8.5); update every reference to `sdd-core:passation` in templates and docs — verify: installing `sdd-core` in a scratch config reports "+ 2 dependencies: superpowers, handoff"; `grep -r "sdd-core:passation"` outside the CHANGELOG is empty

## 3. Rename to claude-toolbox and protect its release

- [x] 3.1 Rehearse the rename on a scratch `CLAUDE_CONFIG_DIR` (install from `sdd-kit`, switch to `claude-toolbox`) and write down the observed behaviour in `MAINTAINING.md` — verify: the notes exist and the README upgrade notice follows them
- [x] 3.2 Marketplace `name` → `claude-toolbox`; README install prompt, GUIDE and every `marketplaces/sdd-kit` path updated; README opens on the catalog; `mods/README.md` installs from `claude-toolbox` — verify: `grep -rn "sdd-kit" --exclude=CHANGELOG.md --exclude=SOURCE.md` lists only the compatibility code and the upgrade notices
- [x] 3.3 Install marker `claude-toolbox: installed <version>`; `check-kit-version.sh` accepts both markers; its test covers both — verify: `bash plugins/sdd-core/hooks/check-kit-version.test.sh` passes (12 cases) and the new cases fail against the former hook
- [x] 3.4 Write the toolbox's own `.sdd/triggers.yaml` (guardrail and hook templates, `sdd-init`, `marketplace.json`, version-check hook = irreversible) and its contributing note — verify: file present and referenced from `MAINTAINING.md`
- [ ] 3.5 Owner-confirmed outward steps, done **before** the lot 1 pull request is merged (the merged README and the version-check message point to `ghislain95/claude-toolbox`): `gh repo rename claude-toolbox`; `claude-mods` README points to the toolbox, then archive it; ruleset on the toolbox's `main` requiring pull requests — verify: `gh repo view ghislain95/claude-toolbox` works and the old URL redirects
- [x] 3.6 Bump `sdd-core` to 0.3.0, CHANGELOG entry (BREAKING catalog name) — verify: `claude plugin validate .` passes and the version-check test passes

## 4. Review harness

- [ ] 4.1 Write `review-spec-conformance`, `review-conventions`, `review-tests`, `review-performance`, `review-interface`, `review-sourced-claims` skills (finding format: severity, file:line, failure scenario) — verify: each skill's description triggers on its angle in a dry run on a sample diff
- [ ] 4.2 Write `review-bugs` and `review-security` as thin wrappers over Claude Code's `/code-review` and `/security-review` — verify: run on a sample diff with a planted bug, the bug is reported
- [ ] 4.3 Write the `review-harness` orchestrator: angle selection from `.sdd/harness.yaml` and the diff, sequential runs, one combined adversarial verifier per round, three-round bound, budget stop, `review.md` report, `review-harness` commit status — verify: on a sample change with one real and one false finding, the false one is refuted and listed, the real one is sent for fixing
- [ ] 4.4 Make the proposal adversarial pass systematic and scaled in the templates (`CLAUDE.md`, `OPENSPEC_GUIDE.md`) — verify: template text states both scales
- [ ] 4.5 Add the `.sdd/harness.yaml` template and its filling in `sdd-init` (tools detected: architecture rules, lint, mutation present or absent) — verify: `sdd-init` dry run on a sample project fills it and marks absent tools

## 5. Triggers, classification and the framing pull request

- [ ] 5.1 Add `.sdd/triggers.yaml` template (intent, irreversible, non-waivable gate machinery) and `classification.yaml` template — verify: schema documented in `OPENSPEC_GUIDE.md`, examples validate against it
- [ ] 5.2 Proposal step writes `classification.yaml` with evidence; the workflow refuses to generate design artifacts without it — verify: `/opsx:ff` on a change without classification stops with the reason
- [ ] 5.3 Framing pull request: after the adversarial pass the agent opens a PR with the proposal and classification only; the owner's merge is the approval; reclassification goes through a new framing PR — verify: documented in the templates and exercised on a sample repository

## 6. merge-conditions check

- [ ] 6.1 Write the trigger matcher (path globs and content regexes, reading `triggers.yaml` and the approved classification from the base branch) with its own test suite — verify: tests cover undeclared migration, waived intent path, gate-machinery edit, classification edited in the PR
- [ ] 6.2 Write `merge-conditions.yml` (`pull_request_target` + `workflow_run`, never executes PR code; aggregate gate from path filters; `review-harness` and `opsx-verify` statuses; commit status with `gates:` description) — verify: on a sample repository, a PR touching no filtered path is still judged, and a PR editing the workflow is judged by `main`'s version
- [ ] 6.3 Contributing guide section "what is enforced where" (client-side, server-side, honour-based) — verify: section present in the template

## 7. Guardrail with the verified merge route

- [ ] 7.1 Port geomni's Python guardrail cases into `block-git-writes.test.sh` (REST merge, `--auto`, tracking a protected branch, force-with-lease) — verify: the new cases fail against the current hook
- [ ] 7.2 Add `MERGE_METHOD` and `ALLOW_FORCE_WITH_LEASE` to the `.conf`, remove `ALLOW_PR_MERGE` and the autonomy levels from templates and `sdd-init` — verify: tests pass for both settings values
- [ ] 7.3 Implement the merge route: query head SHA and `merge-conditions` status, allow only `success` + `gates: none`, fail closed, refuse while an `in-flight` PR exists — verify: tests with a stubbed `gh` cover green/no gate, gate open, stale commit, GitHub unreachable, in-flight present; the suite still fails against allow-all and block-all hooks

## 8. Deploy guard, serialisation, rollback, report, local QA

- [ ] 8.1 Write `.sdd/bin/deploy-guard.sh` with tests (merged PR with green check passes; direct push, red check, unmerged PR refused) — verify: `bash .sdd/bin/deploy-guard.test.sh` passes
- [ ] 8.2 Add `.sdd/deployment.yaml` template and its generation in `sdd-init` (targets, rollback, probes, scheduled jobs, unconfirmed values listed) — verify: dry run on a sample project with a deploy workflow lists an unconfirmed rollback
- [ ] 8.3 Templates for wiring the guard into a GitHub Actions deploy job (with `concurrency`) and into Vercel's `ignoreCommand`, plus the push workflow that opens an alert issue — verify: on a sample repository a direct push to `main` produces no deploy and an issue
- [ ] 8.4 Delivery steps in the workflow templates: `in-flight` label, verification window from scheduled jobs, platform rollback then revert PR with `revert-of` classification, alert, fix change, final report format — verify: templates state each step; the merge-conditions matcher accepts an exact inverse revert and rejects a modified one (test)
- [ ] 8.5 Create the `local-qa` plugin (category `skill`, dependency of `sdd-core`) and implement its skill: inventory (docker labels, listening ports with cwd), reuse/start rule, isolated database on pending migration, `started.json`, cleanup, QA brief format — verify: with another project's container on the default port, the skill starts on a free port and cleanup stops only what it started
- [ ] 8.6 `sdd-init` adoption mode starts with the mapping table approved before any write; marker records the version; `--refresh` three-way merges from the tag `sdd-core-v<version>` — verify: refresh on a sample project with a local edit and a template change on different lines keeps both
- [ ] 8.7 Bump `sdd-core` to 0.4.0, CHANGELOG, tag `sdd-core-v0.4.0` — verify: `claude plugin validate .` and every test suite pass

## 9. geomni adoption (pilot)

- [ ] 9.1 In a geomni worktree, run `sdd-init` adoption: mapping table for `CLAUDE.md` §1, `AGENTS.md`, agents, hook, settings, CI — verify: owner approves the table before any write
- [ ] 9.2 Write geomni's `.sdd/triggers.yaml` (proposal list: any Flyway migration, stored formats incl. browser storage and Redis, edition publication, ETL replay, infra, consumed endpoints, quota; intent paths incl. scoring, ramps, classifier, taxonomy), `.sdd/deployment.yaml` (Cloud Run, Vercel, daily ETL scheduler), `.sdd/harness.yaml` — verify: the matcher test suite run against geomni's last 10 merged PRs classifies them as the owner would (owner checks the table)
- [ ] 9.3 Wire `merge-conditions.yml`, the deploy guard in `deploy-backend.yml` and `vercel.json`, the alert workflow; remove the Python guardrail and its `pr.yml` job — verify: geomni CI green on the adoption PR
- [ ] 9.4 Owner actions: Vercel read-only token, `in-flight` label created — verify: a test push to a scratch branch configured as protected is refused by the guard
- [ ] 9.5 Adoption PR merged by the owner

## 10. Post-deploy verification

- [ ] 10.1 Toolbox: install `sdd-core@claude-toolbox` from GitHub in a clean config — verify: plugins and dependencies load, version notice behaves on an old-marker project
- [ ] 10.2 geomni pilot: the next real geomni change runs the full cycle (framing PR, harness, merge-conditions, merge route or owner merge, deploy guard, verification, archive PR, report) — verify: report delivered; every step observed; deviations become fix changes
- [ ] 10.3 wifisense adoption after the pilot is verified, same steps as group 9 — verify: wifisense CI green and one change through the cycle
