# Spec Delta

## Purpose

Installs the workflow in a project and keeps it current: first setup from the project's own code,
adoption of a project that already has its own agent environment, and refresh to new kit versions.

## ADDED Requirements

### Requirement: Generated environment covers the factory
`sdd-init` SHALL generate, in addition to the rules, agents and guardrail, the project's triggers file,
deployment profile, aggregate CI gate, CI merge workflow and review harness configuration, each value
it could not prove marked for the owner to confirm.

#### Scenario: First setup
- **WHEN** `sdd-init` completes on a project with a deploy workflow
- **THEN** the project has a triggers file, a deployment profile, an aggregate gate and a merge workflow, and the setup report lists the unconfirmed values

### Requirement: Adoption mode
For a project that has its own agent environment and no kit marker, `sdd-init` SHALL run in adoption
mode: it SHALL map each existing rule file to its kit counterpart in an explicit table approved by the
owner before writing, and SHALL keep the project's language and project-specific rules.

#### Scenario: Rules in another file and language
- **WHEN** adoption runs on a project whose git rules live in a French CLAUDE.md section
- **THEN** the mapping table shows where each rule goes and nothing is written before the owner approves it

### Requirement: Refresh with a recorded base
The install marker SHALL record the kit version the project's generated files come from, and
`--refresh` SHALL merge three ways: the recorded template version, the new template version and the
project's current file, keeping local edits and reporting conflicts.

#### Scenario: Local edit and kit change on different lines
- **WHEN** a refresh finds a local edit and a kit change on different lines of the same file
- **THEN** both are kept without asking

#### Scenario: Conflicting edits
- **WHEN** a local edit and a kit change touch the same lines
- **THEN** the refresh reports the conflict to the owner instead of choosing

### Requirement: Setup is delivered as a change branch
The setup or refresh SHALL be committed on a dedicated branch and proposed as a pull request, never
written on a protected branch.

#### Scenario: Refresh on a project
- **WHEN** a refresh completes
- **THEN** its result is on a `chore/sdd-init` branch with a pull request open
