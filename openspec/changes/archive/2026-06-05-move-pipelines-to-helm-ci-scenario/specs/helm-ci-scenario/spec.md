## ADDED Requirements

### Requirement: Helm CI scenario verifies one chart
The `scenarios/helm-ci` scenario SHALL verify a Helm chart directory supplied explicitly by the caller.

#### Scenario: Verify one chart
- **WHEN** a caller provides a Helm chart directory to the `helm-verify` function
- **THEN** the scenario SHALL run Helm lint through the Helm module
- **AND** it SHALL run Helm template through the Helm module
- **AND** lint or template failures SHALL fail the scenario function call

#### Scenario: Verify one chart with values
- **WHEN** a caller provides an optional values file or release name
- **THEN** the scenario SHALL pass those inputs to the Helm template operation

### Requirement: Helm CI scenario publishes one chart
The `scenarios/helm-ci` scenario SHALL publish a Helm chart to an OCI registry using destination and version inputs supplied explicitly by the caller.

#### Scenario: Publish one chart
- **WHEN** a caller provides a chart directory, OCI registry URL, and chart version to the `helm-publish` function
- **THEN** the scenario SHALL package and push the chart through the Helm module
- **AND** publication failures SHALL fail the scenario function call

#### Scenario: Publish with registry credentials
- **WHEN** a caller provides registry username and password inputs
- **THEN** the scenario SHALL authenticate through the Helm module before pushing
- **AND** the scenario SHALL NOT expose registry secrets in returned output

### Requirement: Helm CI scenario verifies changed charts
The `scenarios/helm-ci` scenario SHALL verify changed Helm chart directories selected through provider-neutral Git and path inputs.

#### Scenario: Verify changed chart directories
- **WHEN** a caller provides a repository source, target branch, and chart path to the `helm-verify-changed-charts` function
- **THEN** the scenario SHALL ask the Git module for changed directories since the merge base with the target branch
- **AND** it SHALL run Helm verification for each changed chart directory
- **AND** it SHALL return an empty list when no chart directories changed

#### Scenario: Verify changed library directories
- **WHEN** a caller provides a library path as an additional diff root
- **THEN** the scenario SHALL include changed directories under that library path when selecting charts to verify

#### Scenario: Skip charts without required metadata
- **WHEN** a changed chart directory has no chart name or version in `Chart.yaml`
- **THEN** the scenario SHALL skip that chart directory
- **AND** it SHALL include a returned message explaining that required metadata is missing

### Requirement: Helm CI scenario remains CI-provider portable
The `scenarios/helm-ci` scenario SHALL avoid CI-provider-specific trigger, branch, tag, and changed-path policy.

#### Scenario: Caller controls diff inputs
- **WHEN** a CI workflow wants to verify changed charts
- **THEN** the workflow SHALL provide target branch and path inputs to the scenario
- **AND** the scenario SHALL NOT inspect GitHub Actions, GitLab CI, or other provider event environment variables

#### Scenario: Caller controls publish timing
- **WHEN** a CI workflow decides whether publication should run
- **THEN** the scenario SHALL only publish when called with explicit publish inputs
- **AND** the scenario SHALL NOT parse provider-specific release events

### Requirement: Helm CI scenario hides implementation module object types
The `scenarios/helm-ci` scenario SHALL compose implementation modules internally while exposing a module-neutral public API.

#### Scenario: Compose scenario with independent Helm or Git module versions
- **WHEN** a caller uses the released Helm CI scenario and also depends on different released Helm or Git module versions in their own scenario
- **THEN** the Helm CI scenario public API SHALL remain usable through stable inputs and outputs
- **AND** the Helm CI scenario SHALL NOT require the caller to pass or consume Helm or Git module object types

### Requirement: Helm CI scenario documents CI integration pattern
The `scenarios/helm-ci` README SHALL describe how CI systems call Helm verification and publication workflows.

#### Scenario: Read scenario documentation
- **WHEN** a user reads the Helm CI scenario README
- **THEN** it SHALL show examples using `dagger -m ./scenarios/helm-ci`
- **AND** it SHALL explain that CI provider workflows own event rules, branch selection, changed-path selection, and publish timing

### Requirement: Helm CI scenario has Dagger-native tests
The `scenarios/helm-ci` scenario SHALL have Dagger-native tests that validate public scenario behavior through its public API.

#### Scenario: Run Helm CI scenario tests
- **WHEN** a user or CI runs `make tests scenario helm-ci`
- **THEN** the scenario test module SHALL run its aggregate `all` function
- **AND** the tests SHALL call the scenario through a local Dagger dependency

#### Scenario: Test changed chart verification
- **WHEN** changed chart verification behavior is implemented or moved
- **THEN** the same implementation step SHALL add or update Dagger-native tests for that behavior
- **AND** the tests SHALL verify merge-base diff behavior so base-branch drift does not trigger unrelated chart checks
