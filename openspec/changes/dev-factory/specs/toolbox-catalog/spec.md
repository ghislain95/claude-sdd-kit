# Spec Delta

## Purpose

The single catalog from which every Claude tool of the owner — workflow plugins, standalone skills and
desktop mods — is installed, updated and released.

## ADDED Requirements

### Requirement: Single catalog named claude-toolbox
The catalog SHALL be one repository whose marketplace `name` is `claude-toolbox`, and it SHALL list
every plugin of the owner: workflow plugins, standalone skills and desktop mods. `claude plugin
validate` SHALL pass on the catalog root.

#### Scenario: Catalog validates
- **WHEN** `claude plugin validate` runs on the catalog root
- **THEN** it reports no error

#### Scenario: Plugin installed by catalog name
- **WHEN** a user adds the catalog and installs `handoff@claude-toolbox`
- **THEN** the plugin installs and `claude plugin list` shows it enabled

### Requirement: One plugin per usage
A capability usable outside the spec-driven workflow SHALL be its own plugin. A plugin that needs
another plugin of the catalog SHALL declare it as a dependency instead of embedding a copy of it.

#### Scenario: Handoff installed alone
- **WHEN** a user installs `handoff@claude-toolbox` without `sdd-core`
- **THEN** the handoff skill is available and no workflow skill is installed

#### Scenario: Workflow plugin pulls its dependency
- **WHEN** a user installs `sdd-core@claude-toolbox`
- **THEN** `handoff` is installed as its dependency

#### Scenario: Dependency added to an installed plugin
- **WHEN** a release adds a dependency to a plugin users may already have installed
- **THEN** its changelog entry and the README give the command that installs the new dependency, since an in-place update does not install it

### Requirement: Every entry carries a category
Each plugin entry of the catalog SHALL carry a `category` among `workflow`, `skill` and `mod`, and a
description that states what it does and, for a mod, that it only works in the desktop app.

#### Scenario: Mod listed with its category
- **WHEN** a user browses the catalog in `/plugin`
- **THEN** each mod shows the `mod` category and a desktop-app-only description

### Requirement: Compatibility across the rename for one version
For one minor version after the rename, the catalog SHALL keep working for projects set up with the
former `sdd-kit` catalog: the version check SHALL recognise both the former and the new install
marker, and the handoff files SHALL stay in the `.claude/passation/` folder the mods read.

#### Scenario: Project set up with the former kit
- **WHEN** a session starts in a project whose CLAUDE.md carries the former `sdd-kit: installed` marker
- **THEN** the version check runs and, if the project is behind, suggests a refresh

#### Scenario: Mods still read handoff files
- **WHEN** the handoff skill writes a handoff document
- **THEN** it lands in `.claude/passation/` and the cockpit mod lists it

### Requirement: The toolbox release is gated
Merging the catalog's main branch SHALL be treated as a production release for its users. A change to
the guardrail or hook templates, to `sdd-init`, to the catalog manifest or to the version-check hook
SHALL open the irreversible gate of the toolbox's own classification.

#### Scenario: Guardrail template change
- **WHEN** a pull request of the toolbox modifies the guardrail template
- **THEN** the mechanical check opens the irreversible gate and the merge waits for the owner's go
