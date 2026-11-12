# Contributing

Cross-cutting conventions for contributing to {{PROJECT_NAME}}.

---

## 1. Language

- **Prose** (issues, PRs, docs, review comments): **{{DOC_LANG}}**.
- **Code** (identifiers, file names, inline technical comments), **commit messages** and **OpenSpec artifacts**: **{{CODE_LANG}}**.
- No mixing of languages within a single identifier.

## 2. Git

Rules shared by humans and agents.
<!-- sdd:if autonomy-merge -->
Agents (sub-agents included) commit, push, open and merge PRs **themselves**, following this section; the hook described below enforces the mechanical part.
<!-- sdd:endif -->
<!-- sdd:if autonomy-pr -->
Agents (sub-agents included) commit, push and open PRs **themselves**; merging stays human. The hook described below enforces the mechanical part.
<!-- sdd:endif -->
<!-- sdd:if autonomy-commit -->
Agents (sub-agents included) commit on the change branch; push, PR and merge stay human: **the agent never pushes**, every `git push` is blocked by the hook (`ALLOW_PUSH=0`). The hook described below enforces the mechanical part.
<!-- sdd:endif -->

### Branches
- `{{DEFAULT_BRANCH}}`: stable branch. It only moves **through <!-- sdd:if github -->a merged PR<!-- sdd:endif --><!-- sdd:if !github -->a merge done by a human<!-- sdd:endif -->**: never a direct commit or push, hotfixes included.
- OpenSpec change: `<type>/<change-id>` — e.g. `feat/user-invitations`, `fix/refresh-token-rotation`.
- Outside a change: `<type>/<scope>-<desc>` — e.g. `fix/api-input-validation`, `docs/roadmap-resync`, `chore/tooling-hook-update`.

`<type>` = the branch's main Conventional Commits type; `<scope>` ∈ { <!-- sdd:fill: short module names ({{MODULE_NAME}}), plus `docs`, `tooling`, `ci` --> }; `<desc>` in kebab-case {{CODE_LANG}}.

- Session in a worktree created by the app (imposed branch name): rename the branch according to the convention before the first push (`git branch -m <name>`).
- A branch is deleted after merge, locally (`git branch -d`)<!-- sdd:if github --> and on the remote (`git push origin --delete <branch>`)<!-- sdd:endif -->.

### Commits — Conventional Commits
```
<type>(<scope>): <short imperative description>

<descriptive body: what changes + the key decisions>
```
Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `build`, `ci`.

**Scope**
- A commit that belongs to an **OpenSpec change** has **the change id** as scope: `feat(user-invitations): …`, `chore(user-invitations): …`.
- Otherwise, the scope is the **module** (`<module>`, `<module>/<sub-domain>`), or `docs`, `ci`, `tooling` (dev/agent tooling outside a change: hooks, skills).

**Message = subject + descriptive body, always, in {{CODE_LANG}}.** Short imperative subject; the body says what changes (what) and the key decisions; never the one-liner alone. No Claude attribution: no `Co-Authored-By` trailer, no "Generated with Claude Code" mention.

**Commit rules**
- One commit = one coherent slice (a module, the tests, the docs…); no "wip" commits.
- Staging with **explicit paths** (`git add <paths>`): never `git add -A` / `.` / `-u`, nor `git commit -a` — a commit only carries what we decided to put in it.
- Before a **code** commit: checks of the touched module green (the same commands as CI) and the review done on the diff (review harness for an OpenSpec change, `code-reviewer` otherwise). Before any commit touching `openspec/`: `openspec validate --all`.
- Never rewrite: no `--amend`, no `rebase`, no `reset` to a revision, no force-push. A mistake is fixed with a new commit.
- A long message, or one that quotes commands (`--amend`, `` `git pull` ``…): write it to a file and use `git commit -F <file>` (`gh pr create --body-file <file>`), rather than `-m`.

### Sequence of an OpenSpec change
The same order as the cycle in [`CLAUDE.md`](../CLAUDE.md) §3, on the `<type>/<change-id>` branch:
1. `docs(<id>): …` — framing: proposal, then deltas, design, tasks (one or two commits).
2. `/opsx:apply` → `/sdd-core:review-harness <id>` → `/opsx:verify` OK → `feat|fix|…(<id>): …`, one commit per coherent implementation slice.
3. `/opsx:archive` + post-archive → `chore(<id>): archive change, sync specs, post-archive`.
<!-- sdd:if autonomy-merge -->
4. Push the branch, PR, merge (below).
<!-- sdd:endif -->
<!-- sdd:if autonomy-pr -->
4. Push the branch, PR (below); human merge.
<!-- sdd:endif -->
<!-- sdd:if autonomy-commit -->
4. The agent stops at the last commit; a human pushes, opens the PR if there is a remote, and merges.
<!-- sdd:endif -->

