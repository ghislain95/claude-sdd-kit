# Spec Delta

## Purpose

A per-project description of what merging deploys, how to roll it back, how to probe it and which
scheduled jobs run the merged code later, read by the classification and by the delivery.

## ADDED Requirements

### Requirement: Every project has a deployment profile
A project set up by the kit SHALL have a deployment profile, versioned in the repository, stating for
each deploy target what triggers it on merge, the platform rollback command, and the post-deploy
probes. A project whose merge deploys nothing SHALL state so explicitly.

#### Scenario: Project with two deploy targets
- **WHEN** the profile of a project whose merge deploys a backend to Cloud Run and a frontend to Vercel is read
- **THEN** it lists both targets, each with its trigger, its rollback command and its probes

#### Scenario: Project without deployment
- **WHEN** the profile of a project whose merge deploys nothing is read
- **THEN** it states that merging deploys nothing and lists no rollback command

### Requirement: Scheduled jobs are declared
The deployment profile SHALL list every scheduled job that executes the project's code after a merge,
with its schedule and the code paths it executes.

#### Scenario: Daily ETL declared
- **WHEN** a project runs a daily scheduled ETL job built from its repository
- **THEN** the profile lists that job, its schedule and the code paths it runs

### Requirement: Rollback commands are executable as written
Each rollback command of the profile SHALL return the target to the deployment that preceded the last
merge without rebuilding from source, and SHALL be runnable by the agent with the permissions the
project grants it.

#### Scenario: Backend rollback
- **WHEN** the agent runs the backend rollback command after a failed verification
- **THEN** traffic returns to the previous backend revision without a new build

### Requirement: The profile is generated and kept current
`sdd-init` SHALL generate the deployment profile from the project's CI and deployment files, and SHALL
list each value it could not prove as a point for the owner to confirm.

#### Scenario: Unproven rollback
- **WHEN** `sdd-init` finds a deploy workflow but no evidence of how to roll it back
- **THEN** the profile marks the rollback as unconfirmed and the setup report asks the owner for it
