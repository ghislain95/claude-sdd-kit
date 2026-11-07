<!-- sdd:note: file generated ONLY if the graphify option is on; otherwise do not create it (and do not link it from CLAUDE.md or AGENT_TOOLBOX.md) -->
# Graphify — queryable code map

> A **reading/navigation** tool for AI assistants (Claude Code). Turns the repo into a local, queryable **knowledge graph**. **Not a source of truth**: `openspec/specs/` remains the behavioural truth; graphify writes nothing in the specs, decides nothing, codes nothing.

## Why

On a real-size codebase, answering "who calls X", "what links module A to module B", "what breaks if I touch this type" costs a lot of grepping and reading. Graphify answers through a graph (nodes = symbols, edges = calls/imports/inherits, cited `file:line`), with far fewer tokens than blind grepping — measure it on this repo with `graphify benchmark` (order of magnitude seen on other projects: ~5×).

**tree-sitter AST** parsing, local and deterministic, **zero network calls** for code. Docs/PDFs/images would only go through a semantic pass (LLM), **which does not run here**: see [Why the semantic pass does not run](#why-the-semantic-pass-does-not-run).

## Prerequisites (once per dev / CI)

```bash
uv tool install "graphifyy[sql]"   # the [sql] extra also captures SQL files (migrations, schemas)
graphify --version                  # must print a version
graphify install --platform claude  # installs the /graphify skill at user level (not in the repo)
```

Uninstall: see [Full removal](#full-removal).

## Build / refresh the graph

The graph lives in `graphify-out/` (**gitignored**, never committed — large and volatile).

```bash
# initial build, code-only (local AST, no API cost)
graphify extract . --code-only

# incremental refresh (re-extracts only changed files, AST-only)
graphify update .

# is the graph stale compared with the files?
graphify check-update .

# after a BIG refactor / deletions: force a re-scan
# (otherwise "ghost" nodes of deleted code remain)
graphify update . --force
```

**Exclusions**: a `.graphifyignore` (committed, `.gitignore` syntax) removes the noise and makes the graph **deterministic**.

| Excluded | Reason |
|---|---|
| Lockfiles | Huge, low value |
| `.claude/` | Agent tooling: skill docs have no place in the code graph |
| `**/*.md` | Without a semantic pass, a markdown file only produces **title** nodes, with no edge to the code; added commit after commit, they form an arbitrary partial index, more misleading than nothing. To search the docs: grep / direct reading (`openspec/specs/` remains the truth) |
| `graphify-out/` | The graph itself |
<!-- sdd:fill: stack-specific exclusions (stories, generated code, large fixtures…) with their reason — or nothing -->

**Tests are kept** (useful usage/impact context). Build folders already in `.gitignore` are excluded automatically (graphify respects it).

> **After any change to `.graphifyignore`, run `graphify update . --force`.** An
> incremental `update` alone leaves ghost nodes behind.

## Query

```bash
graphify query "<question>"          # BFS traversal for a free-form question (tune with --budget / --context)
graphify path "<A>" "<B>"            # shortest path (relations, cycles) — "no directed path" = real decoupling
graphify explain "<symbol>"          # a node + its neighbours, cited file:line + edge type (EXTRACTED/INFERRED)
graphify affected "<X>"              # reverse traversal: what is impacted by X
graphify god-nodes                   # architecture hubs (most connected nodes)
graphify benchmark graphify-out/graph.json   # measured token reduction
```

Visualisation: `graphify-out/graph.html` (`--no-viz` at build time if > 5000 nodes). Report: `graphify cluster-only . --no-label` generates `GRAPH_REPORT.md` with no LLM cost.

## Place in the OpenSpec workflow

The OpenSpec cycle (see [`CLAUDE.md` §3](../CLAUDE.md)) **does not change**. Graphify fits in as **reading** at three moments:

1. **Recon (pre-change)** — query the graph (`explain`/`path`/`affected`/`query`) **before** launching exploration agents or grepping. Then read the **targeted** files it points to.
2. **Framing / architecture** — `path "<A>" "<B>"` to check cycles and impact **before** proposing a design; `god-nodes` for the hubs concerned.
3. **Implementation** — find a precedent/pattern through `explain`/`query`.

**Freshness = priority**, owned by the main session ([`CLAUDE.md` §10](../CLAUDE.md)), not by the agents:

| Moment | Command |
|---|---|
| Before the `/opsx:new` recon | `graphify update .` then `graphify check-update .` — framing on a stale graph produces a wrong proposal |
| Before `/opsx:apply` | `graphify check-update .`; stale → `graphify update .` |
| After `/opsx:archive` | `graphify update . --force` if the change **deleted or renamed** files, else `graphify update .`; then `check-update .` |

After a notable code change in the middle of a task: `graphify update .`. When **dispatching an
agent** on code, remind it to query the graph **in the dispatch prompt**: its
definition already says so, but the prompt is the only reliable lever. An agent that must run these
commands needs the `Bash` tool.

**Recommended per-dev safety net**: `graphify hook install` (local, uncommitted — `.git/hooks/` is
not shared, so each developer runs it once; `graphify hook status` to check) rebuilds the graph
incrementally after each commit or checkout, AST only so no API cost. It comes on top of the three points above without replacing them: it does not cover the
`--force` after deletions.

## Integration choices (deliberate)

- **Skill installed at user level** (`graphify install --platform claude`, once per dev), **not committed** in `.claude/skills/`: it follows each developer's CLI version. **Shared config, not the graph**: `.graphifyignore` is committed, `graphify-out/` is gitignored and regenerated.
- **No committed graphify hook.** The auto-nudge (`graphify hook-guard` on every Read/Grep/Bash) is non-blocking but **frequent** and points to a **non-portable** absolute path. A dev who wants it: `graphify claude install --project` locally — ⚠️ it modifies `.claude/settings.json`, which is committed (it carries the git guardrail hook): do not add that change to the commit. Removal: `graphify claude uninstall`.
- **No `watch`** by default (avoid endless rebuilds).

## Limits

- A **stale** graph misleads → always refresh + `check-update` before relying on it.
- **Docs are not in the graph**, guaranteed by `.graphifyignore` (`**/*.md`), not by the `--code-only` flag → no code↔spec link.
- Free-text search (`query`) sometimes spreads out; the structural commands (`explain`/`path`/`affected`/`god-nodes`) are sharper.
- `god-nodes` surfaces shared test utility classes by construction: they are not architecture hubs.

### Why the semantic pass does not run

Findings from other projects (graphify 0.9.x), to re-check if the version changes:

- `--backend claude` requires `ANTHROPIC_API_KEY`. **It is not the CLI**: the name is misleading.
- `--backend claude-cli` goes through the CLI, but `claude -p` rejects the subscription's OAuth token
  (`401 OAuth access token has expired`, even right after logging in); it wants an API key.
- `--backend ollama` works but is unusable locally on a mid-size model (a few
  files in several tens of minutes).

⚠️ Extras add up explicitly: `uv tool install "graphifyy[sql,ollama]"`. Installing
`[ollama]` alone **uninstalls `[sql]`** and silently breaks the extraction of SQL migrations.

**Proof that the pass does not run**: every node and edge in `graph.json` carries
`_origin: "ast"`.

## Full removal

```bash
graphify uninstall                 # removes the skill from every detected platform
rm -rf graphify-out                # deletes the local graph
uv tool uninstall graphifyy        # removes the tool
```
