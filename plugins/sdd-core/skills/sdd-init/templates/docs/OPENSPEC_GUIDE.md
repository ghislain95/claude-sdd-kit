# {{PROJECT_NAME}} — OpenSpec guide (SDD)

> Practical guide to the Spec Driven Development workflow on {{PROJECT_NAME}}.
> Audience: developer (human or agent) working in Claude Code.
> Upstream reference: [OpenSpec](https://github.com/Fission-AI/OpenSpec), [`CLAUDE.md`](../CLAUDE.md), [`AGENTS.md`](../AGENTS.md).

---

## 1. The concepts in 30 seconds

- **`openspec/specs/<domain>/spec.md`** — the **source of truth**: how the
  system behaves *today*. Never edited by hand.
- **`openspec/changes/<change-id>/`** — a **change** = a proposed evolution,
  a self-contained folder: `proposal.md` (why), `specs/` (deltas: what),
  `design.md` (how), `tasks.md` (steps).
- **Delta** — a change declares `ADDED` / `MODIFIED` / `REMOVED` Requirements
  relative to the current specs, without rewriting them.
- **Archive** — `/opsx:archive` merges the deltas into `openspec/specs/` and
  archives the change. The only moment the specs move: the loop
  feeds itself.
- **`openspec/config.yaml`** — the project context and writing rules injected
  into every artifact (proposal, specs, design, tasks).

Specs are born **change by change**: an existing domain without a spec gets its own
from the first change that touches it (the `ADDED` delta then describes the current behaviour
it touches, not the whole domain). No massive reverse-spec: it is expensive and goes stale fast.

## 2. "I want to…" → what to do

| I want to | Action |
|---|---|
| Implement an epic/ticket from the roadmap | `/opsx:new <change-id>` then the full cycle (§3) |
| A feature not framed yet | `/opsx:new <change-id>` — `product-owner` frames it with you |
| Explore an idea without committing | `/opsx:explore` |
| Fix a bug that contradicts a spec | `/opsx:new fix-<bug>` |
| Trivial hotfix (< 30 min, specified behaviour intact) | Direct implementation on a `fix/…` branch, no change |
| Resume a change in progress | `/opsx:continue` or `/opsx:apply` |
| Check the implementation against the specs | `/opsx:verify` |
| Finish a delivered change | `/opsx:archive` |
| Fix a spec (typo, precision) | A small change (`/opsx:new fix-spec-<domain>`, `MODIFIED` delta) then `/opsx:archive` — `/opsx:sync` only carries the deltas of an **existing** change over into `specs/`; never a manual edit of `specs/` |
| Discover the cycle on a real example | `/opsx:onboard` |

## 3. The full cycle of a feature

```
/opsx:new <change-id> → classification → framing merge (approval) → /opsx:ff → /opsx:apply → /opsx:verify → /opsx:archive
```

With the agent team (routing: [`CLAUDE.md`](../CLAUDE.md) §8, details: [`AGENTS.md`](../AGENTS.md)):

1. **Framing** — `product-owner`: `proposal.md` (intent, scope, non-goals,
   testable criteria), roadmap epic referenced, and `classification.yaml` next to it (§7): the
   intent and irreversible gates, open or closed, each with its evidence.
1b. **Adversarial pass** — always, scaled: `architect` tries to break the proposal (a full
   attempt for a structural change — new module, new contract, migration, cross-cutting choice, new
   mechanism —, the five strongest objections for a small one), its classification included;
   objections are resolved in the proposal, or put to the user, before the framing merge.
1c. **Framing <!-- sdd:if github -->pull request<!-- sdd:endif --><!-- sdd:if !github -->merge<!-- sdd:endif -->** — branch `docs/<change-id>-framing`, carrying only the change
   folder (proposal, classification, `.openspec.yaml`)<!-- sdd:if github -->, opened as a pull request<!-- sdd:endif -->. **Its merge
   into `{{DEFAULT_BRANCH}}` by the owner is the approval**: the classification on
   `{{DEFAULT_BRANCH}}` is the one every check reads. No `/opsx:ff`, no apply before it is merged.
   A classification found wrong during apply is amended by a **new** framing branch
   (`docs/<change-id>-framing-2`, the classification and the proposal only); once it is merged, the
   change branch merges `{{DEFAULT_BRANCH}}` in and goes on. Editing the approved classification in
   the change branch never counts: the check reads `{{DEFAULT_BRANCH}}`'s version and treats the edit
   as gate machinery.
2. **Design** — `architect`, on the change branch `<type>/<change-id>` cut from
   `{{DEFAULT_BRANCH}}` after the framing merge: spec deltas (Given/When/Then, translatable 1:1 into tests) +
   `design.md` (owning module, migration yes/no, layer boundaries, decisions
   sourced at the pinned version).
3. **Implementation** — `<module>-dev`<!-- sdd:if multi-module --> / `full-stack-dev`<!-- sdd:endif -->: `tasks.md` ticked as
   it goes; `tester` checks: 1 delta scenario = 1 test.
4. **Verification** — `/sdd-core:review-harness <id>` (every review angle, findings adversarially
   verified, three fix rounds at most, report in `review.md`, commit status `review-harness`), then
   `/opsx:verify` (compliance with the deltas, tests actually run; when it passes, commit status
   `opsx-verify` on the pushed head, [`CONTRIBUTING.md`](CONTRIBUTING.md) §2).
5. **Archiving** — implementation commit(s) by the agent on the change branch (Conventional
   Commits, [`CONTRIBUTING.md`](CONTRIBUTING.md) §2), `/opsx:archive`, post-archive (`doc-writer`
   checks that `docs/` does not contradict the merged specs), commit `chore(<id>)`; finally<!-- sdd:if github --> push, PR and merge<!-- sdd:endif --><!-- sdd:if !github --> a merge by a human<!-- sdd:endif -->
   according to the autonomy level in [`CONTRIBUTING.md`](CONTRIBUTING.md) §2.

**Context hygiene**: a fresh context per phase (`/clear`, or `/handoff:passation` then a
new session) — the artifacts carry the memory.

## 4. Writing rules for specs and deltas

- **SHALL or MUST on the first line** of each requirement's text
  (the validator only reads the first physical line for this check).
- **Observable behaviour only**: endpoints, events, commands, exchange
  formats, error codes. No class names (→ `design.md`).
- `#### Scenario:` scenarios in GIVEN/WHEN/THEN, translatable 1:1 into tests.
- Cover the error cases (invalid input, duplicate, insufficient rights, unknown
  resource, limit reached), not just the happy path.
- Everything in **{{CODE_LANG}}** (like the code and the tests).
- The future does not go into the specs: an unimplemented epic = a future change
  (the intent lives in [`ROADMAP.md`](ROADMAP.md)).
- Any impact on {{DOMAIN_RISKS}} must be explicit in the proposal.

## 5. Useful CLI

```bash
openspec validate --all     # before every commit touching openspec/
openspec list               # changes in progress
openspec status             # state of a change's artifacts
openspec update             # after an upgrade of the npm package (regenerates /opsx:* and skills)
```

The CLI version is pinned in CI (`.github/workflows/openspec.yml`): bump it **at the same
time** locally and in CI, deliberately.

## 6. Known pitfalls

- ❌ Editing `openspec/specs/` by hand → archive/sync only. Single exception: the
  `## Purpose` section (deltas do not carry it), fixed in the archive commit of the change that
  makes it wrong (`CLAUDE.md` §3). CI (`.github/workflows/openspec.yml`) rejects a diff of
  `openspec/specs/` without `openspec/changes/`.
- ❌ SHALL/MUST pushed to the 2nd line by a line break → validation fails.
- ❌ Implementing a contract absent from the specs → a change is missing.
- ❌ Deviating from `design.md` without updating it.
- ❌ Forgetting `/opsx:archive` after delivery → the specs drift.
- ❌ Believing `/opsx:verify` finishes the work: it **audits**, it neither commits nor archives.
- ❌ Committing or pushing on `{{DEFAULT_BRANCH}}` → never: everything goes through a branch and <!-- sdd:if github -->a PR<!-- sdd:endif --><!-- sdd:if !github -->a human merge<!-- sdd:endif -->
  ([`CONTRIBUTING.md`](CONTRIBUTING.md) §2).
- ❌ `/opsx:ff` or `/opsx:apply` before the framing merge → the change has no approved
  classification: the artifacts rules stop, and a change pull request without one is judged
  `gates: unclassified` (a human merges it).
- ❌ Fixing a wrong classification inside the change branch → it is not read, and the edit opens the
  irreversible gate as gate machinery; reclassify through a new framing branch (§3, 1c).

## 7. Classification and triggers

Two files decide, change by change, which human gates stand between an approved proposal and
production. Both are YAML, both are checked by `python3 .sdd/bin/merge_conditions.py validate <file>`.

- **Intent gate** — the change visibly alters a business gesture, a screen, what the product shows or
  how it feels, whatever the layer (a backend scoring rule that changes the colours on screen counts).
  Open → the owner runs a short QA before merge.
- **Irreversible gate** — the change is not *code only*: a migration, a stored format (database,
  cache, browser storage, published file), a rollout step after merge, consumption of paid quota or
  capacity, infrastructure, a public endpoint others consume. Open → the owner gives the go (merges).
- **Gate machinery** — whatever changes what CI or the check does: triggers and every `.sdd/` file,
  any `classification.yaml` outside a framing pull request, hooks, agent settings, `.github/`,
  `.gitattributes`, `.gitmodules`, `openspec/config.yaml`, `vercel.json`: always opens the
  irreversible gate, never waivable.
- Technical risk opens no gate: it raises review depth and post-deploy checks instead.

### `.sdd/triggers.yaml` — what opens a gate (per project)

```yaml
intent:
  paths: [ 'web/src/**', 'api/src/scoring/**' ]       # GitHub path-filter globs
  content:
    - paths: [ 'api/src/**' ]                         # optional: every file when omitted
      pattern: 'colorRamp|scoreWeight'                # Python regex, searched in ADDED lines only
irreversible:
  paths: [ 'api/migrations/**', 'infra/**', 'api/openapi.yaml' ]
  content:
    - paths: [ 'web/src/**' ]
      pattern: 'localStorage\.setItem|sessionStorage\.setItem'
gate_machinery:                                       # never waivable
  paths: [ 'deploy/release.sh' ]                      # the project's own, on top of the built-in list
```

- `paths`: a file the pull request adds, modifies or deletes opens the gate. `*` stops at `/`, `**`
  crosses it, `?` is zero or one of the preceding character (GitHub's syntax).
- `content`: one hit per file, on the first added line that matches; removed lines never match. Every
  file is read as text (binary files and `.gitattributes` settings included). A pattern only sees
  one added line at a time: it misses a construct split across lines, and a change that alters
  behaviour without adding a matching line (a removed guard, an edited constant elsewhere) — use
  `paths` for what must never slip through.
- `gate_machinery`: built in, always applied even when omitted: `.github/**`, `.sdd/**`,
  `.claude/hooks/**`, `.claude/settings.json`, `**/.gitattributes`, `.gitmodules`,
  `openspec/config.yaml`, `vercel.json`; add the project's own (release scripts, deploy
  configuration). Adding, changing or deleting any `openspec/changes/**/classification.yaml` outside
  a framing pull request is gate machinery too, whether or not `{{DEFAULT_BRANCH}}` already has it
  (the archive pull request's identical move excepted).
- Read from `{{DEFAULT_BRANCH}}` only: a pull request that edits this file is judged by the previous
  version (and opens the irreversible gate).

### `openspec/changes/<id>/classification.yaml` — the gates of one change

```yaml
change: add-export                       # the change folder's name
intent:
  open: true
  evidence: "Adds an Export button to the report screen and a new download flow"
  waived: []
irreversible:
  open: false
  evidence: "Code only: no migration, no stored format, the CSV is generated on demand and not kept"
  waived:
    - trigger: 'api/openapi.yaml'        # exactly as written in triggers.yaml
      reason: "Adds an optional field to an internal endpoint no other client calls"
# revert_of: <change-id>                 # only on the classification of a revert pull request
```

- `open` and a non-empty `evidence` for both gates, always. `waived` lists the triggers the diff
  will hit although the gate stays closed, each with its reason; a waiver never closes gate machinery.
- Written by the proposal step, challenged by the adversarial pass, approved by the framing merge
  (§3). The copy on `{{DEFAULT_BRANCH}}` is the only one read.

### What the check does with them
<!-- sdd:if github -->

The `merge-conditions` commit status (workflow `.github/workflows/merge-conditions.yml`, run from
`{{DEFAULT_BRANCH}}`, never from the pull request) classifies each pull request:
<!-- sdd:endif -->
<!-- sdd:if !github -->

`python3 .sdd/bin/merge_conditions.py match --base {{DEFAULT_BRANCH}} --head <branch> --branch <branch>`
classifies a branch the same way:
<!-- sdd:endif -->

| Pull request | Recognised by | Result |
|---|---|---|
| framing | only files of `openspec/changes/<id>/`, `classification.yaml` among them | `gates: framing` — the owner's merge approves |
| change | touches exactly one change folder `openspec/changes/<id>/` (its `tasks.md` at least), from a branch `<type>/<id>`, and `{{DEFAULT_BRANCH}}` holds that change's classification | gates = the classification's open gates + every trigger hit not waived; a hit on a gate declared closed, without a waiver, is **unaccounted** and fails the check; an invalid approved classification gives `gates: invalid` and fails |
| archive | moves `openspec/changes/<id>/` into one folder `openspec/changes/archive/YYYY-MM-DD-<id>/` (or `<id>/`) and touches only `openspec/specs/`, `docs/`, `ROADMAP.md`, `BACKLOG.md` | judged on its own diff, normally `gates: none` |
| unclassified | touches no change folder (hotfix, tooling) — the branch name alone never selects a classification — or its change has no approved classification | `gates: unclassified` — a human merges |

Touching several change folders, or a folder the branch does not name, is an error (the check fails),
and so is a `.sdd/triggers.yaml` missing from `{{DEFAULT_BRANCH}}`. The description reads
`gates: <gates>[ - <what is missing or wrong>]; base <sha7>`, the gates being `none`, `intent`,
`irreversible`, `intent+irreversible`, `framing`, `unclassified` or `invalid`, and `base` the commit
of `{{DEFAULT_BRANCH}}` the verdict was computed against. Only `gates: none` is a change an agent may
merge, and only while `base` is still the head of `{{DEFAULT_BRANCH}}`; any other value is merged by
the owner.<!-- sdd:if github --> A push to `{{DEFAULT_BRANCH}}` re-judges every open pull request into
it (`pending`, `re-judging: …`, first). The status protects against mistakes only: a workflow the pull
request adds, or the agent's own token, can overwrite it. The deploy guard therefore never reads it:
it recomputes the verdict server-side (`merge_conditions.py match --base <merge>^1 --head <pull request
head>`, exit 1 on an unaccounted hit or an error).<!-- sdd:endif -->
