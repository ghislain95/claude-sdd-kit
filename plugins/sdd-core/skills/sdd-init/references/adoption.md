# Adopting a project that already has tooling, and `--refresh`

## 1. The project already has target files

Rule: **what exists was written for a reason.** Merge, don't overwrite.

| File present | What to do |
|---|---|
| `CLAUDE.md` | Read it in full. Keep everything specific to the project (rules, context, pitfalls). Add the template sections that are missing; if an existing section contradicts the workflow (e.g. "commit straight to main"), flag it and ask at gate 1 — don't decide alone. |
| `AGENTS.md` (multi-tool format) | Don't replace it: add a "Claude agent team" section pointing to `.claude/agents/README.md`. |
| `.claude/agents/<x>.md` | Same name as a template → compare: keep the existing file's specific rules, add the template's blocks (USE WHEN / DO NOT USE description, output format, graphify…). Different name → keep it and add it to the routing table. |
| `.claude/settings.json` | JSON merge: add the git guardrail's `PreToolUse` hook, remove or change nothing else. |
| `.claude/hooks/*` from another git guardrail | Show both to the user, recommend keeping only one (two contradictory hooks = baffling blocks). |
| `openspec/` already initialised | No `openspec init`. `openspec update` to refresh the commands. `config.yaml`: merge `context` and `rules` (add the template rules that are missing). Existing specs are **not** touched. |
| `docs/*.md` with the same name | Merge section by section; whatever contradicts the observed code is flagged in the report (not silently fixed). |
| Existing CI | Only add `openspec.yml` and `tooling.yml`; don't touch the existing workflows. |

Show the diff of every merged file at validation gate 1 (summary: sections added / kept / in
conflict).

## 2. Install marker

Last line of the generated `CLAUDE.md`:

```markdown
<!-- claude-toolbox: installed <sdd-core plugin version> on <YYYY-MM-DD> — options: <list> — autonomy: <level> -->
```

It is what `--refresh` relies on. Read the version in the plugin's `.claude-plugin/plugin.json` (two
levels above this skill).

## 3. `/sdd-init --refresh` — resync with a newer version of the kit

1. Read the marker (`claude-toolbox: installed …`, or `sdd-kit: installed …` for a project set up before
   the catalog was renamed — rewrite it to the new form): installed version, options, autonomy. Missing → this project was not set up by
   the kit: offer a full install in adoption mode (§1).
2. Branch `chore/sdd-init-refresh-<version>`.
3. For every file generated from a template (`CLAUDE.md`, `AGENTS.md`, `.claude/agents/*`,
   `docs/{CONTRIBUTING,OPENSPEC_GUIDE,AGENT_TOOLBOX,GRAPHIFY}.md`, `openspec/config.yaml`,
   `.claude/hooks/*`, `.claude/settings.json` (union of the `allow` lists and hooks, nothing removed),
   `.claude/settings.local.example.json`, `.claude/launch.json` (option `ui`), the kit's CI workflows):
   - fill the **new** template with the project's values (read back from the current files, not
     deduced again);
   - compare with the current file: what differs comes either from the kit (to apply) or from a local
     change (to keep). When in doubt about where a difference comes from, keep the local version and
     list it.
4. Files copied verbatim (hook `.sh`/`.pl`/`.test.sh`): replaced, then
   `bash .claude/hooks/block-git-writes.test.sh`; the local `.conf` is kept.
5. Never touch: `openspec/specs/`, `openspec/changes/`, the reverse-documentation (`ARCHITECTURE.md`,
   module docs, glossary, ADRs, roadmap) — it belongs to the project.
6. Phase 5 of `SKILL.md` (checks), then one commit `chore(sdd-init): refresh workflow to <version>`
   listing in its body what comes from the kit and the local differences kept. Marker updated.
