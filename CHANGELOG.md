# Changelog

Versions of the `sdd-core` and `sdd-ui` plugins. A version only reaches users when the `version`
in `plugins/*/.claude-plugin/plugin.json` changes (see [`MAINTAINING.md`](MAINTAINING.md)). After
updating the plugin, run `/sdd-core:sdd-init --refresh` in each installed project to bring its
generated files up to date.

## 0.2.0 — 2026-11-07

### Changed
- Everything is in English: README, guide (`TUTO.md` → `GUIDE.md`), skills, templates. Templates are
  now written in English and translated while being filled when a project chooses another docs
  language.
- No reference to the project the workflow was extracted from.

### Added
- `sdd-core` declares `superpowers@claude-plugins-official` as a dependency (the marketplace allows
  that cross-marketplace dependency). The official marketplace must be added first, otherwise
  `sdd-core` refuses to load: the install prompt and the docs do it.
- Curated `permissions.allow` in the generated `.claude/settings.json` (read-only git, OpenSpec,
  `gh run`/`gh pr`, graphify queries, hook tests) plus the module check commands, so "all the way"
  autonomy doesn't stall on permission prompts; `/fewer-permission-prompts` suggested afterwards.
- `graphify-hooks` option: `graphify hook install` (local git hooks keeping the graph fresh) is
  offered with `graphify` and recommended in the docs.
- `ui` option: `.claude/launch.json` generated from the UI modules' dev-server scripts (preview tools);
  `frontend-design` plugin suggested for building UI from scratch.
- CONTRIBUTING: waiting for CI with a fine-grained token (`gh run list` + one background
  `gh run watch --exit-status`), the token's exact permissions and expiry symptoms.
- CLAUDE.md: rules for parallel sessions on one checkout, restating module rules when dispatching an
  agent, never resetting a local database without asking (checksum realignment for comment-only
  edits of an applied migration), one heavy build at a time; agent fallback for the user-invoked
  `review-animations`; `graphify affected` in the add → migrate → remove task rule.
- README "Staying up to date", `CHANGELOG.md`, `MAINTAINING.md`.
- `sdd-core` session-start notice: in a project set up with an older kit than the installed plugin,
  a one-line message suggests `/sdd-core:sdd-init --refresh` (silent everywhere else).
- The desktop mods (`openspec-cockpit`, `conversation-cards`, `session-hud`, `background-tasks`) are
  listed in the marketplace and offered by the install prompt to desktop-app users.

Projects set up with 0.1.0: run `/sdd-core:sdd-init --refresh` (templates changed).

## 0.1.0 — 2026-11-07

- First release: `/sdd-core:sdd-init` (reverse-documentation, then OpenSpec, agents, git guardrail
  hook with autonomy levels, CI), `--refresh`, `passation`, `retro`, `domain-modeling`,
  `improve-codebase-architecture`; optional `sdd-ui` plugin; one-prompt install in the README.
