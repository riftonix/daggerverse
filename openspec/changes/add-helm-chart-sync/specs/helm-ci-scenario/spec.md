# Helm CI Scenario Delta Specification

## ADDED Requirements

### Requirement: Helm CI scenario chart sync configuration
The system SHALL read chart sync configuration from the YAML file at `config_path` in `source` (default `updatecli/values.yaml`), and the pin of each component from `<config directory>/pins/<component id>.json`. The configuration SHALL define the upstream registry, the default version filter, shared exclusions, shared rewrite rules, the repository `home` URL, and a map of components keyed by component ID. A pin SHALL record the synchronized upstream `version` and OCI manifest `digest`.

#### Scenario: Component uses defaults
- **GIVEN** a component `common` declared as an empty entry
- **WHEN** the caller runs any chart sync function
- **THEN** the scenario SHALL treat `libs/common` as the component directory, `nuc-common` as the upstream chart name, and `upstream.versionfilter` as the version filter
- **AND** it SHALL read the pin from `updatecli/pins/common.json`

#### Scenario: Component overrides defaults
- **GIVEN** a component that declares `path`, `upstream`, `versionfilter`, `exclude`, or `rewrite`
- **WHEN** the scenario synchronizes the component
- **THEN** `path`, `upstream`, and `versionfilter` SHALL replace the defaults
- **AND** `exclude` SHALL be added to `upstream.exclude`
- **AND** `rewrite` rules SHALL be applied after the shared rules

#### Scenario: Caller selects components
- **GIVEN** a caller passes the `components` input with one or more component IDs
- **WHEN** the caller runs any chart sync function
- **THEN** the scenario SHALL process only the selected components
- **AND** an omitted or empty `components` input SHALL select every component

### Requirement: Helm CI scenario chart sync configuration validation
The system SHALL validate the chart sync configuration and pins before running any pipeline, and SHALL fail with one message that names every invalid item.

#### Scenario: Missing configuration values
- **GIVEN** a configuration without `upstream.registry`, `upstream.versionfilter`, `home`, or `components`
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name each missing key

#### Scenario: Unsafe component
- **GIVEN** a component whose ID does not match `[a-z0-9][a-z0-9-]*`, or whose `path` is not `charts/<name>` or `libs/<name>`
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name the component

#### Scenario: Missing or invalid pin
- **GIVEN** a component whose pin file is missing, is a symbolic link, or lacks a semantic `version` or a `sha256` `digest`
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name the component

#### Scenario: Unsupported version filter
- **GIVEN** a version filter that is not a space-separated list of `=`, `>`, `>=`, `<`, or `<=` comparisons with `MAJOR.MINOR.PATCH` versions
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name the component and filter

#### Scenario: Unknown selected component
- **GIVEN** a caller selects a component ID that the configuration does not declare
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name the unknown ID

### Requirement: Helm CI scenario chart sync component independence
The system SHALL treat each component as one independent synchronization unit with its own pipeline, working branch, and pull request, and SHALL NOT encode any order between components.

#### Scenario: One component fails
- **GIVEN** one selected component cannot be synchronized
- **WHEN** the caller runs the pull request update function
- **THEN** the other components SHALL still be synchronized and proposed
- **AND** the function call SHALL fail and report the failed component

#### Scenario: Component does not depend on sibling versions
- **GIVEN** a component whose chart depends on another component
- **WHEN** the scenario synchronizes the component
- **THEN** the result SHALL NOT depend on the pinned or published version of the other component

### Requirement: Helm CI scenario chart sync version selection
The system SHALL select the highest upstream version from the OCI tags of the upstream chart that is a stable `MAJOR.MINOR.PATCH` semantic version and satisfies every comparison of the component version filter. It SHALL propose an update only when the selected version is greater than the pinned version.

#### Scenario: Newer version matches the filter
- **GIVEN** a component pinned to `1.0.4` with filter `>=1.0.0 <2.0.0` and upstream tags `1.0.4`, `1.0.5`, and `2.0.0`
- **WHEN** the scenario synchronizes the component
- **THEN** it SHALL synchronize the component to `1.0.5`

#### Scenario: Tags that are not stable versions
- **GIVEN** upstream tags that include signature tags such as `sha256-<hex>.sig` and prerelease tags such as `1.1.0-rc.1`
- **WHEN** the scenario selects a version
- **THEN** it SHALL ignore those tags

#### Scenario: Component is up to date
- **GIVEN** a component whose pinned version is equal to or greater than the highest matching upstream version
- **WHEN** the scenario synchronizes the component
- **THEN** it SHALL leave the component directory and pin unchanged
- **AND** it SHALL NOT propose a change for that component

