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
/opsx:new <change-id> → /opsx:ff → /opsx:apply → /opsx:verify → /opsx:archive
```

With the agent team (routing: [`CLAUDE.md`](../CLAUDE.md) §8, details: [`AGENTS.md`](../AGENTS.md)):

1. **Framing** — `product-owner`: `proposal.md` (intent, scope, non-goals,
   testable criteria), roadmap epic referenced.
1b. **Adversarial pass** — always, scaled: `architect` tries to break the proposal (a full
   attempt for a structural change, the five strongest objections for a small one); objections are
   resolved in the proposal, or put to the user, before `/opsx:ff`.
2. **Design** — `architect`: spec deltas (Given/When/Then, translatable 1:1 into tests) +
   `design.md` (owning module, migration yes/no, layer boundaries, decisions
   sourced at the pinned version).
3. **Implementation** — `<module>-dev`<!-- sdd:if multi-module --> / `full-stack-dev`<!-- sdd:endif -->: `tasks.md` ticked as
   it goes; `tester` checks: 1 delta scenario = 1 test.
4. **Verification** — `/sdd-core:review-harness <id>` (every review angle, findings adversarially
   verified, three fix rounds at most, report in `review.md`), then `/opsx:verify` (compliance with
   the deltas, tests actually run).
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
