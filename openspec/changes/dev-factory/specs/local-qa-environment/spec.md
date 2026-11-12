# Spec Delta

## Purpose

Prepares a working local copy of the change for the owner's intent QA on a machine shared by parallel
projects and agents, without disturbing them, and hands the owner a clear QA brief.

## ADDED Requirements

### Requirement: Inventory before starting anything
Before preparing a QA environment, the agent SHALL inventory what already runs on the machine —
containers, listening ports, dev servers — and attribute each to its project and worktree when it can.

#### Scenario: Another project's database on the default port
- **WHEN** a container of another project already listens on the database port the change expects
- **THEN** the inventory reports it as belonging to that project

### Requirement: Never disturb what the agent did not start
The agent SHALL NOT stop, restart or reconfigure a container, process or port it did not start in the
current QA preparation.

#### Scenario: Port taken by another agent's dev server
- **WHEN** the port the frontend dev server defaults to is taken by another project's server
- **THEN** the agent starts its server on a free port and leaves the other one running

### Requirement: Reuse what is compatible, start what is missing
The agent SHALL reuse a running service only when it belongs to the same project and is compatible
with the change, and SHALL start every missing service on free ports, wiring the started services to
each other.

#### Scenario: Shared services of the same project running
- **WHEN** the project's shared database and cache containers already run
- **THEN** the agent reuses them and starts only the change's backend and frontend

#### Scenario: Incompatible schema
- **WHEN** the change carries a migration not applied to the running shared database
- **THEN** the agent does not migrate the shared database and starts an isolated one instead

### Requirement: QA brief
Once the environment answers, the agent SHALL hand the owner a QA brief with the link to open, then,
for each point, the gesture to make and the expected result, with before and after captures from its
own QA. The brief SHALL hold between three and six points.

#### Scenario: Brief delivered
- **WHEN** the environment of a change with the intent gate open is ready
- **THEN** the owner receives the link, the gestures, the expected results and the captures

### Requirement: Cleanup of what was started
After the owner's QA, or when the change leaves the QA stage, the agent SHALL stop what it started for
the QA and only that.

#### Scenario: QA passed
- **WHEN** the owner reports the QA as passed
- **THEN** the agent stops the services it started and the services it reused keep running
