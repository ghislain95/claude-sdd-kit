# System architecture — {{PROJECT_NAME}}

> Reverse documentation: this document describes the architecture **observed in the code** as of
> <!-- sdd:fill: date YYYY-MM-DD and short commit of the reverse documentation -->, not a target. Whatever
> could not be verified is marked "to be confirmed". Behaviour is defined by `openspec/specs/`;
> this document describes the **structure**.

---

## 1. Overview

{{PROJECT_PITCH}}

<!-- sdd:fill: ASCII or Mermaid diagram of the components (modules, databases, message queues, external services) and their main flows, taken from the code and the config/deployment files -->

## 2. Modules

| Module | Path | Stack | Role | Docs |
|---|---|---|---|---|
<!-- sdd:each module -->
| `{{MODULE_NAME}}` | `{{MODULE_PATH}}` | {{MODULE_STACK}} | <!-- sdd:fill: role in one sentence --> | [`CODING_RULES`](../{{MODULE_PATH}}/docs/CODING_RULES.md) · [`MODULES`](../{{MODULE_PATH}}/docs/MODULES.md) |
<!-- sdd:endeach -->

Observed architecture style: **{{ARCH_STYLE}}**.

## 3. External contracts

<!-- sdd:fill: the system's observable interfaces, by type — HTTP API (prefixes, versioning, error format, auth), messages/events (topics, queues, schemas), CLI, imported/exported files, webhooks. For each: where it is defined in the code (file:line). Not the full inventory of endpoints: the families and the conventions. Detailed contracts will be born in openspec/specs/ change by change. -->

## 4. Data model

<!-- sdd:fill: main business entities and their relations (short diagram), databases used, migration tool and migrations folder, observed cross-cutting rules (e.g. multi-tenant: every query filters by tenant; soft delete) -->

## 5. Critical flows

<!-- sdd:fill: 2 to 4 end-to-end journeys that carry {{DOMAIN_RISKS}} (e.g. an order from the API to the payment), as numbered steps with the file of each step -->

## 6. Security

<!-- sdd:fill: authentication (mechanism, lifetime, storage), authorisation (roles and where they are defined), input validation, secret management (environment variables, ignored files) — as observed -->

## 7. Environments and runtime

<!-- sdd:fill: how to run the project locally (exact commands), infrastructure dependencies (containers, compose), required environment variables (names only, never values), known deployment environments -->

## 8. Structural decisions

The decisions that shaped this architecture are in [`adr/`](adr/).

<!-- sdd:fill: list of the ADRs created by sdd-init for the implicit decisions observed (e.g. choice of framework, persistence style, monorepo), one line each with a link -->

## 9. Areas to confirm

<!-- sdd:fill: what the reverse documentation could not establish with certainty (apparently dead code, intent of a module, contradictory config), one line each — or "Nothing to confirm." -->
