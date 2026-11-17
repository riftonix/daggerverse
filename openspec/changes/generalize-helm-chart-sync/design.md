# Generalize Helm Chart Sync Design

## Glossary and References

### Glossary

- **Component, pin, base, incoming, ours**: as in the `add-helm-chart-sync` design.
- **Format version**: the top-level `version` key of the chart sync configuration. This change introduces format `2`. The format of `scenarios/helm-ci/v1.4.0` has no `version` key.
- **Registry entry**: a named item of `registries` with an OCI `url` and an optional `plainhttp` flag.
- **Placeholder**: `${id}`, `${upstream}`, `${path}`, or `${registry}` in a configuration value, replaced with a value of one component.
- **Rule scope**: `current` (the default) expands a rewrite rule for the component being synchronized; `all` expands it once for every declared component.
- **Import**: synchronization of a declared component that has neither a directory nor a pin.

### References

- `openspec/changes/archive/2026-11-16-add-helm-chart-sync/`: the chart sync design and requirements that this change generalizes.
- `scenarios/helm-ci/src/helm_ci/chart_sync.py`: `load_config`, `rules`, `VENDORED`, `list_tags`, `pull`, and `synchronize`.
- `riftonix/helm-shared` `master` at `37c5706`: `updatecli/values.yaml` with 25 components.
- Specs: `specs/helm-ci-scenario/spec.md`.

## Context

### Problem Context

See `proposal.md`, section Why. The repository-specific behavior sits in a few places of `chart_sync.py`:

- `load_config` reads one `upstream` block (`registry`, `plainhttp`, `versionfilter`, `exclude`) and a required `home`. It accepts only `charts/<name>` and `libs/<name>` paths, defaults the path to `libs/<id>` and the upstream chart name to `nuc-<id>`, and ignores unknown keys.
- `rules()` prepends the `https://github.com/nixys/<upstream>` to `<home>/tree/master/<path>` rules and inserts the `<upstream>` to `<id>` rules after the shared rules, for every declared component.
- `VENDORED = ["charts", "Chart.lock"]` is added to the package exclusions and to the copy of the fork directory.
- The pin path is `<config directory>/pins/<id>.json`, and a missing pin is a validation error.
- `list_tags` and `pull` take the registry from the single `Config.registry`.

### Existing Technical Constraints

- The scenario validates the configuration by running `chart_sync.py validate`, and renders the manifest from its `id`, `path`, and `pin` output. Both stay as they are.
- In pull request mode, Updatecli commits the files that the shell target changed in its clone, through the GitHub API.
- `helm-shared` is the only known user of the configuration, and it has not adopted the scenario yet.

## Goals / Non-Goals

### Goals

- Express the current `helm-shared` behavior exactly with format `2` configuration, so that its migration does not change synchronization results.
- Keep the merge, digest, and safety logic of the helper unchanged, and reuse it for imports.
- Keep the Dagger function signatures and the rendered manifest unchanged.

### Non-Goals

- Accepting format `1` configuration, or converting it automatically.
- A general template language. Placeholders are plain names without expressions or filters.

## Architecture and Component Boundaries

### Architecture Overview

The architecture of `add-helm-chart-sync` is unchanged. Only the helper changes: configuration loading, rule expansion, registry selection, vendored paths, pin location, and the import path of `synchronize`.

### Component Boundaries

- `main.py` and `chart_sync_manifest.py` keep their behavior. Their docstrings and messages are updated only where they mention the old layout.
- All repository-specific values come from the configuration. The helper keeps generic built-in values only: the default vendored paths, the default pin directory, and the safety rules.

## Component Changes

### Chart Sync Helper

