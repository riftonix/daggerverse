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
The Helm unittest module SHALL discover and run selected Helm unittest suites against the chart directory supplied through `source`. It SHALL own the default suite file patterns `tests/**/*_test.yaml` and `tests/**/*_test.yml` so direct callers and composing scenarios use the same selection behavior.

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

#### Scenario: Caller filters suite files
- **WHEN** a caller supplies one or more suite file glob patterns
- **THEN** the module SHALL pass each pattern to Helm unittest through a separate `-f` option
- **AND** it SHALL run only suites selected by those patterns

#### Scenario: Caller omits suite file filters
- **WHEN** a caller omits suite file patterns
- **THEN** the module SHALL use `tests/**/*_test.yaml` and `tests/**/*_test.yml`
- **AND** it SHALL pass both default patterns to Helm unittest through separate `-f` options

#### Scenario: Caller selects no suite files
- **WHEN** a caller supplies an explicit empty suite file pattern list
- **THEN** the module SHALL report that no suites are selected through its discovery function
- **AND** a composing workflow SHALL be able to skip test execution

#### Scenario: Discover selected suites
- **WHEN** a caller invokes suite discovery with omitted, custom, or empty suite file patterns
- **THEN** the module SHALL resolve the effective patterns using the same rules as test execution
- **AND** it SHALL return whether at least one chart file matches those patterns

#### Scenario: Suite filters preserve color output
- **WHEN** a caller enables color output and supplies suite file patterns
- **THEN** the module SHALL pass both the suite filters and the color option to Helm unittest

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
- **AND** they SHALL cover one and multiple suite file filters
- **AND** they SHALL prove that a valid suite outside the selected patterns is not executed
