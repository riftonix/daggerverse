## Purpose

Describe the existing repository structure and documentation baseline for Daggerverse.

## Requirements

### Requirement: Module repository layout

The repository SHALL organize reusable Dagger CI modules under the `modules/` directory.

#### Scenario: Locate a module
- **WHEN** a user looks for a module implementation
- **THEN** the module is available under `modules/<module-name>`
- **AND** each module directory contains its own Dagger module metadata and source code

### Requirement: Scenario repository layout

The repository SHALL organize reusable Dagger CI scenarios under the `scenarios/` directory.

#### Scenario: Locate a scenario
- **WHEN** a user looks for a scenario implementation
- **THEN** the scenario is available under `scenarios/<scenario-name>`
- **AND** each scenario directory contains its own Dagger module metadata and source code

### Requirement: Repository documentation

The repository SHALL keep English documentation under the `docs/` directory.

#### Scenario: Start reading documentation
- **WHEN** a user opens `docs/README.md`
- **THEN** the page explains the recommended learning path
- **AND** the page links to learning material, task guides, reference material, and design explanations

#### Scenario: Read container image CI documentation
- **WHEN** a user reads the repository documentation for container image CI
- **THEN** it SHALL explain that `modules/docker` provides reusable Docker and OCI primitives
- **AND** it SHALL explain that `scenarios/container-images` provides portable image verification and publication functions
- **AND** it SHALL explain that CI-provider workflows own event triggers, changed path selection, and tag-to-image-reference mapping

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
- **THEN** the tests SHALL be runnable with `make tests module <module-name>`
- **AND** the target SHALL call the module test aggregate function

#### Scenario: Run scenario tests
- **WHEN** a user or CI needs to run tests for a scenario with a Dagger test module
- **THEN** the tests SHALL be runnable with `make tests scenario <scenario-name>`
- **AND** the target SHALL call the scenario test aggregate function

#### Scenario: Scenario has no tests
- **WHEN** a scenario has no Dagger test module
- **THEN** CI discovery SHALL NOT fail only because that scenario has no tests

#### Scenario: Remove legacy shorthand test command
- **WHEN** a user runs a legacy module-only shorthand such as `make tests docker`
- **THEN** the Makefile SHALL reject the command through the generic explicit-form usage validation
- **AND** it SHALL NOT translate the shorthand to `make tests module docker`

#### Scenario: Run lint for all Python components
- **WHEN** a user or CI runs `make lint` or `make lint-check` without a component selector
- **THEN** the command SHALL run Ruff against all existing Python component roots under `modules/` and `scenarios/`

#### Scenario: Run lint for one module
- **WHEN** a user or CI runs `make lint module docker` or `make lint-check module docker`
- **THEN** the command SHALL run Ruff only against `modules/docker`

#### Scenario: Run lint for one scenario
- **WHEN** a user or CI runs `make lint scenario container-images` or `make lint-check scenario container-images`
- **THEN** the command SHALL run Ruff only against `scenarios/container-images`

#### Scenario: Run format for all Python components
- **WHEN** a user or CI runs `make format` or `make format-check` without a component selector
- **THEN** the command SHALL run Ruff formatting against all existing Python component roots under `modules/` and `scenarios/`

#### Scenario: Shared Ruff configuration
- **WHEN** Ruff commands run from the repository root
- **THEN** Ruff SHALL use a shared repository-level configuration file
- **AND** the Ruff configuration SHALL NOT live under `modules/`

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
- **AND** the Git test module SHALL remain runnable with `make tests module git`

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
- **AND** GitHub Actions SHALL run each discovered module through `make tests module <module-name>`
- **AND** the workflow SHALL use the repository-aligned Dagger CLI version

#### Scenario: A module does not yet have Dagger tests
- **WHEN** a module has no Dagger test module
- **THEN** GitHub Actions SHALL NOT fail only because that module has no tests
- **AND** the module MAY be skipped until tests are added for it

#### Scenario: Module tests fail
- **WHEN** a module Dagger test fails in pull request CI
- **THEN** the pull request CI SHALL fail

### Requirement: GitHub pull request CI for available scenario tests

The repository SHALL run available Dagger scenario tests in GitHub Actions for pull requests targeting the repository default branch.

#### Scenario: Pull request targets default branch
- **WHEN** a pull request targets the repository default branch
- **THEN** GitHub Actions SHALL discover scenarios with Dagger test modules under `scenarios/<scenario-name>/tests`
- **AND** GitHub Actions SHALL run each discovered scenario test aggregate function

#### Scenario: Scenario tests fail
- **WHEN** a scenario Dagger test fails in pull request CI
- **THEN** the pull request CI SHALL fail

### Requirement: Scenario publication workflow

The repository SHALL publish Dagger scenarios through GitHub Actions using rules analogous to module publication.

#### Scenario: Publish all scenarios on default branch push
- **WHEN** changes are pushed to the default branch
- **THEN** GitHub Actions SHALL discover scenarios under `scenarios/<scenario-name>` with Dagger module metadata
- **AND** GitHub Actions SHALL publish each discovered scenario

#### Scenario: Publish one scenario from release tag
- **WHEN** a tag matching `scenarios/<scenario-name>/vX.Y.Z` is pushed
- **THEN** GitHub Actions SHALL publish only the named scenario
- **AND** the workflow SHALL fail clearly if the tag references an unknown scenario

### Requirement: Dagger version alignment

The repository SHALL align Dagger module metadata and CI on the repository Dagger version.

#### Scenario: Dagger module metadata is updated
- **WHEN** Dagger module metadata is updated
- **THEN** affected Dagger module metadata SHALL use the repository-aligned engine version
- **AND** generated SDK artifacts SHALL be consistent with that engine version
