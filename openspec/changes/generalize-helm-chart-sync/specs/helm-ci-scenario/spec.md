# Helm CI Scenario Delta Specification

## ADDED Requirements

### Requirement: Helm CI scenario chart sync upstream registries
The system SHALL resolve the upstream chart of each component in the named registry that the component `registry` key selects, or `defaults.registry` when the component omits it. It SHALL list tags and pull packages of that component only from that registry, and SHALL use plain HTTP only when the registry sets `plainhttp: true`.

#### Scenario: Components from different registries
- **GIVEN** registries `a` and `b`, `defaults.registry: a`, a component `demo` without `registry`, and a component `other` with `registry: b`
- **WHEN** the scenario synchronizes both components
- **THEN** it SHALL resolve `demo` in registry `a` and `other` in registry `b`

#### Scenario: Registry uses HTTPS by default
- **GIVEN** a registry without `plainhttp`
- **WHEN** the scenario lists tags or pulls packages from it
- **THEN** it SHALL use HTTPS

### Requirement: Helm CI scenario chart sync component placeholders
The system SHALL replace `${id}` in `defaults.path` and `defaults.upstream`, and `${id}`, `${upstream}`, `${path}`, and `${registry}` in the `from`, `regex`, `to`, and `file` values of rewrite rules, with the component ID, upstream chart name, component path, and registry URL. `$${` SHALL produce a literal `${`. Substituted values SHALL match and be inserted literally in regular expression rules.

#### Scenario: Path and upstream name templates
- **GIVEN** `defaults.path: libs/${id}`, `defaults.upstream: nuc-${id}`, and a component `common` declared as an empty entry
- **WHEN** the caller runs any chart sync function
- **THEN** the scenario SHALL use `libs/common` as the component path and `nuc-common` as the upstream chart name

#### Scenario: Placeholder in a regular expression rule
- **GIVEN** a component with upstream chart name `nuc.demo` and a rule with `regex: '${upstream}'`
- **WHEN** the scenario rewrites a package
- **THEN** the rule SHALL replace `nuc.demo` and SHALL NOT replace `nucXdemo`

#### Scenario: Escaped placeholder
- **GIVEN** a rule with `to: '$${id}'`
- **WHEN** the scenario rewrites a package
- **THEN** the rule SHALL write the literal text `${id}`

### Requirement: Helm CI scenario chart sync initial import
The system SHALL import a declared component whose directory and pin are both absent. It SHALL select the version as for an update, write the selected package to the component path after exclusions, vendored paths, and rewrites, and create the pin with the selected `version` and OCI manifest `digest`.

#### Scenario: Preview an import
- **GIVEN** a declared component without a directory and without a pin
- **WHEN** the caller runs the preview function
- **THEN** the report SHALL name the component as an import with the selected version
- **AND** no file in `source` SHALL be modified

#### Scenario: Import a component
- **GIVEN** a declared component without a directory and without a pin
- **WHEN** the caller runs the local synchronization function or the pull request update function
- **THEN** the result SHALL contain the normalized selected package at the component path and the new pin
- **AND** no other path SHALL change

#### Scenario: Import cannot resolve a version
- **GIVEN** a declared component without a directory and without a pin, and no upstream tag that matches its filter
- **WHEN** the scenario synchronizes the component
- **THEN** the component SHALL fail without creating the component directory or pin

## MODIFIED Requirements

### Requirement: Helm CI scenario chart sync configuration
The system SHALL read chart sync configuration from the YAML file at `config_path` in `source` (default `updatecli/values.yaml`). The configuration SHALL declare `version: 2`, named `registries`, optional `defaults`, optional shared `rewrite` rules, an optional `pins` directory, and a map of components keyed by component ID. The pin of each component SHALL be `<pins>/<component id>.json`, where `pins` is relative to `source` and defaults to `<config directory>/pins`. A pin SHALL record the synchronized upstream `version` and OCI manifest `digest`.

#### Scenario: Component uses defaults
- **GIVEN** `defaults` with `registry`, `path`, `upstream`, `versionfilter`, `exclude`, and `vendored`, and a component `common` declared as an empty entry
- **WHEN** the caller runs any chart sync function
- **THEN** the scenario SHALL use those defaults for `common`
- **AND** it SHALL read the pin from `updatecli/pins/common.json`

#### Scenario: Upstream chart name without a default
- **GIVEN** a configuration without `defaults.upstream` and a component without `upstream`
- **WHEN** the caller runs any chart sync function
- **THEN** the scenario SHALL use the component ID as the upstream chart name

#### Scenario: Component overrides defaults
- **GIVEN** a component that declares `registry`, `path`, `upstream`, `versionfilter`, `exclude`, `vendored`, or `rewrite`
- **WHEN** the scenario synchronizes the component
- **THEN** `registry`, `path`, `upstream`, `versionfilter`, and `vendored` SHALL replace the defaults
- **AND** `exclude` SHALL be added to `defaults.exclude`
- **AND** `rewrite` rules SHALL be applied after the shared rules

#### Scenario: Component path at any depth
- **GIVEN** a component with `path: platform/charts/demo`
- **WHEN** the scenario synchronizes the component
- **THEN** it SHALL change only `platform/charts/demo` and the component pin

#### Scenario: Custom pin directory
- **GIVEN** a configuration with `pins: sync/pins`
- **WHEN** the caller runs any chart sync function
- **THEN** the scenario SHALL read and write the pin of component `common` at `sync/pins/common.json`

#### Scenario: Caller selects components
- **GIVEN** a caller passes the `components` input with one or more component IDs
- **WHEN** the caller runs any chart sync function
- **THEN** the scenario SHALL process only the selected components
- **AND** an omitted or empty `components` input SHALL select every component