#### Scenario: No version matches the filter
- **GIVEN** an upstream chart without any tag that matches the component filter
- **WHEN** the scenario synchronizes the component
- **THEN** the component SHALL fail and name the chart and filter

#### Scenario: Registry is unreachable
- **GIVEN** the upstream registry cannot be reached or rejects anonymous tag listing
- **WHEN** the scenario synchronizes the component
- **THEN** the component SHALL fail instead of being skipped

### Requirement: Helm CI scenario chart sync package integrity
The system SHALL verify that the pulled pinned package has the pinned OCI manifest digest and that both pulled packages declare the requested chart name and version, and SHALL record the digest of the selected package in the pin.

#### Scenario: Pinned digest does not match
- **GIVEN** an upstream package whose digest differs from the pinned `digest`
- **WHEN** the scenario synchronizes the component
- **THEN** the component SHALL fail without writing the component directory or pin

#### Scenario: Pin is updated
- **GIVEN** a component synchronized to a new version
- **WHEN** the scenario writes the result
- **THEN** the pin SHALL contain the selected `version` and the OCI manifest `digest` of the selected package

### Requirement: Helm CI scenario chart sync merge
The system SHALL merge the upstream changes between the pinned and the selected package into the component directory, keep local fork edits, and change only the component directory and its pin.

#### Scenario: Upstream adds, changes, deletes, and renames files
- **GIVEN** an upstream package that added, changed, deleted, and renamed files since the pinned version
- **WHEN** the scenario synchronizes the component
- **THEN** the component directory SHALL contain those upstream changes
- **AND** files that exist only in the fork, and local edits that do not conflict, SHALL be kept

#### Scenario: Merge conflict
- **GIVEN** an upstream change that conflicts with a local fork edit
- **WHEN** the scenario synchronizes the component
- **THEN** the component SHALL fail without writing the component directory or pin

#### Scenario: Chart version collision
- **GIVEN** a merge result that changes the component files but keeps the local `Chart.yaml` `version`
- **WHEN** the scenario synchronizes the component
- **THEN** the component SHALL fail with a message that requires manual resolution of the version collision

#### Scenario: Vendored dependencies are not merged
- **GIVEN** a component directory with a `charts/` directory or `Chart.lock`
- **WHEN** the scenario synchronizes the component
- **THEN** it SHALL neither read nor write those paths

#### Scenario: Unsafe package content
- **GIVEN** an upstream package or component directory that contains symbolic links or `.git` metadata
- **WHEN** the scenario synchronizes the component
- **THEN** the component SHALL fail without writing the component directory or pin

### Requirement: Helm CI scenario chart sync exclusions and rewrites
The system SHALL remove excluded chart-relative paths from both upstream packages and SHALL rewrite UTF-8 files of both packages before merging, in this order: `https://github.com/nixys/<upstream>` to `<home>/tree/master/<path>` for every component, the shared rules, each upstream chart name to its component ID, and the component rules.

#### Scenario: Exclusion matches exact paths
- **GIVEN** an exclusion `LICENSE` and upstream files `LICENSE` and `LICENSE.txt`
- **WHEN** the scenario synchronizes the component
- **THEN** `LICENSE` SHALL be excluded and `LICENSE.txt` SHALL be kept

#### Scenario: Literal, regular expression, and file-scoped rules
- **GIVEN** a rule with `from`, a rule with `regex`, and a rule limited by `file`
- **WHEN** the scenario rewrites a package
- **THEN** it SHALL replace the literal `from` text, replace Python regular expression `regex` matches, and apply a `file` rule only to that chart-relative path

#### Scenario: Binary files
- **GIVEN** an upstream file that is not valid UTF-8
- **WHEN** the scenario rewrites a package
- **THEN** the file SHALL be left unchanged

### Requirement: Helm CI scenario chart sync preview and local synchronization
The system SHALL expose a manifest function that returns the rendered Updatecli manifest, a preview function that reports pending component updates without modifying files, and a local synchronization function that returns `source` with the selected components synchronized. The preview and local synchronization functions SHALL run without SCM access or credentials.

#### Scenario: Preview pending updates
- **GIVEN** components with newer upstream versions
- **WHEN** the caller runs the preview function
- **THEN** the report SHALL name each outdated component with its pinned and selected versions
- **AND** no file in `source` SHALL be modified

#### Scenario: Synchronize locally
- **GIVEN** components with newer upstream versions
- **WHEN** the caller runs the local synchronization function
- **THEN** the returned directory SHALL contain the synchronized component directories and pins

#### Scenario: Render the pull request manifest
- **GIVEN** a caller passes `repository` and `branch` to the manifest function
- **WHEN** the scenario renders the manifest
- **THEN** it SHALL return one pipeline per selected component with pipeline ID `upstream-<component id>`
- **AND** the rendered manifest SHALL NOT contain token values

