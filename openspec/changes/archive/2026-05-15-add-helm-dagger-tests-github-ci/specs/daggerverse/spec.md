## ADDED Requirements

### Requirement: Repository command interface

The repository SHALL expose supported local and CI workflows through the root `Makefile`.

#### Scenario: Run module tests

- **WHEN** a user or CI needs to run tests for a module with a Dagger test module
- **THEN** the tests SHALL be runnable with `make tests <module-name>`
- **AND** the target SHALL call the module test aggregate function.

#### Scenario: Run module maintenance commands

- **WHEN** a user needs to run a supported maintenance command for modules
- **THEN** the command SHOULD be available through the root `Makefile`
- **AND** module-specific commands SHOULD accept a positional module name, such as `make lint <module-name>` or `make format <module-name>`.

### Requirement: Dagger-native module tests

When module-specific tests are added for a reusable Dagger module, the repository SHALL implement them as a neighboring Dagger test module.

#### Scenario: Add tests for a module

- **WHEN** tests are added for `modules/<module-name>`
- **THEN** the tests SHOULD live under `modules/<module-name>/tests`
- **AND** the test directory SHOULD be a Dagger module
- **AND** the test module SHOULD depend on the parent module through a local dependency
- **AND** test functions SHOULD call the parent module public API rather than shelling out to the Dagger CLI to call the parent module.

#### Scenario: Run all tests for a tested module

- **WHEN** a module has a Dagger test module
- **THEN** the test module SHOULD expose an aggregate function suitable for CI
- **AND** the aggregate function SHOULD run the module checks that are expected to gate pull requests.

### Requirement: Helm module Dagger tests

The Helm module SHALL have a Dagger test module that verifies the existing fixture chart through the Helm module public API.

#### Scenario: Verify Helm lint

- **WHEN** the Helm test module aggregate test runs
- **THEN** it SHALL run Helm lint against the existing fixture chart
- **AND** lint failures SHALL fail the test.

#### Scenario: Verify Helm template

- **WHEN** the Helm test module aggregate test runs
- **THEN** it SHALL run Helm template against the existing fixture chart
- **AND** template failures SHALL fail the test.

#### Scenario: Verify Helm package

- **WHEN** the Helm test module aggregate test runs
- **THEN** it SHALL package the existing fixture chart
- **AND** package failures SHALL fail the test.

#### Scenario: Verify Helm push

- **WHEN** the Helm test module aggregate test runs
- **THEN** it SHALL push the existing fixture chart to a local OCI registry service
- **AND** push failures SHALL fail the test
- **AND** the test SHALL NOT require GitHub Container Registry credentials.

#### Scenario: Verify Helm publication lookup

- **WHEN** the Helm test module aggregate test runs after pushing the fixture chart to a local OCI registry service
- **THEN** it SHALL verify the pushed chart version through the Helm module publication lookup function
- **AND** lookup failures SHALL fail the test
- **AND** the test SHALL NOT depend on pre-existing external registry state.

### Requirement: GitHub pull request CI for available module tests

The repository SHALL run the in-scope Dagger module tests in GitHub Actions for pull requests targeting the repository default branch.

#### Scenario: Pull request targets default branch

- **WHEN** a pull request targets the repository default branch
- **THEN** GitHub Actions SHALL discover modules with Dagger test modules
- **AND** GitHub Actions SHALL run each discovered module through `make tests <module-name>`
- **AND** the workflow SHALL use Dagger CLI version `0.20.6`.

#### Scenario: A module does not yet have Dagger tests

- **WHEN** a module has no Dagger test module
- **THEN** GitHub Actions SHALL NOT fail only because that module has no tests
- **AND** the module MAY be skipped until tests are added for it.

#### Scenario: Helm tests fail

- **WHEN** the Helm Dagger test module fails in pull request CI
- **THEN** the pull request CI SHALL fail.

### Requirement: Dagger version alignment

The repository SHALL align the Helm test module work and GitHub pull request CI on Dagger `0.20.6`.

#### Scenario: Dagger module metadata is updated

- **WHEN** the Helm test module change is implemented
- **THEN** affected Dagger module metadata SHALL use engine version `v0.20.6`
- **AND** generated SDK artifacts SHALL be consistent with that engine version.
