## ADDED Requirements

### Requirement: Helm CI scenario validates changed chart repositories
The `scenarios/helm-ci` scenario SHALL provide a provider-neutral validation workflow for changed Helm chart repositories using explicit repository source, refs, and glob-like chart component roots supplied by the caller.

#### Scenario: Validate changed charts from application and library roots
- **WHEN** a caller invokes the changed repository validation workflow with `source`, `base_ref`, `head_ref`, and repeatable `charts_path` values such as `charts/*` and `libs/*`
- **THEN** the scenario SHALL pass those chart component roots to the Git module to discover changed chart directories using provider-neutral Git inputs
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

### Requirement: Helm CI scenario auto-detects Helm unittest checks
The `scenarios/helm-ci` scenario SHALL support Helm unittest validation by composing the dedicated Helm unittest module for charts that contain selected test suites while allowing charts without selected tests to pass validation. The Helm unittest module SHALL own default suite discovery, while the scenario SHALL allow callers to replace the module defaults with repeatable `unittest_suite_files` glob patterns.

#### Scenario: Run unittest for chart with suite files
- **WHEN** a chart directory contains Helm unittest suite files matching the effective suite file patterns
- **THEN** the scenario SHALL use `modules/helm-unittest` to discover the selected suites
- **AND** it SHALL run Helm unittest for that chart through the same module
- **AND** it SHALL pass the effective suite file patterns to the module
- **AND** a unittest failure SHALL fail the validation workflow

#### Scenario: Skip unittest for chart without suite files
- **WHEN** a chart directory does not contain Helm unittest suite files matching the effective suite file patterns
- **THEN** the scenario SHALL skip Helm unittest for that chart
- **AND** it SHALL report the unittest step as skipped without failing validation

#### Scenario: Ignore unrelated YAML files
- **WHEN** a chart contains YAML files under `tests/` that do not match the Helm unittest module defaults
- **THEN** those files SHALL NOT enable Helm unittest execution
- **AND** they SHALL NOT be passed to Helm unittest as suite files

#### Scenario: Caller selects unittest suites
- **WHEN** a caller supplies one or more `unittest_suite_files` glob patterns
- **THEN** the scenario SHALL replace the default suite file patterns with the supplied patterns
- **AND** it SHALL pass the same patterns to the Helm unittest module for discovery and execution

#### Scenario: Caller selects no unittest suites
- **WHEN** a caller supplies an explicit empty `unittest_suite_files` list
- **THEN** the scenario SHALL skip Helm unittest execution
- **AND** it SHALL report that no suite files matched the configured patterns

#### Scenario: Caller configures Helm unittest module runtime image
- **WHEN** a caller configures Helm CI runtime images
- **THEN** the scenario SHALL expose prefixed public runtime image inputs for the `modules/helm-unittest` runtime
- **AND** callers SHALL be able to override registry, repository, tag, and container user values through inputs such as `helm_unittest_image_registry`, `helm_unittest_image_repository`, `helm_unittest_image_tag`, and `helm_unittest_container_user_id` without changing provider workflow logic

### Requirement: Helm CI scenario publishes release chart versions
The `scenarios/helm-ci` scenario SHALL expose `publish_chart` as the single release publication entrypoint for one caller-selected chart. One `publish_chart` invocation SHALL publish the chart and create and push its Git release tag without requiring additional Dagger calls.

#### Scenario: Resolve repository and chart sources
- **WHEN** a caller constructs Helm CI with scenario-level `source` and invokes `verify_chart` or `publish_chart` with an optional `chart_source`
- **THEN** the scenario SHALL resolve the chart directory as `chart_source or self.source`
- **AND** it SHALL use the resolved chart directory for Helm and Helm unittest operations
- **AND** it SHALL always use scenario-level `source` as the Git repository directory for release tag operations

#### Scenario: Use scenario source as chart fallback
- **WHEN** a caller omits `chart_source`
- **THEN** `verify_chart` and `publish_chart` SHALL treat scenario-level `source` as the chart directory
- **AND** single-chart repository calls SHALL remain possible without a separate chart directory input

#### Scenario: Publish one release chart and tag in one call
- **WHEN** a caller invokes `publish_chart` with a repository source, optional chart source, Git tag prefix, OCI base URL and credentials, and Git credentials
- **THEN** the function SHALL read the chart version from the resolved chart source's `Chart.yaml`
- **AND** it SHALL use that version unless the caller supplies an explicit `version` override
- **AND** it SHALL run Helm dependency update by default unless the caller sets `with_dependency_update` to false
- **AND** it SHALL append the normalized `git_tag_prefix` to `oci_base_url` as the chart repository path
- **AND** it SHALL package and push the effective version without appending build metadata
- **AND** it SHALL compute the chart-scoped release tag
- **AND** it SHALL create and push that Git tag through the Git module before the function returns
- **AND** it SHALL authenticate to the registry host derived from the resulting OCI URL unless the caller supplies an explicit registry address
- **AND** it SHALL expose registry credentials as `registry_login` and `registry_password`
- **AND** it SHALL require `registry_login` and `registry_password` to be supplied together
- **AND** all publication and tagging operations SHALL occur within the same `publish_chart` Dagger call

#### Scenario: Compute chart-scoped release tag
- **WHEN** `publish_chart` receives a Git tag prefix such as `charts/appchart` and the selected chart declares version `1.2.3`
- **THEN** the release Git tag SHALL be `charts/appchart/v1.2.3`
- **AND** the tag SHALL identify both the chart component and release version

#### Scenario: Create release Git tag after successful publication
- **WHEN** release publication succeeds for the selected chart
- **THEN** the scenario SHALL create and push a chart-scoped Git tag through the Git module
- **AND** the tag SHALL include the chart scope and version, for example `charts/appchart/v1.2.3` or `libs/common/v0.4.0`
- **AND** it SHALL NOT create or push the tag before chart publication succeeds

#### Scenario: Skip when release Git tag already exists
- **WHEN** `publish_chart` detects that the target chart-scoped Git tag already exists locally or on the configured remote
- **THEN** the release workflow SHALL return a successful no-op result
- **AND** it SHALL report that the release tag already exists
- **AND** it SHALL perform this check before registry login and before pushing the chart package
- **AND** it SHALL NOT publish the chart or create or push a duplicate tag

#### Scenario: Fail when release Git tag cannot be pushed
- **WHEN** the scenario attempts to create or push a release Git tag through the Git module and the provided Git credentials do not allow it
- **THEN** the release workflow SHALL fail
- **AND** it SHALL report the Git tag push failure without falling back to provider-specific APIs

#### Scenario: Provider controls release branch policy
- **WHEN** a provider workflow wants release publication only on a default branch such as `master`
- **THEN** the provider workflow SHALL decide whether to call the release publication function
- **AND** the scenario SHALL NOT hardcode `main`, `master`, or provider-specific branch variables

### Requirement: Helm CI scenario returns structured publication results
The `scenarios/helm-ci` scenario SHALL return a structured publication result for the single release chart selected by `publish_chart`.

#### Scenario: Publication result contains package references
- **WHEN** `publish_chart` packages and pushes a chart
- **THEN** its publication result SHALL include chart path, chart name, chart version, published version, package file name, release Git tag, status, and message
- **AND** it SHALL include registry-visible OCI fields when available
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
- **THEN** the provider workflow SHALL select one chart per job and pass repository `source`, optional `chart_source`, `git_tag_prefix`, OCI base URL, registry credentials, and Git credentials to `publish_chart`
- **AND** one `publish_chart` Dagger call SHALL publish the selected chart version and create its chart-scoped release Git tag without hardcoding the repository name or provider
