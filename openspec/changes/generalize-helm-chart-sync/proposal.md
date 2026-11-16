# Generalize Helm Chart Sync Proposal

## Why

### Initial Requirements and Drivers

The chart sync functions of `scenarios/helm-ci` (released in `scenarios/helm-ci/v1.4.0`) were ported from the `helm-shared` draft updater and still carry that repository's assumptions. The repository owner wants the chart sync to work for any repository that forks OCI-published Helm charts, with every repository-specific rule kept in the configuration in the repository's `updatecli/` directory instead of in the scenario code.

### Current Solution

- Before the scenario's rewrite rules, it always rewrites `https://github.com/nixys/<upstream>` to `<home>/tree/master/<path>` for every component. The GitHub organization `nixys` and the branch `master` are hardcoded.
- After the shared rules, it always replaces each upstream chart name with its component ID, as a substring, in every UTF-8 file of both packages. This rule cannot be disabled or reordered.
- A component path must be `charts/<name>` or `libs/<name>`. An omitted path defaults to `libs/<id>`, and an omitted upstream chart name defaults to `nuc-<id>`.
- The configuration has one upstream registry (`upstream.registry` and `upstream.plainhttp`) for all components.
- Vendored dependencies (`charts/` and `Chart.lock`) are always left out of the merge. Pins are always stored in `<config directory>/pins/<id>.json`.
- A component must already have a directory and a pin. Importing a new upstream chart is a manual change.

### Business Problems

- Repositories that fork charts from other organizations, registries, or branch layouts get wrong rewrites that they cannot turn off.
- The forced name replacement can corrupt files where the upstream chart name occurs as a plain substring.
- Repositories with other directory layouts, or with charts from more than one registry, cannot use the chart sync at all.
- Registering a new forked chart needs a manual copy of the upstream package and a hand-written pin with the right digest.

## Stakeholders

- Repository owner of `daggerverse` and `helm-shared`: maintains the scenario and the forked charts.
- Future users of the chart sync functions in other repositories that fork OCI-published charts.

## What Changes

### Goals

- Remove every repository-specific rule from the scenario code, so that the configuration file describes all rewrites, paths, upstream names, and registries.
- Support component directories at any safe relative path.
- Support several named upstream registries, selected per component.
- Make the vendored paths and the pin directory configurable.
- Import a declared component that has neither a directory nor a pin.

### Scope

- **BREAKING:** a new chart sync configuration format with a required `version: 2` key. The scenario rejects the format of `scenarios/helm-ci/v1.4.0`, and `helm-shared` migrates its `updatecli/values.yaml` when it adopts the scenario.
- Named registries with a default registry and a per-component selection.
- A `defaults` section for the registry, path and upstream name templates, version filter, exclusions, and vendored paths.
- Rewrite rules with component placeholders, applied either to the current component or to every declared component. These rules replace the built-in GitHub URL and chart name rewrites.
- A configurable pin directory.
- Initial import of a component whose directory and pin are both absent.
- Chart sync tests and the scenario README for the new format.

### Non-Goals

- GitLab or other SCM kinds. Pull requests stay on GitHub.
- Registry credentials and non-OCI chart repositories.
- Prerelease versions and version filters beyond the current comparison syntax.
- Configurable pipeline IDs, working branch names, pull request titles, and descriptions.
- Changes to `verify_chart`, `publish_chart`, and the other existing Helm CI functions.
- The `helm-shared` integration itself. It stays a separate follow-up.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `helm-ci-scenario`: changes the chart sync configuration, validation, exclusions and rewrites, merge, and test requirements, and adds upstream registry and initial import requirements.

## Impact

### Users and Business Processes

- Callers of the chart sync functions write all rewrite rules, path and upstream name defaults, and registries explicitly in their configuration.
- Registering a new forked chart becomes a configuration entry, followed by a reviewed import pull request.

### Systems and Components

- `daggerverse`: the `scenarios/helm-ci` chart sync helper, its tests and fixtures, and the scenario README. The Dagger function signatures and the rendered Updatecli manifest do not change.
- `helm-shared`: `updatecli/values.yaml` has to be migrated to the new format before it uses a scenario release with this change.

### Data and Integrations

- The configuration format changes incompatibly. The pin file format does not change.
- Upstream registries are still read anonymously over the OCI Distribution API.

### Operational Impact

- Releases of `scenarios/helm-ci` with this change reject chart sync configurations in the `scenarios/helm-ci/v1.4.0` format.
