## ADDED Requirements

### Requirement: Helm CI scenario validates changed chart repositories
The `scenarios/helm-ci` scenario SHALL provide a provider-neutral validation workflow for changed Helm chart repositories using explicit repository source, refs, and chart roots supplied by the caller.

#### Scenario: Validate changed charts from application and library roots
- **WHEN** a caller invokes the changed repository validation workflow with `source`, `base_ref`, `head_ref`, and chart roots such as `charts/*` and `libs/*`
- **THEN** the scenario SHALL discover changed chart directories under those roots using provider-neutral Git inputs
- **AND** it SHALL validate each discovered chart directory that contains a `Chart.yaml`
- **AND** it SHALL return a successful no-op result when no chart directories changed

#### Scenario: Validate application chart
- **WHEN** a changed chart has no `type: library` value in `Chart.yaml`
- **THEN** the scenario SHALL run Helm dependency update when applicable
- **AND** it SHALL run Helm lint in strict mode
- **AND** it SHALL run Helm template for that chart
- **AND** a lint or template failure SHALL fail the validation workflow

#### Scenario: Validate library chart
- **WHEN** a changed chart has `type: library` in `Chart.yaml`
- **THEN** the scenario SHALL run Helm dependency update when applicable
- **AND** it SHALL run Helm lint in strict mode
- **AND** it SHALL skip Helm template for that chart
- **AND** it SHALL report the template step as skipped because the chart is a library chart

#### Scenario: Ignore non-chart changed directories
- **WHEN** a changed directory under a configured root does not contain `Chart.yaml`
- **THEN** the scenario SHALL skip that directory
- **AND** it SHALL include a structured skip result identifying the path and reason

### Requirement: Helm CI scenario runs optional Helm unittest checks
The `scenarios/helm-ci` scenario SHALL support Helm unittest validation by composing the dedicated Helm unittest module for charts that contain test suites while allowing charts without tests to pass validation.

#### Scenario: Run unittest for chart with tests directory
- **WHEN** unittest validation is enabled and a chart directory contains a `tests` directory
- **THEN** the scenario SHALL run Helm unittest for that chart through `modules/helm-unittest`
- **AND** a unittest failure SHALL fail the validation workflow

#### Scenario: Skip unittest for chart without tests directory
- **WHEN** unittest validation is enabled and a chart directory does not contain a `tests` directory
- **THEN** the scenario SHALL skip Helm unittest for that chart
- **AND** it SHALL report the unittest step as skipped without failing validation

#### Scenario: Caller configures Helm unittest module runtime image
- **WHEN** a caller configures Helm unittest validation through the Helm CI scenario
- **THEN** the scenario SHALL expose prefixed public runtime image inputs for the `modules/helm-unittest` runtime
- **AND** callers SHALL be able to override registry, repository, tag, and container user values through inputs such as `helm_unittest_image_registry`, `helm_unittest_image_repository`, `helm_unittest_image_tag`, and `helm_unittest_container_user_id` without changing provider workflow logic

### Requirement: Helm CI scenario publishes development chart versions
The `scenarios/helm-ci` scenario SHALL publish development versions of changed charts using caller-provided registry settings and version metadata.

#### Scenario: Publish changed dev charts
- **WHEN** a caller invokes development publication with repository source, base ref, head ref, chart roots, registry destination, credentials, and a build metadata suffix
- **THEN** the scenario SHALL discover changed chart directories relative to the caller-provided base ref
- **AND** it SHALL package each changed chart with version `<chart-version>+<build-metadata-suffix>`
- **AND** it SHALL push each package to the caller-provided OCI registry destination
- **AND** it SHALL return structured publication results for every selected chart

#### Scenario: Dev publication does not decide manual policy
- **WHEN** a provider workflow wants development publication to be manual or optional
- **THEN** the provider workflow SHALL decide whether to call the development publication function
- **AND** the scenario SHALL NOT inspect provider-specific manual action variables

#### Scenario: No changed dev charts
- **WHEN** development publication finds no changed chart directories
- **THEN** the scenario SHALL return a successful no-op publication result
- **AND** it SHALL NOT attempt registry login or chart push unless required by implementation order after chart selection