### Requirement: Helm CI scenario chart sync configuration validation
The system SHALL validate the chart sync configuration and pins before running any pipeline, and SHALL fail with one message that names every invalid item.

#### Scenario: Previous configuration format
- **GIVEN** a configuration without `version: 2`, such as the format accepted by `scenarios/helm-ci/v1.4.0`
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name the required format version

#### Scenario: Unknown keys
- **GIVEN** an unknown key at the top level, in `defaults`, in a registry, in a component, or in a rewrite rule
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name the key and its location

#### Scenario: Missing configuration values
- **GIVEN** a configuration without `registries` or `components`, or a component without a registry, a path, or a version filter from its own keys or from `defaults`
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name each missing value

#### Scenario: Invalid registry
- **GIVEN** a registry whose name does not match `[a-z0-9][a-z0-9-]*` or whose URL is not `oci://<host>[/<project>]`, or a component or `defaults.registry` that names an undeclared registry
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name the registry

#### Scenario: Unsafe component
- **GIVEN** a component whose ID does not match `[a-z0-9][a-z0-9-]*`, or whose `path` is not a relative path inside `source`, contains a `.` or `..` segment, passes through a symbolic link, or is equal to, contains, or is contained in another component path, the configuration file, or the pin directory
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name the component

#### Scenario: Missing or invalid pin
- **GIVEN** a component whose directory exists and whose pin file is missing, a component whose pin exists without its directory, or a pin that is a symbolic link or lacks a semantic `version` or a `sha256` `digest`
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name the component

#### Scenario: Invalid placeholder
- **GIVEN** a `${...}` placeholder that is not supported in the value where it appears
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name the value and placeholder

#### Scenario: Unsupported version filter
- **GIVEN** a version filter that is not a space-separated list of `=`, `>`, `>=`, `<`, or `<=` comparisons with `MAJOR.MINOR.PATCH` versions
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name the component and filter

#### Scenario: Unknown selected component
- **GIVEN** a caller selects a component ID that the configuration does not declare
- **WHEN** the caller runs any chart sync function
- **THEN** the call SHALL fail and name the unknown ID

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
- **GIVEN** a component with vendored paths, which are `charts` and `Chart.lock` unless `vendored` is declared
- **WHEN** the scenario synchronizes the component
- **THEN** it SHALL neither read nor write those chart-relative paths in the component directory
- **AND** it SHALL leave them out of both upstream packages

#### Scenario: No vendored paths
- **GIVEN** a component with `vendored: []`
- **WHEN** the scenario synchronizes the component
- **THEN** it SHALL merge `charts/` and `Chart.lock` like any other path

#### Scenario: Unsafe package content
- **GIVEN** an upstream package or component directory that contains symbolic links or `.git` metadata
- **WHEN** the scenario synchronizes the component
- **THEN** the component SHALL fail without writing the component directory or pin

### Requirement: Helm CI scenario chart sync exclusions and rewrites
The system SHALL remove excluded chart-relative paths from both upstream packages and SHALL rewrite UTF-8 files of both packages before merging, with the shared rules followed by the component rules, each list in its declared order. A rule with `scope: all` SHALL be applied once for every declared component, in declaration order, and any other rule once for the current component. The system SHALL NOT apply rewrites that the configuration does not declare.

#### Scenario: Exclusion matches exact paths
- **GIVEN** an exclusion `LICENSE` and upstream files `LICENSE` and `LICENSE.txt`
- **WHEN** the scenario synchronizes the component
- **THEN** `LICENSE` SHALL be excluded and `LICENSE.txt` SHALL be kept

#### Scenario: Literal, regular expression, and file-scoped rules
- **GIVEN** a rule with `from`, a rule with `regex`, and a rule limited by `file`
- **WHEN** the scenario rewrites a package
- **THEN** it SHALL replace the literal `from` text, replace Python regular expression `regex` matches, and apply a `file` rule only to that chart-relative path

#### Scenario: No implicit rewrites
- **GIVEN** a configuration without rewrite rules and an upstream package that contains its upstream chart name and a `https://github.com/nixys/<upstream>` URL
- **WHEN** the scenario synchronizes the component
- **THEN** the component directory SHALL contain that text unchanged

#### Scenario: Rule for every component
- **GIVEN** a shared rule with `scope: all`, `from: '${upstream}'`, and `to: '${id}'`, and components `demo` and `other` with upstream chart names `nuc-demo` and `nuc-other`
- **WHEN** the scenario rewrites the package of `demo`
- **THEN** it SHALL replace both `nuc-demo` with `demo` and `nuc-other` with `other`

#### Scenario: Rule for the current component
- **GIVEN** a shared rule without `scope`, with `from: '${upstream}'` and `to: '${id}'`, and the components of the previous scenario
- **WHEN** the scenario rewrites the package of `demo`
- **THEN** it SHALL replace `nuc-demo` with `demo` and SHALL leave `nuc-other` unchanged

#### Scenario: Binary files
- **GIVEN** an upstream file that is not valid UTF-8
- **WHEN** the scenario rewrites a package
- **THEN** the file SHALL be left unchanged

### Requirement: Helm CI scenario chart sync Dagger tests
The system SHALL verify chart sync behavior in the `scenarios/helm-ci/tests` Dagger test module using local registry and repository fixtures and no credentials.

#### Scenario: Run chart sync tests
- **GIVEN** the Helm CI scenario test module
- **WHEN** a user or CI runs `make tests scenario helm-ci`
- **THEN** the aggregate test SHALL cover configuration validation, named registries, component paths, placeholders, version selection, digest verification, merge, conflict, version collision, vendored paths, exclusions, rewrites and their scopes, pin directories, initial import, preview, local synchronization, and rendered pull request manifests
- **AND** any failed check SHALL fail the test run
