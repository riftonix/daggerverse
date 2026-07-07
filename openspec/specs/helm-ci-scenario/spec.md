# helm-ci-scenario Specification

## Purpose
Describe the current Helm CI scenario behavior for portable chart verification,
changed-chart verification, and OCI chart publication.
## Requirements
### Requirement: Helm CI scenario verifies one chart
The `scenarios/helm-ci` scenario SHALL verify a Helm chart directory supplied explicitly by the caller through the public input named `source`.

#### Scenario: Verify one chart
- **WHEN** a caller provides a Helm chart directory to the `helm-verify` function as `source`
- **THEN** the scenario SHALL run Helm lint through the Helm module
- **AND** it SHALL run Helm template through the Helm module
- **AND** lint or template failures SHALL fail the scenario function call

#### Scenario: Verify one chart with values
- **WHEN** a caller provides an optional values file or release name
- **THEN** the scenario SHALL pass those inputs to the Helm template operation

### Requirement: Helm CI scenario publishes one chart
The `scenarios/helm-ci` scenario SHALL publish a Helm chart supplied through the public input named `source` to an OCI registry using destination and version inputs supplied explicitly by the caller.

#### Scenario: Publish one chart
- **WHEN** a caller provides a chart directory as `source`, OCI registry URL, and chart version to the `helm-publish` function
- **THEN** the scenario SHALL package and push the chart through the Helm module
- **AND** publication failures SHALL fail the scenario function call

#### Scenario: Publish with registry credentials
- **WHEN** a caller provides registry username and password inputs
- **THEN** the scenario SHALL authenticate through the Helm module before pushing
- **AND** the scenario SHALL NOT expose registry secrets in returned output

### Requirement: Helm CI scenario verifies changed charts
The `scenarios/helm-ci` scenario SHALL verify changed Helm chart directories selected through provider-neutral Git and path inputs, with the repository checkout supplied through the public input named `source`.

#### Scenario: Verify changed chart directories
- **WHEN** a caller provides a repository source, target branch, and chart path to the `helm-verify-changed-charts` function
- **THEN** the scenario SHALL ask the Git module for changed directories since the merge base with the target branch
- **AND** it SHALL run Helm verification for each changed chart directory
- **AND** it SHALL return an empty list when no chart directories changed
- **AND** `charts_path` SHALL remain a secondary path inside the repository source rather than a replacement for `source`

#### Scenario: Verify changed library directories
- **WHEN** a caller provides a library path as an additional diff root
- **THEN** the scenario SHALL include changed directories under that library path when selecting charts to verify
- **AND** `libs_path` SHALL remain a secondary path inside the repository source rather than a replacement for `source`

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

### Requirement: Helm CI Runtime Image Inputs
The Helm CI scenario SHALL expose runtime image inputs for the Helm and Git modules it composes.

#### Scenario: Caller configures Helm runtime image
- **WHEN** a caller invokes Helm chart verification or publication through the Helm CI scenario
- **THEN** the scenario SHALL use `helm_image_registry`, `helm_image_repository`, `helm_image_tag`, and `helm_container_user_id` when creating the Helm module

#### Scenario: Caller configures Git runtime image
- **WHEN** a caller invokes changed-chart verification through the Helm CI scenario
- **THEN** the scenario SHALL use `git_image_registry`, `git_image_repository`, `git_image_tag`, and `git_container_user_id` when creating the Git module

#### Scenario: Single-chart workflow does not require Git image inputs
- **WHEN** a caller invokes `helm-verify` or `helm-publish` for one chart directory
- **THEN** Git runtime image inputs SHALL remain available on the scenario API
- **AND** the scenario SHALL NOT invoke the Git module for those operations

#### Scenario: Runtime inputs do not expose module object types
- **WHEN** callers configure Helm CI runtime images
- **THEN** they SHALL pass primitive image input values
- **AND** the scenario SHALL NOT require callers to pass Helm or Git module object values