### Requirement: Helm CI scenario publishes release chart versions
The `scenarios/helm-ci` scenario SHALL publish release versions of changed charts after default-branch merges using explicit refs and caller-provided registry settings.

#### Scenario: Publish changed release charts
- **WHEN** a caller invokes release publication with repository source, previous ref, head ref, chart roots, registry destination, and credentials
- **THEN** the scenario SHALL discover changed chart directories between the previous ref and head ref
- **AND** it SHALL package each selected chart using the version already declared in `Chart.yaml`
- **AND** it SHALL push each package to the caller-provided OCI registry destination
- **AND** it SHALL return structured publication results for every selected chart

#### Scenario: Gate release publication by chart metadata changes
- **WHEN** a caller provides metadata path filters such as `charts/*/Chart.yaml` and `libs/*/Chart.yaml`
- **THEN** the release publication workflow SHALL skip publication when no matching metadata files changed
- **AND** it SHALL return a successful no-op result explaining that release metadata did not change

#### Scenario: Skip already published release version
- **WHEN** idempotent release publication is enabled and the destination registry already contains a chart version
- **THEN** the scenario SHALL skip pushing that chart
- **AND** it SHALL report the chart as already published instead of failing

#### Scenario: Provider controls release branch policy
- **WHEN** a provider workflow wants release publication only on a default branch such as `master`
- **THEN** the provider workflow SHALL decide whether to call the release publication function
- **AND** the scenario SHALL NOT hardcode `main`, `master`, or provider-specific branch variables

### Requirement: Helm CI scenario returns structured chart workflow results
The `scenarios/helm-ci` scenario SHALL return structured results for multi-chart validation and publication workflows.

#### Scenario: Validation result contains chart step statuses
- **WHEN** a validation workflow checks one or more chart directories
- **THEN** each chart result SHALL include chart path, chart name when available, chart version when available, workflow action, status, and message
- **AND** each chart result SHALL distinguish passed, failed, and skipped steps without requiring callers to parse shell output

#### Scenario: Publication result contains package references
- **WHEN** a publication workflow packages or pushes one or more charts
- **THEN** each publication result SHALL include chart path, chart name, chart version, published version, package file name when available, destination OCI reference, status, and message
- **AND** registry credentials SHALL NOT appear in any returned result

### Requirement: Helm CI scenario validates repository documentation content without site publication
The `scenarios/helm-ci` scenario SHALL support optional repository documentation validation for chart repositories without rendering or publishing the external main documentation site.

#### Scenario: Validate chart documentation content
- **WHEN** documentation validation is enabled for a chart repository
- **THEN** the scenario SHALL validate caller-selected documentation files or directories inside the repository source
- **AND** it SHALL fail when required documentation content is missing or invalid according to the configured validation mode

#### Scenario: Skip external site rendering
- **WHEN** documentation validation runs for `helm-shared` or another component repository whose documentation is imported by an external main site
- **THEN** the scenario SHALL NOT render the external main site
- **AND** it SHALL NOT publish documentation artifacts or manage provider deployment state

### Requirement: Helm CI scenario supports the helm-shared integration contract
The `scenarios/helm-ci` scenario SHALL expose inputs and behavior suitable for the `riftonix/helm-shared` repository while remaining reusable for other Helm chart repositories.

#### Scenario: Validate helm-shared pull request
- **WHEN** a GitHub Actions workflow in `riftonix/helm-shared` calls the validation workflow for a pull request targeting `master`
- **THEN** the workflow can pass explicit refs and chart roots `charts/*` and `libs/*`
- **AND** the scenario SHALL validate changed charts without reading GitHub-specific environment variables

#### Scenario: Publish helm-shared release charts
- **WHEN** a GitHub Actions workflow in `riftonix/helm-shared` calls release publication after a merge to `master`
- **THEN** the workflow can pass explicit previous and head refs, chart roots `charts/*` and `libs/*`, registry destination, and credentials
- **AND** the scenario SHALL publish changed chart versions without hardcoding the repository name or provider
