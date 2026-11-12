# Spec Delta

## Purpose

The independent checks that stand in for the owner's eyes on every change: reviewer angles backed by
mechanical evidence, adversarial verification of findings, and a bounded fix loop.

## ADDED Requirements

### Requirement: Reviewer angles
The harness SHALL provide one reviewer per angle: spec conformance, project conventions and
architecture, bug hunting, tests, security, performance, interface, and sourced claims. Each reviewer
SHALL report findings with a severity among BLOCKER, MAJOR and MINOR and the location, plus, for a
BLOCKER or a MAJOR, the concrete scenario in which it fails.

#### Scenario: Finding format
- **WHEN** a reviewer reports a finding
- **THEN** the finding names its severity, its file and line, and, for a BLOCKER or MAJOR, the concrete scenario in which it fails

### Requirement: Angles selected by technical risk
The angles run on a change SHALL follow its technical risk: spec conformance, conventions, bug hunting,
tests and sourced claims always run, bug hunting and tests being skipped on a documentation-only
change; security, performance and interface run when the change touches their ground. The selection
SHALL be stated in the review report.

#### Scenario: Documentation-only change
- **WHEN** a change only edits documentation
- **THEN** the sourced-claims angle runs and the report states why the others were limited

#### Scenario: Interface change
- **WHEN** a change modifies a UI component
- **THEN** the interface angle runs

### Requirement: Mechanical backing
A reviewer SHALL back its opinion with a mechanical check when the project has one for its angle:
executable architecture rules, lint, measurements against the proposal's thresholds, mutation testing
scoped to the changed code. When the tooling is absent, the reviewer SHALL say so in its report.

#### Scenario: Mutation tooling absent
- **WHEN** the tests reviewer runs on a project without mutation tooling
- **THEN** its report states that test strength was judged without mutation evidence

#### Scenario: Surviving mutant
- **WHEN** a mutation of the changed code leaves every test green
- **THEN** the tests reviewer reports a finding on the missing assertion

### Requirement: Adversarial verification of findings
Every BLOCKER and MAJOR finding SHALL be verified by an independent agent instructed to refute it
before it is fixed. A refuted finding SHALL be dropped, with the refutation kept in the report.

#### Scenario: False positive refuted
- **WHEN** the verifier shows that a reported bug cannot occur
- **THEN** the finding is not sent to the developer and the report lists it as refuted

### Requirement: Bounded fix loop
Confirmed findings SHALL be sent to the developer agent, then re-reviewed by the angles concerned. The
loop SHALL stop at zero BLOCKER and zero MAJOR, or after the configured number of rounds (three by
default), in which case the agent SHALL stop and escalate to the owner with the open findings.

#### Scenario: Three rounds without convergence
- **WHEN** a MAJOR finding is still open after the last configured round (the third by default)
- **THEN** the agent stops and reports the open findings to the owner

### Requirement: Budget
The harness SHALL run within a per-change budget stated in the project's configuration — wall-clock
minutes and a number of agent runs, which bounds the tokens spent — with sequential agents, one heavy
build at a time, at normal or high effort. Exceeding the budget SHALL stop the harness and report what
was not covered.

#### Scenario: Budget exceeded
- **WHEN** the harness reaches its budget before every selected angle has run
- **THEN** it stops and the report names the angles not covered

### Requirement: Adversarial pass on proposals
Every proposal SHALL go through an adversarial pass before its design artifacts are generated, scaled
to the change: a short challenge for a small change, a full attempt to break it for a structural one.
Its objections SHALL be resolved in the proposal or put to the owner.

#### Scenario: Structural change
- **WHEN** a proposal introduces a new module or a migration
- **THEN** a full adversarial pass runs and its objections are resolved before design
