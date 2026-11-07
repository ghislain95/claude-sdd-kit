<!-- sdd:note: instantiated once per module in {{MODULE_PATH}}/docs/TESTING_STRATEGY.md. Describe the OBSERVED way of testing (frameworks, folders, fixtures, existing helpers); if the module has few or no tests, say so and propose the minimal strategy, marking it "target, to be validated" + a line in the Backlog of docs/ROADMAP.md. -->
# Testing strategy — `{{MODULE_NAME}}`

> Reference for how to test `{{MODULE_PATH}}` ({{MODULE_STACK}}). Any deviation is justified in the PR.

---

## 1. Test pyramid

| Layer | Tools | Scope | When to use it |
|---|---|---|---|
<!-- sdd:fill: one line per observed layer (integration, unit, e2e, not tested directly), with tools, scope and selection rule. Mark the PRIMARY layer (the one where the business rules live) -->

<!-- sdd:fill: observed non-negotiable rule(s), e.g. "never an embedded database: containers with the production engine" — or remove the line -->

## 2. Running the tests

```bash
{{MODULE_CHECK}}             # everything, identical to CI
```

<!-- sdd:fill: commands to run a single file / a single test / a tag, and prerequisites (Docker, local database, environment variables) -->

## 3. Layout

<!-- sdd:fill: where the tests, fixtures and helpers live (tree block), and the naming convention of test files -->

## 4. From spec scenario to test

Each `#### Scenario:` of an OpenSpec spec yields **one** test, named after the scenario, following its GIVEN/WHEN/THEN.

<!-- sdd:fill: how to translate a GIVEN/WHEN/THEN concretely in this module (Gherkin/Cucumber if present, otherwise a parameterised test or a function named `test_<scenario>`), with a short example in the real stack -->

## 5. Isolation and data

<!-- sdd:fill: how tests isolate themselves (rolled-back transaction, explicit cleanup, database per test, mocks), unique random vs fixed data, async waiting (never a sleep: waiting tool used) -->

## 6. Assertions

- Assert according to the **contract**: an order assertion only if the spec imposes an order; otherwise an order-insensitive comparison, or a shuffled fixture to test a sort.
- A weakened assertion, a raised threshold or a disabled test "to make it pass" is a BLOCKER in review.
<!-- sdd:fill: assertion levels used in the module (status only, key fields, full body, database invariants) and when to pick which -->

## 7. Checklist when adding a feature

<!-- sdd:fill: 4-7 concrete steps in this module (create the test file here, fixture there, cleanup, run) -->

## 8. Anti-patterns to flag in review

| ❌ Anti-pattern | ✅ Do instead |
|---|---|
| Test disabled, skipped or neutralised without justification | Fix the cause, or justify in writing |
| Waiting with a fixed `sleep` | Waiting tool with a condition and a max delay |
| Order assertion without an order contract | Order-insensitive comparison |
<!-- sdd:fill: anti-patterns specific to the module's stack and helpers -->