Outside a change (hotfix, tooling, docs): same path, shorter — branch `<type>/<scope>-<desc>`, `code-reviewer` review if code changes, commit(s)<!-- sdd:if !autonomy-commit -->, PR<!-- sdd:endif --><!-- sdd:if autonomy-merge -->, merge<!-- sdd:endif -->.

### What the hook enforces
The hook [`.claude/hooks/block-git-writes.sh`](../.claude/hooks/block-git-writes.sh) (registered in [`.claude/settings.json`](../.claude/settings.json)) blocks, for an agent (sub-agents included):
- `commit`, `merge`, `revert`, `cherry-pick` on a protected branch. The branch is the one of the directory where the command really runs: the `cwd`, then each `cd`/`pushd`/`popd` and `git -C <dir>` (a subshell gives the directory back when it exits), and a `git switch|checkout <branch>` placed earlier in the same command — to a protected branch, counted immediately; to another branch, only if the next command is chained with `&&` (a failed switch stops the chain). A directory or branch that cannot be resolved (`$VAR`, `$(…)`, `cd -`, nonexistent directory) counts as protected: write literal paths, and run `git worktree add <dir>` in a separate call from the `cd <dir>` that follows;
- any push of a protected branch (including through `HEAD`, `@` or a `$…` reference while on it), a push without an explicit remote **and** branch (`git push -u origin <branch>`), force-push (`--force*`, `-f`, `+refspec`, `--mirror`, `--all`)<!-- sdd:if autonomy-commit --> — and here **every** `git push` (`ALLOW_PUSH=0`)<!-- sdd:endif -->;
- `pull` without `--ff-only`, with rebase, or, on a protected branch, of a branch other than itself;
- history rewriting: `rebase`, `commit --amend`, `reset` to a revision, `branch -f`, `am`, `commit-tree`, `filter-branch`;
- mass staging: `add -A` / `.` / `./` / `..` / `*` / `-u`, `commit -a`;
- what throws work away: `reset --hard`, `clean -f/--force`, `checkout .`/`-f`, `switch --discard-changes`, `restore .`, `stash drop/clear`, `branch -D`/`-M`;
- `--no-verify`;
- `gh pr merge` other than `--merge` (no `--squash`, `--rebase`, `--admin`, `--auto`)<!-- sdd:if !autonomy-merge -->, and here **every** `gh pr merge` (`ALLOW_PR_MERGE=0`)<!-- sdd:endif -->.

**Settings** — [`.claude/hooks/block-git-writes.conf`](../.claude/hooks/block-git-writes.conf) (committed, read by the hook if present):

| Key | Default | Effect |
|---|---|---|
| `PROTECTED_BRANCHES` | `main\|master` | Protected branches, separated by `\|` (here `{{DEFAULT_BRANCH}}`) |
| `ALLOW_PUSH` | `1` | `1`: the agent pushes its branch (never a protected branch); `0`: every `git push` blocked (a human pushes) |
| `ALLOW_PR_MERGE` | `1` | `1`: `gh pr merge --merge` allowed for the agent; `0`: every `gh pr merge` blocked (human merge) |

Before the checks, the command is read the way the shell reads it: escapes, `#` comments and quoted heredoc bodies are set aside, and quoted strings containing spaces (messages, PR bodies) are neutralised — their text is never read as an option or a command. What the shell executes (`$(…)`, backticks, including inside double quotes or an unquoted heredoc) is still checked.

Tests: `bash .claude/hooks/block-git-writes.test.sh`<!-- sdd:if ci -->, also run in CI on every change to the hook ([`tooling.yml`](../.github/workflows/tooling.yml))<!-- sdd:endif -->.<!-- sdd:if !lean --> Details: [`AGENT_TOOLBOX.md`](AGENT_TOOLBOX.md).<!-- sdd:endif --> It is a **guardrail against mistakes, not a sandbox** (deliberate `sh -c "…"`, `eval` are not covered); without server-side branch protection, the rule "`{{DEFAULT_BRANCH}}` only moves through <!-- sdd:if github -->a PR<!-- sdd:endif --><!-- sdd:if !github -->a human merge<!-- sdd:endif -->" relies on this hook and on this discipline. Without `jq`, the hook blocks every `git`/`gh` command until it is installed.

**Left to the user**, outside git: framing decisions, any spending commitment, any irreversible action on production or on data.

