## ADDED Requirements

### Requirement: Helm CI scenario repository layout
The repository SHALL place Helm CI orchestration under `scenarios/helm-ci`.

#### Scenario: Locate Helm CI scenario
- **WHEN** a user looks for Helm CI workflow implementation
- **THEN** the implementation SHALL be available under `scenarios/helm-ci`
- **AND** the scenario directory SHALL contain its own Dagger module metadata and source code
- **AND** the repository SHALL NOT keep the Helm CI workflow implementation under `modules/pipelines`

#### Scenario: Run Helm CI scenario tests
- **WHEN** a user or CI needs to run Helm CI scenario tests
- **THEN** the tests SHALL be runnable with `make tests scenario helm-ci`
- **AND** the command SHALL call the scenario test aggregate function

### Requirement: Repository documentation includes Helm CI scenario
The repository documentation SHALL describe Helm CI orchestration as a scenario.

#### Scenario: Read Helm CI documentation
- **WHEN** a user reads the repository documentation for Helm CI checks
- **THEN** it SHALL explain that `modules/helm` provides reusable Helm primitives
- **AND** it SHALL explain that `scenarios/helm-ci` provides portable Helm verification and publication workflows
- **AND** it SHALL explain that CI-provider workflows own event triggers, branch selection, changed path selection, and publish timing

#### Scenario: Read root repository overview
- **WHEN** a user opens the root README
- **THEN** the module list SHALL NOT include `pipelines`
- **AND** the scenario list SHALL include `helm-ci`
