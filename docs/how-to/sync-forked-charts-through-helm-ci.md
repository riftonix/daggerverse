# Sync Forked Charts Through Helm CI

Use the `helm-ci` chart sync functions when a repository keeps forks of
upstream Helm charts and needs to pull upstream releases into them without
losing local edits. The scenario runs one Updatecli pipeline per component
through `modules/updatecli`, either locally or as one GitHub pull request per
component.

For each component, the scenario lists the upstream OCI tags, selects the
highest stable version that matches the version filter, and merges the upstream
change between the pinned and the selected package into the fork with a 3-way
Git merge. Fork edits survive, conflicts fail the component, and only the
component directory and its pin are written.

## Describe The Components

The configuration is a YAML file in the repository, `updatecli/values.yaml` by
default. Pass `--config-path` to use another file.

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

The keys mean the following:

- `upstream.registry` is the upstream OCI registry and project. The scenario
  requests anonymous Bearer tokens when the registry asks for them.
- `upstream.versionfilter` is the default filter: a space-separated list of
  `>=`, `>`, `<=`, `<`, or `=` comparisons with `X.Y.Z` versions. Prerelease
  and signature tags are never candidates.
- `upstream.exclude` lists exact chart-relative paths that are never
  synchronized. `charts/` and `Chart.lock` are always left out of the merge.
- `upstream.plainhttp` switches the registry to plain HTTP, for local test
  registries.
- `home` is the fork repository URL. Links to `https://github.com/nixys/<upstream>`
  become `<home>/tree/master/<component path>`.
- `rewrite` holds shared text rules with `from` or `regex` (Python syntax),
  `to`, and an optional chart-relative `file`. Binary files are not rewritten.
- `components` maps component IDs to overrides. An empty entry means
  `libs/<id>`, the upstream chart `nuc-<id>`, and the default filter. Component
  `exclude` entries extend the shared list, and component `rewrite` rules run
  after the shared ones.

Rewrites and exclusions apply to both upstream packages before the merge. An
upstream release that changes only removed or rewritten content, such as
`Chart.yaml` annotations, therefore produces a change of `version` alone.

Each component also needs a pin at `<config directory>/pins/<id>.json` that
records the upstream package the fork was last synchronized with:

```json
{
  "version": "1.0.4",
  "digest": "sha256:..."
}
```

The scenario validates the whole configuration and every pin before running any
pipeline and reports all problems in one error. The pinned package must still
have the pinned digest.

## Preview And Synchronize Locally

Every chart sync function accepts repeated `--components` to select component
IDs. Without it, all components run.

Preview pending updates without writing files:

```bash
dagger -m ./scenarios/helm-ci call --source=. sync-charts-diff --components=common
```

Synchronize and export the result into the working tree:

```bash
dagger -m ./scenarios/helm-ci call --source=. sync-charts --components=traefik export --path=.
```

A component whose pin is equal to or newer than the selected version is
reported as unchanged. A failing component fails the call but does not stop the
other components.

## Open Pull Requests From CI

`sync-charts-update` opens or updates one pull request per changed component
from the working branch `updatecli_<branch>_upstream-<id>`:

```bash
dagger -m ./scenarios/helm-ci call --source=. \
  sync-charts-update \
  --github-token=env://GITHUB_TOKEN \
  --repository=example/helm-fork \
  --branch=master
```

The token reaches Updatecli only as a secret variable. Commits are created
through the GitHub API, so the GitHub Actions built-in token is enough when the
job has `contents` and `pull-requests` write permissions. Check out the same
branch that you pass as `--branch`.

Pull requests created with the built-in token do not start `pull_request`
workflows. Give the job `actions: write` as well, add `workflow_dispatch` to the
CI workflow, and dispatch it for each open update branch after the sync step:

```bash
gh pr list --state open --json headRefName \
  --jq '.[].headRefName | select(startswith("updatecli_master_upstream-"))' |
  while read -r ref; do gh workflow run ci.yaml --ref "$ref"; done
```

Use `sync-charts-manifest --repository=<owner/name> --branch=<branch>` to
inspect the rendered Updatecli manifest. It never contains token values.

The scenario does not schedule runs, trigger CI, enable auto-merge, or merge.
The caller workflow owns the schedule, review, and merge order.

## Replace The Runtime Container

Chart sync runs in the Updatecli runtime image configured by the
`updatecli_image_*` and `updatecli_container_user_id` constructor inputs. The
default image provides Updatecli, Helm, Git, and Python with PyYAML.

`updatecli-container` returns that runtime with `source` at `/work`.
`with-updatecli-container` replaces it, for example to bind a local registry
service in tests. Derive the replacement from `updatecli-container` so that
`source` stays at `/work`.

See the [Updatecli module reference](../reference/updatecli.md) for the
underlying runtime and [Runtime image input conventions](../reference/runtime-images.md)
for image pinning.
