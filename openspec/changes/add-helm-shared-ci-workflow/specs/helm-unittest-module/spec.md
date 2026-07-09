## ADDED Requirements

### Requirement: Helm unittest module wraps the public helm-unittest runtime
The repository SHALL provide a reusable `modules/helm-unittest` Dagger module for running Helm chart unit tests with the public `helmunittest/helm-unittest` container image by default.

#### Scenario: Construct Helm unittest module with public defaults
- **WHEN** a caller constructs the Helm unittest module with a chart directory as `source`
- **THEN** the module SHALL use a public `helmunittest/helm-unittest` runtime image by default
- **AND** the module SHALL expose `image_registry`, `image_repository`, `image_tag`, and `container_user_id` inputs for runtime image overrides

#### Scenario: Use mirrored Helm unittest runtime image
- **WHEN** a caller overrides the Helm unittest runtime image inputs
- **THEN** the module SHALL run Helm unittest from the configured registry, repository, tag, and container user values
- **AND** the public function behavior SHALL remain unchanged

### Requirement: Helm unittest module runs chart unit tests
The Helm unittest module SHALL run Helm unittest against the chart directory supplied through `source`.

#### Scenario: Run unit tests for chart
- **WHEN** a caller invokes the Helm unittest run function with a chart directory containing Helm unittest suites
- **THEN** the module SHALL execute Helm unittest for that chart
- **AND** it SHALL return command output on success

#### Scenario: Fail on unit test failure
- **WHEN** Helm unittest reports a failed suite or test
- **THEN** the module function SHALL fail the Dagger call
- **AND** the failure output SHALL identify the failed Helm unittest command output

#### Scenario: Caller controls color output
- **WHEN** a caller chooses whether color output is enabled
- **THEN** the module SHALL pass the corresponding Helm unittest option to the runtime command

### Requirement: Helm unittest module remains reusable outside Helm CI
The Helm unittest module SHALL be usable directly by downstream Dagger callers and by scenarios without requiring Helm CI scenario types.

#### Scenario: Direct module call
- **WHEN** a caller invokes `modules/helm-unittest` directly for a chart directory
- **THEN** the caller SHALL be able to run unit tests without constructing `scenarios/helm-ci`

#### Scenario: Scenario composition hides module object types
- **WHEN** a scenario composes the Helm unittest module internally
- **THEN** the scenario public API SHALL expose primitive inputs and scenario-owned results
- **AND** it SHALL NOT require callers to pass or consume Helm unittest module object types

### Requirement: Helm unittest module has Dagger-native tests
The Helm unittest module SHALL have neighboring Dagger-native tests that validate its public API.

#### Scenario: Run Helm unittest module tests
- **WHEN** a user or CI runs `make tests module helm-unittest`
- **THEN** the Helm unittest test module SHALL run its aggregate `all` function
- **AND** the tests SHALL call the parent Helm unittest module through a local Dagger dependency

#### Scenario: Test successful and failing suites
- **WHEN** Helm unittest module tests run
- **THEN** they SHALL cover a successful chart unittest suite
- **AND** they SHALL cover a failing chart unittest suite that produces a Dagger call failure