<!-- sdd:if !github -->
### Merge
- No GitHub remote: the branch is reviewed (review harness, or `code-reviewer` outside a change, with no open BLOCKER or MAJOR; for a change, `/opsx:verify` OK and change archived), then **a human** merges it into `{{DEFAULT_BRANCH}}` as a merge commit (`git merge --no-ff <branch>`).
<!-- sdd:endif -->
<!-- sdd:if github -->
### Pull Requests
- Title = subject of the main commit.
- Description in {{DOC_LANG}}: context, technical choices, impact, tests run<!-- sdd:if ui -->, screenshots<!-- sdd:endif -->. No Claude attribution.
- 1 PR = 1 topic (one OpenSpec change, or one fix). Outside a change, no mixing of modules without a reason.
- Green CI required: the workflows in [`.github/workflows/`](../.github/workflows/). They are path-filtered: a PR none of them concerns (docs only, for example) triggers no check — the condition is then met, provided the local checks have run.
- Review: the review of the diff is mandatory (review harness for a change, `code-reviewer` otherwise); it counts as the approval when the developer is alone on the repository.
- Waiting for CI with a fine-grained token: `gh pr checks` may fail (it needs permissions such tokens often lack). Use `gh run list --branch <branch>` to find the runs, then a single `gh run watch <run-id> --exit-status` in the background — no polling loop. A path-filtered PR that triggers no check at all meets the CI condition, provided the local checks have run.
<!-- sdd:endif -->
<!-- sdd:if autonomy-merge -->
- **An agent merges by itself** only if: green CI, review (harness for a change, `code-reviewer` otherwise) with no open BLOCKER or MAJOR, and — for an OpenSpec change — `/opsx:verify` OK and change archived on the branch. Otherwise it stops and asks the user.
- Merge as a **merge commit** (neither squash nor rebase), title `<subject> (#N)`: `gh pr merge <n> --merge --subject "<subject> (#<n>)"`.
- After the merge, in the main checkout: `git switch {{DEFAULT_BRANCH}} && git pull --ff-only`, then delete the branch (`git branch -d <branch>`, `git push origin --delete <branch>`). From a worktree, `{{DEFAULT_BRANCH}}` is already checked out elsewhere: only delete the remote branch; the local branch and the worktree are cleaned up from the main checkout (`git worktree remove` then `git branch -d`).
<!-- sdd:endif -->
<!-- sdd:if autonomy-pr -->
- The agent opens the PR, gives its link and the CI status, then stops: **a human merges**, as a merge commit.
<!-- sdd:endif -->
<!-- sdd:if github -->
- Access: `gh` must see the repository. On the agent side, a token limited to the repository can be set as `GH_TOKEN` in `.claude/settings.local.json` (gitignored, copied into worktrees by [`.worktreeinclude`](../.worktreeinclude)). **Never in `settings.json`, which is committed.** Fine-grained token, limited to this repository, with exactly: Contents read/write, Pull requests read/write, Actions read, Commit statuses read, Metadata read (template: [`.claude/settings.local.example.json`](../.claude/settings.local.example.json)). Tokens expire: a sudden 404 or 403 from `gh` on a repository that worked yesterday usually means an expired token. Such a token cannot create repositories — that needs a different token or the web UI. Without access,<!-- sdd:if !autonomy-commit --> the agent pushes the branch and gives the user the link to open the PR<!-- sdd:endif --><!-- sdd:if autonomy-commit --> the user pushes the branch and opens the PR themselves<!-- sdd:endif -->.
<!-- sdd:endif -->

## 3. Code style

<!-- sdd:each module -->
### `{{MODULE_PATH}}` ({{MODULE_STACK}})
- See [`{{MODULE_PATH}}/docs/CODING_RULES.md`](../{{MODULE_PATH}}/docs/CODING_RULES.md).
<!-- sdd:fill: 2-3 key rules of the module, taken from its CODING_RULES.md -->
<!-- sdd:endeach -->

## 4. Tests

<!-- sdd:each module -->
- **`{{MODULE_PATH}}`**: {{MODULE_TEST_KINDS}} — `{{MODULE_CHECK}}`. See [`TESTING_STRATEGY.md`](../{{MODULE_PATH}}/docs/TESTING_STRATEGY.md).
<!-- sdd:endeach -->

## 5. Documentation

- Every added feature updates the README of the relevant module if the public API changes.
- Every change to an observable contract **is born in the spec deltas** of the OpenSpec change (`openspec/changes/<id>/specs/`); the docs in `docs/` are updated afterwards, at post-archive (`doc-writer`).
- If a new business concept appears: entry in [`GLOSSARY.md`](GLOSSARY.md).
- A structural decision (technology, cross-cutting contract, architecture style): an ADR in [`adr/`](adr/).

## 6. Security

- Never commit a secret (`.env.local`, CI secrets, `.claude/settings.local.json`).
- Strict validation of every external input.
<!-- sdd:fill: project-specific security rules observed (auth, rate limiting, sensitive data not to log) -->
