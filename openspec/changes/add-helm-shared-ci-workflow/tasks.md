## 1. Helm And Helm Unittest Module Support

- [x] 1.1 Add a Helm module helper that returns structured chart metadata, reusing the existing chart version and library chart detection behavior, and including chart annotations.
- [x] 1.1a Update the Helm module runtime image API to use `DEFAULT_CONTAINER_USER_ID` and `container_user_id`.
- [x] 1.2 Add `modules/helm-unittest` with public runtime image defaults based on `helmunittest/helm-unittest`.
- [x] 1.3 Implement a Helm unittest module function that runs unit tests for a supplied chart directory.
- [x] 1.4 Ensure Helm dependency update can be applied before lint, template, package, and unittest workflows without leaking provider-specific behavior.
- [x] 1.5 Add Dagger-native Helm module tests for structured metadata detection, including chart name, version, chart type, and annotations.
- [x] 1.6 Add Dagger-native Helm module tests for library chart template skip behavior.
- [x] 1.7 Add Dagger-native Helm unittest module tests for successful unittest execution and failing unittest execution.

## 2. Helm CI Scenario Result Model

- [x] 2.1 Define scenario-owned structured result objects or JSON-compatible records for chart publication results.
- [x] 2.2 Define scenario-owned structured result objects or JSON-compatible records for development publication cleanup results.
- [x] 2.3 Ensure publication and cleanup workflows return deterministic ordered lists of result records rather than dictionaries keyed by chart or artifact identity.
- [x] 2.4 Ensure publication and cleanup results include registry-visible OCI reference fields: `oci_reference`, `oci_registry`, `oci_repository`, `oci_tag`, and `oci_digest` when available.
- [x] 2.5 Ensure result fields use only primitive values and do not expose Helm, Git, or registry helper module object types.
- [x] 2.6 Ensure returned results never include registry credentials or secret-derived values.

## 3. Changed Chart Validation Workflow

- [x] 3.1 Extend `scenarios/helm-ci` to accept caller-provided glob-like chart component roots such as `charts/*` and `libs/*` through repeatable `charts_path` inputs for repository validation.
- [x] 3.2 Implement changed-chart discovery from explicit `base_ref` and `head_ref` inputs using the Git module.
- [ ] 3.3 Implement validation for changed application charts with dependency update, strict lint, template, and auto-detected unittest through `modules/helm-unittest`.
- [ ] 3.4 Implement validation for changed library charts with dependency update, strict lint, template skip, and auto-detected unittest through `modules/helm-unittest`.
- [ ] 3.5 Return successful no-op results when no chart directories changed.
- [ ] 3.6 Add Dagger-native scenario tests for application chart validation, library chart validation, non-chart skips, and no-op changed validation.

## 4. Development Publication Workflow

- [ ] 4.1 Add a scenario function that discovers changed charts relative to caller-provided pull request refs.
- [ ] 4.2 Support invoking development publication from pull request workflows after validation succeeds.
- [ ] 4.3 Compute development package versions by appending caller-provided SemVer build metadata to the chart version, including a stable pull request marker such as `pr.<number>`.
- [ ] 4.4 Package and publish each selected chart to a caller-provided OCI registry destination.
- [ ] 4.5 Return structured publication results for published, skipped, and failed charts, including registry-visible OCI references suitable for cleanup and summaries.
- [ ] 4.6 Add tests for development version calculation and changed dev publication behavior, using a local registry or dry-run path where appropriate.

## 4a. Development Publication Cleanup Workflow

- [ ] 4a.1 Add provider-neutral cleanup support for pull-request development chart versions using OCI registry APIs rather than GitHub Packages APIs.
- [ ] 4a.2 Allow cleanup to select development versions by a caller-provided pull request marker such as `pr.<number>`.
- [ ] 4a.3 Ensure cleanup skips release chart versions and reports deleted, skipped, and failed artifacts as structured results.
- [ ] 4a.4 Support provider workflow retry by accepting explicit cleanup inputs such as registry destination, package or chart scope, and pull request marker.
- [ ] 4a.5 Add a reusable `skopeo`-based module if direct OCI registry API operations require a containerized helper.
- [ ] 4a.6 Add tests for cleanup selection, release-version protection, and retry inputs using a local registry or dry-run path where appropriate.

## 5. Release Publication Workflow

- [ ] 5.1 Add a scenario function that discovers changed charts between caller-provided previous and head refs.
- [ ] 5.2 Add optional metadata path gating so release publication can skip when no matching `Chart.yaml` files changed.
- [ ] 5.3 Package release charts using the version from `Chart.yaml` without appending build metadata.
- [ ] 5.4 Add optional idempotent behavior that skips pushing chart versions already present in the destination registry.
- [ ] 5.5 Detect chart version bumps from changed `Chart.yaml` metadata and publish release charts automatically when the provider workflow invokes the release function after a default-branch merge.
- [ ] 5.6 Create and push chart-scoped release Git tags through the Git module after successful release publication.
- [ ] 5.7 Fail release publication when the target release Git tag already exists.
- [ ] 5.8 Fail release publication when Git credentials cannot create or push the release Git tag.
- [ ] 5.9 Add tests for metadata gating, unchanged no-op behavior, release version publication, already-published skips, release tag creation, existing-tag failure, and tag permission failure where practical.

## 6. Documentation Content Validation

- [ ] 6.1 Add an optional documentation validation path to the Helm CI scenario for caller-selected files or directories inside the repository source.
- [ ] 6.2 Ensure documentation validation does not render or publish the external main documentation site.
- [ ] 6.3 Add tests for missing documentation, valid documentation, and documentation validation disabled behavior.

## 7. Documentation And Consumer Guidance

- [ ] 7.1 Update `scenarios/helm-ci/README.md` with changed validation, dev publication, release publication, unittest, result output, and provider boundary examples.
- [ ] 7.2 Update repository docs for Helm CI usage, including `riftonix/helm-shared` guidance with default branch `master` and chart roots `charts/*` and `libs/*`.
- [ ] 7.3 Document that `helm-shared` documentation is externally published by the main site and that this workflow only validates repository content.
- [ ] 7.4 Document public runtime image defaults and mirror override inputs for Helm, Git, Helm unittest, and any documentation validation runtime, including `container_user_id` naming for new modules.

## 8. Verification

- [ ] 8.1 Run `make tests module helm`.
- [ ] 8.2 Run `make tests module helm-unittest`.
- [ ] 8.3 Run `make tests scenario helm-ci`.
- [ ] 8.4 Run `make lint-check module helm`, `make lint-check module helm-unittest`, and `make lint-check scenario helm-ci`.
- [ ] 8.5 Run `make format-check module helm`, `make format-check module helm-unittest`, and `make format-check scenario helm-ci`.
- [ ] 8.6 Run OpenSpec validation for `add-helm-shared-ci-workflow`.
