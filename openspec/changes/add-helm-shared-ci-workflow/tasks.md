## 1. Helm And Helm Unittest Module Support

- [x] 1.1 Add a Helm module helper that returns structured chart metadata, reusing the existing chart version and library chart detection behavior, and including chart annotations.
- [x] 1.1a Update the Helm module runtime image API to use `DEFAULT_CONTAINER_USER_ID` and `container_user_id`.
- [x] 1.2 Add `modules/helm-unittest` with public runtime image defaults based on `helmunittest/helm-unittest`.
- [x] 1.3 Implement a Helm unittest module function that runs unit tests for a supplied chart directory.
- [x] 1.4 Ensure Helm dependency update can be applied before lint, template, package, and unittest workflows without leaking provider-specific behavior.
- [x] 1.5 Add Dagger-native Helm module tests for structured metadata detection, including chart name, version, chart type, and annotations.
- [x] 1.6 Add Dagger-native Helm module tests for library chart template skip behavior.
- [x] 1.7 Add Dagger-native Helm unittest module tests for successful unittest execution and failing unittest execution.
- [x] 1.8 Add optional repeatable suite file filters to the Helm unittest module while preserving unfiltered and color behavior.
- [x] 1.9 Add Dagger-native Helm unittest tests for one and multiple filters, excluded valid suites, and selected failures.
- [x] 1.10 Move default suite patterns and suite discovery into the Helm unittest module and use the defaults when `test` is called without filters.
- [x] 1.11 Add Dagger-native Helm unittest tests for default discovery, custom discovery, empty selection, and default filtered execution.

## 2. Helm CI Scenario Result Model

- [x] 2.1 Define scenario-owned structured result objects or JSON-compatible records for chart publication results.
- [x] 2.2 Ensure publication results use primitive fields and include registry-visible OCI reference fields when available.
- [x] 2.5 Ensure result fields use only primitive values and do not expose Helm, Git, or registry helper module object types.
- [x] 2.6 Ensure returned results never include registry credentials or secret-derived values.

## 3. Changed Chart Validation Workflow

- [x] 3.1 Extend `scenarios/helm-ci` to accept caller-provided glob-like chart component roots such as `charts/*` and `libs/*` through repeatable `charts_path` inputs for repository validation.
- [x] 3.2 Define CI-side changed-chart discovery using the Git module's `get_changed_components` function with explicit `base_ref`, `head_ref`, and chart roots.
- [x] 3.3 Implement single-chart validation with dependency update, strict lint, conditional template execution for non-library charts, and auto-detected unittest through `modules/helm-unittest`.
- [x] 3.4 Move changed-chart fan-out and no-op handling to the provider workflow matrix; the scenario validates only the selected chart directory.
- [x] 3.5 Add Dagger-native scenario tests for application and library chart validation and rejection of non-chart directories.
- [x] 3.6 Restrict Helm CI unittest discovery to `*_test.yaml` and `*_test.yml` defaults and allow callers to replace them with repeatable suite file patterns.
- [x] 3.7 Add Dagger-native scenario tests for unrelated YAML, default and custom patterns, empty selection, skipped execution, and selected failures.
- [x] 3.8 Delegate Helm CI suite discovery and default pattern ownership to the Helm unittest module.

## 6. Release Publication Workflow

- [x] 6.1 Change `publish_chart` into the single release publication entrypoint that publishes one chart and pushes its Git release tag in one Dagger call.
- [x] 6.2 Keep scenario-level `source` as the Git repository directory and add optional `chart_source: dagger.Directory | None` to `verify_chart` and `publish_chart`, resolving the chart as `chart_source or self.source`.
- [x] 6.3 Use the resolved chart source for Helm and Helm unittest operations while always using scenario-level `source` for Git operations.
- [x] 6.4 Package the release chart using the version from `Chart.yaml` by default, allow an optional explicit version override, and run dependency update by default with an opt-out input.
- [x] 6.5 Compute a chart-scoped release tag from caller-provided `git_tag_prefix` and the effective chart version, for example `charts/appchart/v1.2.3`.
- [x] 6.6 Accept an OCI base URL plus registry and Git authentication inputs on `publish_chart`, preserve `git_tag_prefix` as the chart repository path, publish the chart, and create and push the release tag through the Git module within the same function invocation.
- [x] 6.7 Check the target release tag before publication, return a successful no-op when it already exists, and create and push a missing tag only after successful chart publication.
- [x] 6.8 Fail when Git credentials cannot create or push the release tag, without falling back to provider-specific APIs.
- [x] 6.9 Add tests for chart source fallback and override behavior, release version publication, release tag calculation and push, existing-tag no-op before publication, and tag permission failure where practical.
- [x] 6.10 Rename registry publication inputs to `registry_login` and `registry_password`, and delegate post-publication tag creation and push to the Git module's `ensure_pushed_tag` function within the same call.

## 7. Documentation Content Validation

- [ ] 7.1 Add an optional documentation validation path to the Helm CI scenario for caller-selected files or directories inside the repository source.
- [ ] 7.2 Ensure documentation validation does not render or publish the external main documentation site.
- [ ] 7.3 Add tests for missing documentation, valid documentation, and documentation validation disabled behavior.

## 8. Documentation And Consumer Guidance

- [ ] 8.1 Update `scenarios/helm-ci/README.md` with changed validation, release publication, unittest, result output, and provider boundary examples.
- [ ] 8.2 Update repository docs for Helm CI usage, including `riftonix/helm-shared` guidance with default branch `master` and chart roots `charts/*` and `libs/*`.
- [ ] 8.3 Document that `helm-shared` documentation is externally published by the main site and that this workflow only validates repository content.
- [ ] 8.4 Document public runtime image defaults and mirror override inputs for Helm, Git, Helm unittest, and any documentation validation runtime, including `container_user_id` naming for new modules.

## 9. Verification

- [x] 9.1 Run `make tests module helm`.
- [x] 9.2 Run `make tests module helm-unittest`.
- [ ] 9.3 Run `make tests scenario helm-ci`.
- [ ] 9.4 Run `make lint-check module helm`, `make lint-check module helm-unittest`, and `make lint-check scenario helm-ci`.
- [ ] 9.5 Run `make format-check module helm`, `make format-check module helm-unittest`, and `make format-check scenario helm-ci`.
- [ ] 9.6 Run OpenSpec validation for `add-helm-shared-ci-workflow`.
