# Helm CI Scenario

Portable Helm chart verification and publication workflows on top of the local
`helm` and `git` modules.

This scenario is provider-neutral. CI provider workflows decide when to call it,
which branch or paths to diff, and when publication should run.

For full repository documentation, see [../../docs/README.md](../../docs/README.md).
For task-oriented Helm CI usage, see
[Run Helm checks through Helm CI](../../docs/how-to/run-helm-checks-through-helm-ci.md).

## Features

- Helm chart lint + template
- Helm unittest execution for selected suite files
- Helm chart publish to OCI
- Run checks only for changed directories through the Git module
- Verify changed charts from charts/libs directories
- Synchronize forked charts from upstream OCI packages through the `updatecli`
  module, locally or as one GitHub pull request per component

## Quick Start

Verify a single chart:

```bash
dagger -m ./scenarios/helm-ci call \
  --helm-image-tag=3.18.6 \
  --source=./modules/helm/tests/charts/ns-configurator \
  verify-chart
```

Verify one chart selected by the CI matrix:

```bash
dagger -m ./scenarios/helm-ci call \
  --helm-image-tag=3.18.6 \
  --source=charts/app \
  verify-chart
```

`source` must point directly to one Helm chart directory containing
`Chart.yaml`. The scenario keeps one chart per Dagger container and does not
select a nested chart from a repository root.

By default, the composed Helm unittest module discovers and runs files matching
`tests/**/*_test.yaml` or `tests/**/*_test.yml`. Select different suites by
repeating `--unittest-suite-files`:

```bash
dagger -m ./scenarios/helm-ci call \
  --source=charts/app \
  verify-chart \
  --unittest-suite-files='tests/units/*_test.yaml' \
  --unittest-suite-files='tests/components/*_test.yml'
```

Custom patterns replace the defaults. An explicit empty list skips Helm
unittest. Other YAML files, such as `tests/e2e/kind.yaml`, do not enable the
unittest step.

Publish one chart and push its chart-scoped release tag in the same call:

```bash
export GITHUB_TOKEN="$(gh auth token)"

dagger -m ./scenarios/helm-ci call \
  --source=. \
  publish-chart \
  --chart-source=libs/argocd \
  --git-tag-prefix=libs/argocd \
  --oci-url=ghcr.io/riftonix/libs \
  --registry-address=ghcr.io \
  --with-dependency-update=false \
  --registry-login=rift0nix \
  --registry-password=env://GITHUB_TOKEN \
  --git-token=env://GITHUB_TOKEN
```

`registry-login` and `registry-password` authenticate the OCI registry and must
be supplied together. `git-token` authenticates release tag fetch and push
operations. One token can serve both purposes when it has package write and
repository contents write permissions.

`oci-url` is the complete Helm push destination without `oci://` or the chart
name. `registry-address` is optional and defaults to the host and port extracted
from `oci-url`; set it explicitly when the registry login endpoint differs.

The release tag is `<git-tag-prefix>/v<chart-version>`. An existing tag returns
a successful no-op before registry login or chart publication. A missing tag is
created and pushed only after the chart is published successfully.

## Chart Sync

Chart sync keeps forked charts in `charts/<name>` or `libs/<name>` up to date
with their upstream OCI packages. For each component, it lists the upstream
tags, selects the highest stable version that matches the version filter, and
merges the upstream change between the pinned and the selected package into the
fork with Git. Fork edits are kept, conflicts fail the component, and only the
component directory and its pin are written.

### Configuration

The configuration is read from `config_path` in `source`, by default
`updatecli/values.yaml`:

```yaml
upstream:
  registry: oci://registry.example.com/nuc
  versionfilter: ">=1.0.0 <2.0.0"
  exclude: [LICENSE]
home: https://github.com/example/helm-fork
rewrite:
  - {from: oci://registry.example.com/nuc, to: oci://ghcr.io/example/libs}
  - {file: Chart.yaml, regex: '(?m)^home:.*\n?', to: ''}
components:
  common:
  traefik:
    path: charts/traefik
    upstream: nuc-traefik
    versionfilter: ">=3.0.0"
    exclude: [docs/internal.md]
    rewrite:
      - {from: upstream-name, to: fork-name}
```

- `upstream.registry`: upstream OCI registry and project. Anonymous Bearer
  tokens are requested when the registry asks for them.
- `upstream.versionfilter`: default filter, a space-separated list of
  `>=`, `>`, `<=`, `<`, or `=` comparisons with `X.Y.Z` versions. Only stable
  `X.Y.Z` tags are candidates, so prerelease and signature tags are ignored.
- `upstream.exclude`: chart-relative paths that are never synchronized.
  `charts/` and `Chart.lock` are always excluded.
- `upstream.plainhttp`: use plain HTTP; intended for local test registries.
- `home`: fork repository URL. `https://github.com/nixys/<upstream>` links are
  rewritten to `<home>/tree/master/<component path>`.
- `rewrite`: shared text rewrite rules with `from` or `regex`, `to`, and an
  optional chart-relative `file`. Binary files are never rewritten.
