# Maintaining the kit

How to publish a new version, and what users experience.

## Publishing a version

1. **Change** the skills, templates or docs on a branch (`feat/…`, `fix/…`, `docs/…`).
2. **Check**:
   ```bash
   claude plugin validate .
   claude plugin validate plugins/sdd-core
   claude plugin validate plugins/sdd-ui
   bash plugins/sdd-core/skills/sdd-init/templates/claude/hooks/block-git-writes.test.sh
   bash plugins/sdd-core/hooks/check-kit-version.test.sh
   ```
   For a template change, also dry-run `sdd-init` on a throwaway project (one module and several
   modules if the change concerns `multi-module`) and check that no `{{…}}` or `sdd:` marker is left.
3. **Bump `version`** in `plugins/<plugin>/.claude-plugin/plugin.json` of every plugin you changed
   (semver: a template or behaviour change is at least a minor bump). **Without a bump, users don't
   receive anything**: Claude Code keeps their cached copy until the version string changes. Keep the
   version in `plugin.json` only, not in the marketplace entry as well.
4. **Write the entry** in [`CHANGELOG.md`](CHANGELOG.md): what changed, and whether projects need
   `/sdd-core:sdd-init --refresh` to benefit from it (template changes do; a new skill doesn't).
5. **Pull request**, review, merge into `main`. The marketplace serves `main`.
6. Optional: `claude plugin tag` creates a `<plugin>--v<version>` git tag, needed only if another
   plugin wants to depend on a version range of this one.

## The desktop mods

The marketplace lists the four desktop mods with a `git-subdir` source on
`ghislain95/claude-mods` (`ref: main`). They follow their own `version` in that repository: a
version bump there reaches users without any change here. Change the entries in
`.claude-plugin/marketplace.json` only to add, remove or pin a mod (`ref` to a tag or `sha`).

## What users experience

- **Plugin, with auto-update on** (`/plugin` → Marketplaces → `sdd-kit` → Enable auto-update): during
  a session, Claude Code refreshes the marketplace in the background, installs the new version and
  tells them; `/reload-plugins` or a restart applies it.
- **Plugin, with auto-update off** (the default for third-party marketplaces): nothing happens until
  they run `claude plugin marketplace update sdd-kit && claude plugin update sdd-core@sdd-kit`.
- **Projects**: the files `sdd-init` generated are copies. When a session opens in a project whose
  `CLAUDE.md` marker is older than the installed `sdd-core`, the plugin's session-start hook
  (`plugins/sdd-core/hooks/check-kit-version.sh`) shows a one-line notice.
  The files change only when someone runs
  `/sdd-core:sdd-init --refresh` (or the README's install prompt) in the project; it applies the kit's
  changes and keeps local edits. Say in the CHANGELOG when a refresh is worth it.

## Changing the git guardrail hook

The hook is copied into projects. Any change must keep `block-git-writes.test.sh` green and add the
cases it covers; projects get it through `--refresh`, which replaces the `.sh`/`.pl`/`.test.sh` files
and keeps the project's `.conf`.
