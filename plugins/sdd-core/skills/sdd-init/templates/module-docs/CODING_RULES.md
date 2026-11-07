<!-- sdd:note: instantiated once per module in {{MODULE_PATH}}/docs/CODING_RULES.md. Every rule is taken from the real code (majority pattern observed, lint/format config, architecture test) — never from a generic "best practice" absent from the code. A rule only partly observed (minority pattern) is marked "trend, to be confirmed". Remove a section with no observable content rather than inventing, then renumber the sections. -->
# Coding rules — `{{MODULE_NAME}}`

**These rules are strict.** Any exception is justified explicitly in the PR (or in the change's `design.md`).

Stack: {{MODULE_STACK}} — versions pinned in `{{MODULE_DEPS_FILE}}`.

---

## 1. Architectural style

<!-- sdd:fill: observed style ({{ARCH_STYLE}} for this module) in 2-4 bullets, and what it is NOT (e.g. "no canonical DDD with formal bounded contexts"). A "❌ Never…" about unrequested reorganisation -->

## 2. Structure — source of truth

<!-- sdd:fill: CLOSED list of the module's root packages/folders (e.g. `src/<pkg>/{a,b,c}`), with the rule "do not invent a new root package: discussion + update of MODULES.md before any code". Pointer to MODULES.md -->

## 3. Internal conventions

<!-- sdd:fill: typical tree of a package/feature as observed (e.g. model/ service/ repository/ api/), in a code block, with the role of each folder -->

## 4. Domain / adapter separation

<!-- sdd:fill: what is forbidden in adapters (HTTP controllers, message handlers, jobs, CLI): no business logic; forbidden dependencies from the domain to frameworks; where the logic lives (service names). Cite the automated check if one exists (architecture test, import lint) with its file, otherwise "not enforced by tooling" -->

## 5. Boundaries (API, messages, UI)

<!-- sdd:fill: rules observed at the boundaries: DTOs/validation schemas, error format, status codes, serialisation, auth handling at adapter level. For a UI module: components vs pages, state, data access -->

<!-- sdd:if migrations -->
## 6. Persistence

<!-- sdd:fill: ORM/driver, migration tool and folder, observed rules (transactions, queries filtered by tenant, no automatic schema generation), "an applied migration is never modified" -->
<!-- sdd:endif -->

## 7. Code style

<!-- sdd:fill: format/lint tools and their config (file), observed naming conventions, typing (strict? `any`/ignore tolerated?), import rules -->

## 8. Logging

<!-- sdd:fill: logging library, levels used, what must never be logged (secrets, tokens, personal data, full payloads at info level) -->

## 9. Error handling

<!-- sdd:fill: typed business exceptions/errors? global handler? validation at the boundaries? per-message error isolation in a consumer? fail fast vs fallback -->

## 10. Tests

- Tests: {{MODULE_TEST_KINDS}}. Detailed strategy: [`TESTING_STRATEGY.md`](TESTING_STRATEGY.md).
- Full check, identical to CI: `{{MODULE_CHECK}}`.
<!-- sdd:fill: 2-3 test rules specific to the module (e.g. no full application context for pure logic) -->

## 11. Language

- Code, identifiers, inline technical comments: **{{CODE_LANG}}**.
- Markdown documentation: **{{DOC_LANG}}**.

## 12. Critical guardrails

When describing, modifying or generating code in this module:

1. Always start from the **existing structure**.
2. **Never** invent a missing domain or root package.
3. **Never** reorganise the architecture without an explicit request.
4. **Never** put business logic in an adapter.
<!-- sdd:fill: guardrails specific to the module and the domain ({{DOMAIN_RISKS}}) -->
