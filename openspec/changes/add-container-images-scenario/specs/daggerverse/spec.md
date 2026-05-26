## ADDED Requirements

### Requirement: Container image module and scenario documentation
The repository documentation SHALL describe the Docker module and container-images scenario as separate layers.

#### Scenario: Read container image CI documentation
- **WHEN** a user reads the repository documentation for container image CI
- **THEN** it SHALL explain that `modules/docker` provides reusable Docker and OCI primitives
- **AND** it SHALL explain that `scenarios/container-images` provides portable image verification and publication functions
- **AND** it SHALL explain that CI-provider workflows own event triggers, changed path selection, and tag-to-image-reference mapping

### Requirement: Container images scenario layout
The repository SHALL place the portable container images scenario under `scenarios/container-images`.

#### Scenario: Locate container images scenario
- **WHEN** a user looks for the container images CI scenario
- **THEN** the scenario SHALL be available under `scenarios/container-images`
- **AND** the scenario SHALL contain its own Dagger module metadata and source code

### Requirement: Scenario test command interface
The repository SHALL expose supported scenario test workflows through the root command interface.

#### Scenario: Run scenario tests
- **WHEN** a user or CI needs to run tests for a scenario with a Dagger test module
- **THEN** the tests SHALL be runnable through the root `Makefile` using an explicit scenario kind and scenario name
- **AND** the target SHALL call the scenario test aggregate function

#### Scenario: Scenario has no tests
- **WHEN** a scenario has no Dagger test module
- **THEN** CI discovery SHALL NOT fail only because that scenario has no tests

### Requirement: Explicit module and scenario command interface
The repository SHALL address modules and scenarios explicitly in root Makefile commands.

#### Scenario: Run module tests
- **WHEN** a user or CI runs tests for a module named `docker`
- **THEN** the command SHALL be `make tests module docker`
- **AND** it SHALL run `modules/docker/tests`

#### Scenario: Run scenario tests
- **WHEN** a user or CI runs tests for a scenario named `container-images`
- **THEN** the command SHALL be `make tests scenario container-images`
- **AND** it SHALL run `scenarios/container-images/tests`

#### Scenario: Reject legacy shorthand test command
- **WHEN** a user runs a legacy module-only shorthand such as `make tests docker`
- **THEN** the Makefile SHALL fail with usage guidance for the explicit command form

### Requirement: Repository-wide Ruff command interface
The repository SHALL lint and format Python code in both modules and scenarios through the root Makefile.

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
