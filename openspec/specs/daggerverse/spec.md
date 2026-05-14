## Purpose

Describe the existing repository structure and documentation baseline for Daggerverse.

## Requirements

### Requirement: Module repository layout

The repository SHALL organize reusable Dagger CI modules under the `modules/` directory.

#### Scenario: Locate a module
- **WHEN** a user looks for a module implementation
- **THEN** the module is available under `modules/<module-name>`
- **AND** each module directory contains its own Dagger module metadata and source code

### Requirement: Repository documentation

The repository SHALL keep English documentation under the `docs/` directory.

#### Scenario: Start reading documentation
- **WHEN** a user opens `docs/README.md`
- **THEN** the page explains the recommended learning path
- **AND** the page links to learning material, task guides, reference material, and design explanations

### Requirement: Module README links

Each module README SHALL point readers to the repository documentation.

#### Scenario: Read a module README
- **WHEN** a user opens `modules/<module-name>/README.md`
- **THEN** the README links to `docs/README.md`

### Requirement: OpenSpec baseline

The repository SHALL keep current-state specifications separate from planned change proposals.

#### Scenario: Document existing behavior
- **WHEN** behavior is already implemented
- **THEN** it is documented under `openspec/specs/`

#### Scenario: Document planned behavior
- **WHEN** behavior is planned but not implemented
- **THEN** it is documented under `openspec/changes/`
