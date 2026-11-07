<!-- sdd:note: instantiated once per module in {{MODULE_PATH}}/docs/MODULES.md. Inventory taken from the code: one `##` per root package/folder, nothing invented. Stay at the "role + key types/services + specific rules" granularity (ten lines per package at most): the fine detail lives in the code and will be born in the specs. -->
# Modules — `{{MODULE_NAME}}`

Index of the root packages/folders of `{{MODULE_PATH}}`. This page is the **source of truth for the structure** — any evolution goes through here first.

> Strict rule: **do not invent a new root package** without validation. See [`CODING_RULES.md`](CODING_RULES.md).

Exhaustive list: <!-- sdd:fill: list of the root packages in backticks, comma-separated -->

---

<!-- sdd:fill: for each root package, one section:

## `<package>` — <role in a few words>

- `<key type or file>` — <what it carries>.
- `<key service>` — <responsibility>, <notable business rule>.
- Depends on: `<packages>`; never depends on: `<packages>` (if observable).
- ⚠️ <observed debt or ambiguity, to be confirmed> (if needed).
-->

## Startup

<!-- sdd:fill: module entry point (file), local start command, required configuration (names of the environment variables, never values) -->