### Requirement: Helm CI scenario chart sync runtime container
The system SHALL expose a function that returns the Updatecli runtime container used by the chart sync functions, and a function that replaces it with a caller-provided container. The chart sync functions SHALL run Updatecli in the replaced container, with the helper, the manifest, and secrets added to it.

#### Scenario: Default runtime container
- **GIVEN** a caller has not replaced the runtime container
- **WHEN** the caller requests the runtime container
- **THEN** the scenario SHALL return a container from the configured Updatecli runtime image with `source` as the working tree

#### Scenario: Caller binds a service to the runtime container
- **GIVEN** a caller takes the runtime container, binds a registry service to it under an alias, and passes the result back to the scenario
- **WHEN** the caller runs any chart sync function
- **THEN** the helper SHALL reach the bound service under that alias

### Requirement: Helm CI scenario chart sync pull request proposal
The system SHALL expose an update function that takes `github_token` as a secret, `repository` as `owner/name`, and `branch`, and creates or updates one pull request per changed component against `branch` from the working branch `updatecli_<branch>_upstream-<component id>`.

#### Scenario: Component changed upstream
- **GIVEN** a component with a newer upstream version
- **WHEN** the caller runs the update function
- **THEN** a pull request against `branch` SHALL contain only the component directory changes and the pin change
- **AND** a later run for the same component SHALL update the same pull request

#### Scenario: Built-in CI token
- **GIVEN** the caller passes a GitHub Actions built-in token with contents and pull request write permissions
- **WHEN** the caller runs the update function
- **THEN** the scenario SHALL create commits and pull requests without any other credential
- **AND** the token value SHALL NOT appear in returned output

#### Scenario: Nothing changed upstream
- **GIVEN** every selected component is up to date
- **WHEN** the caller runs the update function
- **THEN** no pull request SHALL be created or updated

### Requirement: Helm CI scenario chart sync remains CI-provider portable
The system SHALL leave scheduling, pull request CI triggering, review, merge order, and merging to the caller workflow.

#### Scenario: Caller runs updates
- **GIVEN** a caller workflow that runs the update function
- **WHEN** the scenario creates or updates pull requests
- **THEN** the scenario SHALL NOT trigger CI workflows, enable auto-merge, or merge pull requests
- **AND** it SHALL NOT inspect CI provider event environment variables

### Requirement: Helm CI scenario chart sync Dagger tests
The system SHALL verify chart sync behavior in the `scenarios/helm-ci/tests` Dagger test module using local registry and repository fixtures and no credentials.

#### Scenario: Run chart sync tests
- **GIVEN** the Helm CI scenario test module
- **WHEN** a user or CI runs `make tests scenario helm-ci`
- **THEN** the aggregate test SHALL cover configuration validation, version selection, digest verification, merge, conflict, version collision, exclusions, rewrites, preview, local synchronization, and rendered pull request manifests
- **AND** any failed check SHALL fail the test run

## MODIFIED Requirements

### Requirement: Helm CI Runtime Image Inputs
The Helm CI scenario SHALL expose runtime image inputs for the Helm, Git, and Updatecli modules it composes.

#### Scenario: Caller configures Helm runtime image
- **WHEN** a caller invokes Helm chart verification or publication through the Helm CI scenario
- **THEN** the scenario SHALL use `helm_image_registry`, `helm_image_repository`, `helm_image_tag`, and `helm_container_user_id` when creating the Helm module

#### Scenario: Caller configures Git runtime image
- **WHEN** a caller invokes changed-chart verification through the Helm CI scenario
- **THEN** the scenario SHALL use `git_image_registry`, `git_image_repository`, `git_image_tag`, and `git_container_user_id` when creating the Git module

#### Scenario: Caller configures Updatecli runtime image
- **GIVEN** a caller provides `updatecli_image_registry`, `updatecli_image_repository`, `updatecli_image_tag`, or `updatecli_container_user_id`
- **WHEN** the caller runs any chart sync function
- **THEN** the scenario SHALL pass those values to the Updatecli module
- **AND** the default runtime image SHALL provide Updatecli, Helm, git, and Python with PyYAML

#### Scenario: Single-chart workflow does not require Git image inputs
- **WHEN** a caller invokes `verify-chart` or `publish-chart` for one chart directory
- **THEN** Git runtime image inputs SHALL remain available on the scenario API
- **AND** the scenario SHALL NOT invoke the Git module for those operations

#### Scenario: Runtime inputs do not expose module object types
- **WHEN** callers configure Helm CI runtime images
- **THEN** they SHALL pass primitive image input values
- **AND** the scenario SHALL NOT require callers to pass Helm, Git, or Updatecli module object values