- `components`: component IDs. An empty entry uses `libs/<id>`, the upstream
  chart `nuc-<id>`, and the default filter. Upstream chart names of every
  component are rewritten to their IDs. Component `rewrite` rules run after the
  shared rules.

Each component has a pin at `<config directory>/pins/<id>.json` with the
synchronized upstream package:

```json
{
  "version": "1.0.4",
  "digest": "sha256:..."
}
```

The scenario validates the whole configuration and every pin before running any
pipeline and reports all problems in one error. The pinned package must still
match its digest. A pin that is equal to or newer than the selected version
produces no change. Each component runs in its own Updatecli pipeline, so one
failing component does not stop the others.

### Functions

Every function accepts `--config-path` and repeated `--components` to select
component IDs; without `--components`, all components run.

Preview updates without writing files:

```bash
dagger -m ./scenarios/helm-ci call --source=. sync-charts-diff --components=common
```

Synchronize locally and export the updated source:

```bash
dagger -m ./scenarios/helm-ci call --source=. sync-charts export --path=.
```

Render the Updatecli manifest. Without `--repository` and `--branch`, the
manifest updates the local source; with them, it uses a GitHub SCM and a pull
request action:

```bash
dagger -m ./scenarios/helm-ci call --source=. \
  sync-charts-manifest --repository=example/helm-fork --branch=master
```

Open or update one pull request per changed component from the working branch
`updatecli_<branch>_upstream-<id>`:

```bash
dagger -m ./scenarios/helm-ci call --source=. \
  sync-charts-update \
  --github-token=env://GITHUB_TOKEN \
  --repository=example/helm-fork \
  --branch=master
```

The token reaches Updatecli only as the `UPDATECLI_GITHUB_TOKEN` secret
variable and is not written to the manifest. Commits are created through the
GitHub API. Pull requests use the manual merge strategy; the scenario does not
schedule runs, trigger CI, enable auto-merge, or merge.

### Workflow

A scheduled or manually dispatched GitHub Actions workflow can pass the
built-in token. It needs `contents`, `pull-requests`, and `actions` write
permissions, and should check out the same branch that it passes as
`--branch`. Pull requests created with the built-in token do not start
`pull_request` workflows, so the workflow dispatches CI on each open update
branch:

```yaml
on:
  schedule:
    - cron: "0 6 * * 1"
  workflow_dispatch:
    inputs:
      component: {description: Component ID; empty runs all components, required: false, type: string}
permissions: {contents: write, pull-requests: write, actions: write}
concurrency: {group: updatecli-charts, cancel-in-progress: false}
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: dagger/dagger-for-github@v8.4.1
        with: {version: 0.21.10}
      - run: |
          args=()
          [[ -n "$COMPONENT" ]] && args+=(--components="$COMPONENT")
          dagger -m github.com/riftonix/daggerverse/scenarios/helm-ci@<tag> call --source=. \
            sync-charts-update --github-token=env://GITHUB_TOKEN \
            --repository="$GITHUB_REPOSITORY" --branch=master "${args[@]}"
        env: {GITHUB_TOKEN: "${{ github.token }}", COMPONENT: "${{ inputs.component }}"}
      - run: |
          gh pr list --state open --json headRefName \
            --jq '.[].headRefName | select(startswith("updatecli_master_upstream-"))' |
            while read -r ref; do gh workflow run ci.yaml --ref "$ref"; done
        env: {GH_TOKEN: "${{ github.token }}"}
```

The dispatched `ci.yaml` needs a `workflow_dispatch` trigger.

### Runtime Container

`updatecli-container` returns the chart sync runtime: the Updatecli image with
Python, PyYAML, Git, and Helm, running as the configured user with `source` at
`/work`. `with-updatecli-container` replaces it, for example to bind a registry
service in tests. Derive the replacement from `updatecli-container` so that
`source` stays at `/work`.

## Runtime Image Inputs

Helm operations use these constructor inputs:

- `helm_image_registry`: `docker.io`
- `helm_image_repository`: `alpine/helm`
- `helm_image_tag`: `3.18.6`
- `helm_container_user_id`: `65532`

Changed-chart operations also use Git runtime inputs:

- `git_image_registry`: `docker.io`
- `git_image_repository`: `alpine/git`
- `git_image_tag`: `2.52.0`
- `git_container_user_id`: `65532`

Helm unittest operations use these constructor inputs:

- `helm_unittest_image_registry`: `docker.io`
- `helm_unittest_image_repository`: `helmunittest/helm-unittest`
- `helm_unittest_image_tag`: `4.2.0-1.1.0`
- `helm_unittest_container_user_id`: `65532`

Chart sync operations use these constructor inputs:

- `updatecli_image_registry`: `ghcr.io`
- `updatecli_image_repository`: `riftonix/container-images/updatecli-python-nodejs`
- `updatecli_image_tag`: `py3.14-node26-updatecli0.123.0-pyyaml6.0.3-helm4.3.2`
- `updatecli_container_user_id`: `65532`

`verify-chart` uses the resolved chart directory only. `publish-chart` uses the
resolved chart directory for Helm operations and scenario-level `source` as the
Git repository for release tag operations.

Because these inputs are part of the public scenario API, release changes to
them under a new scenario tag.

## License

See the repository root LICENSE file.