- **Configuration loading:** `load_config` checks `version == 2` first. For any other value it fails with one error that names the required version, without further checks, because a format `1` file would otherwise produce many misleading errors. It then validates each section against its allowed keys and collects every error.
- **Registries:** a frozen `Registry(name, url, plain_http)` replaces `Config.registry` and `Config.plain_http`. Every `Component` holds its resolved `Registry`. `list_tags` and `pull` take the registry of the component.
- **Defaults:** `defaults.path` and `defaults.upstream` are templates with `${id}`. The resolved component path, upstream chart name, registry, version filter, exclusions, and vendored paths are stored on the `Component`.
- **Paths:** a component path is one or more `[A-Za-z0-9][A-Za-z0-9._-]*` segments, without `.` or `..`. No existing prefix of the path may be a symbolic link or a regular file. Overlap is checked on path segments between all component paths, the configuration file, and the pin directory.
- **Pins:** the pin directory comes from `pins` (default: the parent of `config_path`) and is validated like a component path. It may be absent; an import creates it.
- **Vendored paths:** `DEFAULT_VENDORED = ["charts", "Chart.lock"]` replaces `VENDORED`. Component `vendored` replaces `defaults.vendored`, which replaces the built-in default. The resolved list is used where `VENDORED` was used.
- **Rewrite rules:** `rules()` drops the built-in GitHub and name rules. It expands the shared rules and then the component rules, in declared order. A `scope: all` rule produces one rule per declared component, in declaration order. Any other rule produces one rule for the current component.
- **Placeholders:** they are parsed once during validation, with the pattern `\$\$\{|\$\{([A-Za-z]+)\}`. Any other `${` sequence, and a name that the value does not support, is a configuration error. The expansion adapts each value to the field it is inserted into:
  - in `regex`, the value is inserted with `re.escape`;
  - in the `to` of a `regex` rule, backslashes in the value are doubled, so that `re.sub` inserts the value literally;
  - in `from`, in the `to` of a literal rule, and in `file`, the value is inserted as is.

  `$${` always becomes `${`.
- **Import:** a component with an absent directory and an absent pin is marked for import. `synchronize` then does the following:
  1. it selects the version as before, and pulls only the selected package;
  2. it uses empty `base` and `ours` trees, so that the existing merge yields the normalized package;
  3. it skips the version-collision check, because there is no local `Chart.yaml`;
  4. it fails if the patch is empty, because a pin without a directory would fail the next validation;
  5. after `git apply --check`, it prints `Preview <id>: import <version>` or `Apply <id>: import <version>`;
  6. on apply, it applies the patch, creates the pin directory when it is missing, and writes the pin.

### Tests and Fixtures

- The fork fixture `updatecli/values.yaml` moves to format `2` with two registry entries that point to two projects of the one local `registry:3` service. This covers registry selection without a second service.
- New fixture components cover:
  - a nested path, such as `platform/charts/<id>`;
  - a component without a directory and pin, for import;
  - custom `vendored` and `pins` values.
- The existing rewrite expectations stay valid through explicit `scope: all` rules in the fixture. A separate check runs without rules and expects upstream names to stay unchanged.

### Scenario README

The chart sync section documents format `2`: every key, placeholders and scopes, registries, vendored paths, the pin directory, imports, and a format `1` to format `2` migration example.

## Data Model

### Entities and Relationships

Format `2`, with the current `helm-shared` behavior expressed explicitly:

```yaml
version: 2
registries:
  nixys:
    url: oci://registry.nixys.ru/nuc
defaults:
  registry: nixys
  path: libs/${id}
  upstream: nuc-${id}
  versionfilter: '>=1.0.0 <2.0.0'
  exclude: [.github/, docs/AGENTS.md, CHANGELOG.md, LICENSE]
rewrite:
- scope: all
  from: https://github.com/nixys/${upstream}
  to: https://github.com/riftonix/helm-shared/tree/master/${path}
- {from: oci://registry.nixys.ru/nuc/nxs-universal-chart, to: oci://ghcr.io/riftonix/helm-shared/charts/appchart}
- {from: oci://registry.nixys.ru/nuc, to: oci://ghcr.io/riftonix/helm-shared/libs}
# ... the remaining shared rules of the current file, unchanged
- scope: all
  from: ${upstream}
  to: ${id}
components:
  appchart: {path: charts/appchart, upstream: nxs-universal-chart, versionfilter: '>=3.0.0 <4.0.0', rewrite: [...]}
  cert-manager: {upstream: nuc-certificates}
  common: {}
```

The rule order matches the current built-in order: GitHub URLs, shared rules, chart names, component rules. `charts/` and `Chart.lock` no longer need to be in `exclude`, because they are the default vendored paths. `home` and `github` are removed; they are unknown keys in format `2`.

Allowed keys:

| Location | Keys |
| --- | --- |
| top level | `version`, `registries`, `defaults`, `pins`, `rewrite`, `components` |
| `registries.<name>` | `url`, `plainhttp` |
| `defaults` | `registry`, `path`, `upstream`, `versionfilter`, `exclude`, `vendored` |
| `components.<id>` | `registry`, `path`, `upstream`, `versionfilter`, `exclude`, `vendored`, `rewrite` |
| rewrite rule | `from` or `regex`, `to`, `file`, `scope` |

