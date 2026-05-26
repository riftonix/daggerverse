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

### Requirement: Repository command interface

The repository SHALL expose supported local and CI workflows through the root `Makefile`.

#### Scenario: Run module tests
- **WHEN** a user or CI needs to run tests for a module with a Dagger test module
- **THEN** the tests SHALL be runnable with `make tests <module-name>`
- **AND** the target SHALL call the module test aggregate function

#### Scenario: Run module maintenance commands
- **WHEN** a user needs to run a supported maintenance command for modules
- **THEN** the command SHOULD be available through the root `Makefile`
- **AND** module-specific commands SHOULD accept a positional module name, such as `make lint-check <module-name>` or `make format-check <module-name>`

### Requirement: Dagger-native module tests

When module-specific tests are added for a reusable Dagger module, the repository SHALL implement them as a neighboring Dagger test module.

#### Scenario: Add tests for a module
- **WHEN** tests are added for `modules/<module-name>`
- **THEN** the tests SHOULD live under `modules/<module-name>/tests`
- **AND** the test directory SHOULD be a Dagger module
- **AND** the test module SHOULD depend on the parent module through a local dependency
- **AND** test functions SHOULD call the parent module public API rather than shelling out to the Dagger CLI to call the parent module

#### Scenario: Document test implementation guidance
- **WHEN** a contributor needs to add Dagger-native tests for a module
- **THEN** repository documentation SHALL include practical guidance for writing Dagger CI modules and tests
- **AND** the guidance SHALL describe the neighboring test module pattern
- **AND** the guidance SHALL describe calling parent module APIs through local Dagger dependencies

#### Scenario: Implement Git module feature
- **WHEN** a feature is implemented for `modules/git`
- **THEN** the same implementation step SHALL add or update Dagger-native tests for that feature
- **AND** the Git test module SHALL remain runnable with `make tests git`

#### Scenario: Run all tests for a tested module
- **WHEN** a module has a Dagger test module
- **THEN** the test module SHOULD expose an aggregate function suitable for CI
- **AND** the aggregate function SHOULD run the module checks that are expected to gate pull requests

### Requirement: Helm module Dagger tests

The Helm module SHALL have a Dagger test module that verifies the existing fixture chart through the Helm module public API.

#### Scenario: Verify Helm lint
- **WHEN** the Helm test module aggregate test runs
- **THEN** it SHALL run Helm lint against the existing fixture chart
- **AND** lint failures SHALL fail the test

#### Scenario: Verify Helm template
- **WHEN** the Helm test module aggregate test runs
- **THEN** it SHALL run Helm template against the existing fixture chart
- **AND** template failures SHALL fail the test

#### Scenario: Verify Helm package
- **WHEN** the Helm test module aggregate test runs
- **THEN** it SHALL package the existing fixture chart
- **AND** package failures SHALL fail the test

#### Scenario: Verify Helm push
- **WHEN** the Helm test module aggregate test runs
- **THEN** it SHALL push the existing fixture chart to a local OCI registry service
- **AND** push failures SHALL fail the test
- **AND** the test SHALL NOT require GitHub Container Registry credentials

#### Scenario: Verify Helm publication lookup
- **WHEN** the Helm test module aggregate test runs after pushing the fixture chart to a local OCI registry service
- **THEN** it SHALL verify the pushed chart version through the Helm module publication lookup function
- **AND** lookup failures SHALL fail the test
- **AND** the test SHALL NOT depend on pre-existing external registry state

### Requirement: GitHub pull request CI for available module tests

The repository SHALL run the in-scope Dagger module tests in GitHub Actions for pull requests targeting the repository default branch.

#### Scenario: Pull request targets default branch
- **WHEN** a pull request targets the repository default branch
- **THEN** GitHub Actions SHALL discover modules with Dagger test modules
- **AND** GitHub Actions SHALL run each discovered module through `make tests <module-name>`
- **AND** the workflow SHALL use Dagger CLI version `0.20.6`

#### Scenario: A module does not yet have Dagger tests
- **WHEN** a module has no Dagger test module
- **THEN** GitHub Actions SHALL NOT fail only because that module has no tests
- **AND** the module MAY be skipped until tests are added for it

#### Scenario: Module tests fail
- **WHEN** a module Dagger test fails in pull request CI
- **THEN** the pull request CI SHALL fail

### Requirement: Dagger version alignment

The repository SHALL align the Helm test module work and GitHub pull request CI on Dagger `0.20.6`.

#### Scenario: Dagger module metadata is updated
- **WHEN** the Helm test module change is implemented
- **THEN** affected Dagger module metadata SHALL use engine version `v0.20.6`
- **AND** generated SDK artifacts SHALL be consistent with that engine version
