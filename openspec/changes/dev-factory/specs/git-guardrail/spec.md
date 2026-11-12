# Spec Delta

## Purpose

Filters the agent's git and GitHub commands to prevent mistakes — writes to protected branches,
destroyed work, bypassed hooks — configured per project; a guard against mistakes, not a security
boundary.

## ADDED Requirements

### Requirement: Protected branches are never written by the agent
The guardrail SHALL block any agent command that commits, merges, reverts, cherry-picks or pulls onto a
protected branch, pushes a protected branch, or sets a branch to track a protected branch, judging the
branch where the command really runs.

#### Scenario: Commit on main through a directory change
- **WHEN** the agent runs a command that changes into a checkout on `main` and commits there
- **THEN** the command is blocked

#### Scenario: Commit on a change branch
- **WHEN** the agent commits explicitly staged paths on `feat/<change-id>`
- **THEN** the command is allowed

### Requirement: One verified merge route
The guardrail SHALL allow the agent a single merge route, the GitHub CLI merge command with the
project's merge method, and only after querying GitHub itself that `merge-conditions` is green on the
pull request's head commit and reports no open gate. Every other route — REST merge endpoint, automatic
merge, another merge method — SHALL be blocked.

#### Scenario: REST merge
- **WHEN** the agent calls the pull request merge endpoint through the GitHub API
- **THEN** the command is blocked

#### Scenario: CLI merge with conditions green
- **WHEN** the agent runs the CLI merge with the project's method and GitHub reports `merge-conditions` green with no open gate on the head commit
- **THEN** the command is allowed

#### Scenario: CLI merge with a gate open
- **WHEN** GitHub reports an open gate for the pull request
- **THEN** the command is blocked and the message tells the agent to hand the merge to the owner

#### Scenario: GitHub unreachable
- **WHEN** the guardrail cannot obtain the check status from GitHub
- **THEN** the merge is blocked

### Requirement: Work is never destroyed or hooks bypassed
The guardrail SHALL block history rewriting, commands that discard work, sweeping stages, and any
option that skips git hooks.

#### Scenario: Hard reset
- **WHEN** the agent runs a hard reset
- **THEN** the command is blocked

#### Scenario: Skipping hooks
- **WHEN** the agent commits with an option that skips hooks
- **THEN** the command is blocked

### Requirement: Per-project settings
The guardrail SHALL read its project settings from a versioned configuration: protected branches,
allowed merge method for the CI merge, and whether `--force-with-lease` is allowed on change branches.

#### Scenario: Force with lease allowed
- **WHEN** the project allows force-with-lease and the agent force-pushes its change branch with a lease
- **THEN** the command is allowed

#### Scenario: Force with lease not allowed
- **WHEN** the project does not allow it
- **THEN** the same command is blocked

### Requirement: Tested guardrail
The guardrail SHALL ship with a regression suite that runs in the project's CI, and that suite SHALL
fail against a guardrail that allows everything and against one that blocks everything.

#### Scenario: Weakened guardrail
- **WHEN** the guardrail is replaced by one that allows every command
- **THEN** the regression suite fails in CI
