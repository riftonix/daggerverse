## Why

Dagger modules and scenarios currently use different public parameter names for the primary input directory, so CI commands are harder to copy between workflows and users must remember whether a component expects `source`, `site`, a chart directory, or a repository directory. Standardizing on `source` makes the repository API easier to learn and keeps scenario calls aligned with the existing Helm module constructor pattern.

## What Changes

- Introduce a repository-wide convention that the primary input directory for a project, chart, site, repository checkout, or other main source tree is named `source`.
- **BREAKING** Update public module and scenario APIs that still expose specialized primary directory names, such as `site`, `chart`, or repository-source variants, to use `source` instead.
- **BREAKING** Update `scenarios/static-site` from function-level `site` directory inputs to an object API with constructor `source`, matching the `modules/helm` pattern.
- Keep specialized names only for secondary inputs, such as values files, output directories, registry URLs, target branches, chart paths inside a repository, and other paths that are not the primary input tree.
- Require callers to provide `hugo_theme_url` when using the Hugo engine instead of hardcoding `DEFAULT_THEME_URL` inside `scenarios/static-site/src/static_site/main.py`.
- Audit existing modules and scenarios for primary directory inputs and update any outliers to the `source` convention.
- Update READMEs, repository docs, and examples so CLI calls use `dagger -m <module-or-scenario> call --source=<dir> <function> ...`.
- Add or adjust tests that cover public API shape and documented CLI examples, especially the static-site scenario call form.
- Document the migration path for CI consumers, including replacing `--site` with `--source` for `scenarios/static-site`; do not preserve backward-compatible aliases.
- Keep provider-specific CI policy outside scenarios: `source` only identifies the input tree, while events, checkout strategy, preview URL derivation, publication, and cleanup remain owned by the CI provider workflow.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `daggerverse`: Establish the repository-wide public API and documentation convention for primary input directories named `source`.
- `static-site-scenario`: Change the static-site scenario public API to constructor `source`, update verify/render behavior to use that source tree, and require a Hugo theme URL for Hugo-backed operations.
- `helm-ci-scenario`: Confirm and, if needed, standardize any public primary source directory inputs while preserving specialized secondary inputs such as target branch and chart path.

## Impact

- Affected code: module and scenario public APIs that accept primary input directories, with specific work expected in `scenarios/static-site`.
- API impact: breaking CLI change for callers using old primary directory parameter names, including `scenarios/static-site` callers that currently pass `--site`.
- CI impact: provider workflows must migrate calls to `--source=<dir>` and continue computing provider-specific event, checkout, preview, and publication details outside the Dagger scenario.
- Documentation impact: root README, scenario READMEs, how-to guides, and examples must use the standardized `--source` call shape.
- Release impact: changed scenarios/modules need new tags so downstream users can opt into the breaking API.
