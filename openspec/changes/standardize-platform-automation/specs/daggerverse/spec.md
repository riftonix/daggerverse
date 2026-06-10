## MODIFIED Requirements

### Requirement: Repository command interface

The repository SHALL expose supported local and CI workflows through GitHub Actions workflows that can be reused in hosted CI and, where supported, run locally through `act`.

#### Scenario: Run module tests

- **WHEN** a user or CI needs to run tests for a module with a Dagger test module
- **THEN** the tests SHALL be runnable through the repository's GitHub Actions test workflow
- **AND** the workflow SHALL call the module test aggregate function
- **AND** local execution SHALL be available through a documented `act` command when the workflow is marked as locally supported

#### Scenario: Run scenario tests

- **WHEN** a user or CI needs to run tests for a scenario with a Dagger test module
- **THEN** the tests SHALL be runnable through the repository's GitHub Actions test workflow
- **AND** the workflow SHALL call the scenario test aggregate function
- **AND** local execution SHALL be available through a documented `act` command when the workflow is marked as locally supported

#### Scenario: Scenario has no tests

- **WHEN** a scenario has no Dagger test module
- **THEN** CI discovery SHALL NOT fail only because that scenario has no tests

#### Scenario: Remove legacy shorthand test command

- **WHEN** a user runs a legacy module-only shorthand such as `make tests docker`
- **THEN** the repository SHALL NOT treat that shorthand as a supported command interface
- **AND** documentation SHALL direct users to the supported workflow or `act` command instead

#### Scenario: Run lint for all Python components

- **WHEN** a user or CI runs the repository quality workflow without a component selector
- **THEN** the workflow SHALL run Ruff against all existing Python component roots under `modules/` and `scenarios/`

#### Scenario: Run lint for one module

- **WHEN** a user or CI runs the repository quality workflow with a module selector such as `module docker`
- **THEN** the workflow SHALL run Ruff only against `modules/docker`

#### Scenario: Run lint for one scenario

- **WHEN** a user or CI runs the repository quality workflow with a scenario selector such as `scenario container-images`
- **THEN** the workflow SHALL run Ruff only against `scenarios/container-images`

#### Scenario: Run format for all Python components

- **WHEN** a user or CI runs the repository format workflow without a component selector
- **THEN** the workflow SHALL run Ruff formatting against all existing Python component roots under `modules/` and `scenarios/`

#### Scenario: Shared Ruff configuration

- **WHEN** Ruff commands run from the repository workflow
- **THEN** Ruff SHALL use a shared repository-level configuration file
- **AND** the Ruff configuration SHALL NOT live under `modules/`

#### Scenario: Transitional Makefile during migration

- **WHEN** the repository still contains a root Makefile during the platform automation migration
- **THEN** the Makefile SHALL be treated as transitional automation
- **AND** equivalent GitHub Actions workflow and local `act` paths SHALL be documented before removing the transitional targets