### Persistence Model

The pin format and the way the helper writes component directories do not change. An import writes the component directory through the same binary patch, and creates the pin directory with default permissions.

### Indexes and Constraints

- Registry names and component IDs match `[a-z0-9][a-z0-9-]*`.
- Component paths, the configuration file, and the pin directory do not overlap on path segments.
- `scope` is `current` or `all`.

## Technical Contracts

### Internal Contracts

- The `validate` and `sync` commands, their arguments, exit codes, and the stdout rule (output only on a change) do not change.
- The report line of an import is `Preview <id>: import <version>` or `Apply <id>: import <version>`.
- The `validate` JSON keeps `id`, `path`, and `pin`. `pin` reflects the configured pin directory.

## Error Handling

### Error Categories

- **Configuration errors:** in addition to the existing ones, these are a wrong or missing format version, unknown keys, an invalid or undeclared registry, a missing path or version filter, an invalid placeholder or scope, an overlapping path, and a pin that exists without its directory. They are reported together, except for a wrong format version, which is reported alone.
- **Import errors:** a missing matching tag, a failed pull, an identity mismatch, unsafe content, or an empty result. They fail the component without creating the directory or the pin.

### Retry and Recovery

A failed import leaves the repository unchanged, so the next run retries it. To retry an import after a manual partial copy, remove the component directory and keep the pin absent.

## Decisions

### Decision: Explicit rules instead of built-in rewrites

The built-in GitHub URL and chart name rules become ordinary configuration rules with `scope: all` and placeholders. They depend on all declared components and on the order relative to shared rules. A per-rule scope expresses both without new special keys. `home` becomes unnecessary.

Alternatives considered:
- boolean switches such as `rewritenames: false` and a configurable GitHub organization and branch, rejected because they keep the special cases and their fixed order;
- requiring one literal rule per component, rejected because `helm-shared` would need 50 generated rules.

### Decision: Breaking format with a version key

Accepting both formats would keep the nixys defaults alive in the code, and the format has no adopters yet. A required `version: 2` makes the break explicit, and the error names the required version instead of reporting unrelated missing keys. Unknown keys are now rejected, so leftovers such as `home`, `upstream`, or `github` fail instead of being silently ignored.

Alternative considered: keeping format `1` with new opt-out keys, rejected by the repository owner in favor of a clean break.

### Decision: Named registries

Components select a registry by name. Repositories with many components from one registry declare it once, and a registry change edits one place. The `${registry}` placeholder gives rewrite rules the URL of the component registry.

Alternative considered: a per-component `registry` URL override, rejected as more repetitive and without a shared name for rules.

### Decision: Import through the existing merge

An import is a merge with empty base and ours trees. The safety checks, the exclusions and rewrites, the patch check, and the write path stay the same for updates and imports. An import starts only when both the directory and the pin are absent. A directory without a pin, or a pin without a directory, is ambiguous and stays a validation error.

Alternative considered: a separate `import` helper command or Dagger function, rejected because it would duplicate the pipeline and the pull request flow.

## Risks / Trade-offs

- [Format `2` configurations of `helm-shared` change synchronization results by mistake] → The design includes the equivalent configuration. The `helm-shared` follow-up runs `sync-charts-diff` before and after the migration and compares the reports.
- [Updatecli does not commit the new, untracked files of an import through the GitHub API] → Not verified yet. The first import runs for one component in a pull request and is reviewed before imports are relied on.
- [Placeholders collide with literal `${` in regular expressions or text] → `$${` escapes it, and unsupported placeholders fail validation instead of being kept.
- [Nested component paths hide one chart in another] → Overlapping paths are rejected.

## Migration Plan

### Rollout

1. Implement the change and release a new version of `scenarios/helm-ci`.
2. In the `helm-shared` integration follow-up, migrate `updatecli/values.yaml` to format `2` (see [Entities and Relationships](#entities-and-relationships)) and use the new release.

### Backward Compatibility

- Format `1` configurations are rejected with an error that names the required format version.
- Pins, Dagger function signatures, the manifest, the working branch names, and the pull request texts do not change.

### Rollback

`helm-shared` can return to `scenarios/helm-ci/v1.4.0` together with its format `1` configuration. Pins stay valid in both directions.

## Open Questions

- Release version number: the chart sync configuration break has no adopters, so the release can be either the next minor or the next major version of `scenarios/helm-ci`. This does not change the implementation.
