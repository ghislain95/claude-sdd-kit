# Spec Delta

## Purpose

Decides, change by change, which human gates stand between an approved proposal and production: the
intent gate for what the user sees and does, the irreversible gate for what a revert cannot undo.

## ADDED Requirements

### Requirement: Every proposal carries a classification
Every change proposal SHALL carry a classification stating, for the intent gate and for the
irreversible gate, whether it is open, with the evidence for each answer, and any trigger it waives
with the reason. The owner SHALL approve the classification together with the proposal.

#### Scenario: Classification missing
- **WHEN** a proposal without a classification is submitted for approval
- **THEN** the workflow refuses to go on to the design artifacts

#### Scenario: Classification approved
- **WHEN** the owner approves a proposal
- **THEN** its classification is recorded as approved and becomes the reference for the mechanical check

### Requirement: Intent gate
The intent gate SHALL be open when the change visibly alters a business gesture, a screen, or what the
product shows or how it feels, whatever the layer the change lives in. An open intent gate SHALL
require the owner's QA before merge.

#### Scenario: Backend scoring change
- **WHEN** a change only modifies a backend scoring rule that changes the colours the map shows
- **THEN** the intent gate is open

#### Scenario: Internal refactor
- **WHEN** a change restructures code without any visible difference
- **THEN** the intent gate is closed

### Requirement: Revertible means code only
A change SHALL be revertible only when it changes code alone: no schema migration, no change to a
stored format (database, cache, browser storage, published artefact), no rollout step after merge, and
no consumption of paid quota or capacity. A change that is not revertible SHALL open the irreversible
gate, which requires the owner's go before merge.

#### Scenario: Additive migration
- **WHEN** a change adds a column through a migration and nothing else
- **THEN** the irreversible gate is open

#### Scenario: Browser storage format change
- **WHEN** a change modifies the shape of data the frontend persists in browser storage
- **THEN** the irreversible gate is open

#### Scenario: Pure code change
- **WHEN** a change modifies only application code, with no stored format, migration, rollout step or quota consumption
- **THEN** the irreversible gate is closed

### Requirement: Per-project triggers
Each project SHALL declare, in a versioned triggers file, the path and content patterns that open each
gate. The irreversible triggers SHALL at least cover migrations, stored formats, post-merge rollout
steps, infrastructure, consumed public endpoints, and quota consumption.

#### Scenario: geomni migration trigger
- **WHEN** a diff of geomni adds a file under the Flyway migrations folder
- **THEN** the irreversible trigger matches

### Requirement: Gate machinery is always gated
A change that modifies the triggers file, an approved classification, the agent hooks or settings, the
deployment profile or the CI workflows SHALL open the irreversible gate, and this trigger SHALL NOT be
waivable.

#### Scenario: Pull request weakens a trigger
- **WHEN** a pull request edits the triggers file
- **THEN** the irreversible gate opens regardless of the approved classification

### Requirement: Mechanical check of the diff
Before any merge, a mechanical check SHALL match the diff of the pull request against the triggers and
the approved classification, both read from the base branch, never from the pull request. A match on
a gate the classification declared closed, without an explicit waiver, SHALL block the merge.

#### Scenario: Undeclared migration
- **WHEN** a change classified with both gates closed contains a migration file
- **THEN** the merge is blocked and the report names the trigger and the file

#### Scenario: Classification edited in the pull request
- **WHEN** a pull request changes its own classification after approval
- **THEN** the check uses the approved classification from the base branch and the gate-machinery trigger opens the irreversible gate

#### Scenario: Waived intent trigger
- **WHEN** a diff matches an intent path trigger that the approved classification waived with a reason
- **THEN** the intent gate stays closed for that trigger
