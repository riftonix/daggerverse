## MODIFIED Requirements

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
