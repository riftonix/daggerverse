# Run Helm Checks Through Helm CI

Use the `helm-ci` scenario when you want a CI-style wrapper around Helm chart
checks. The scenario composes `modules/helm` for Helm operations and
`modules/git` for changed-directory selection.

CI provider workflows own event triggers, branch selection, path selection, and
publish timing. Pass those decisions into the scenario as explicit inputs.

## Verify One Chart

```bash
dagger -m ./scenarios/helm-ci call \
  --helm-image-tag=3.18.6 \
  --source=./modules/helm/tests/charts/ns-configurator \
  verify-chart
```

The command runs Helm lint and template through the local Helm module dependency.
`source` must point directly to one chart directory containing `Chart.yaml`.
The scenario does not select a nested chart from a repository root.

By default, the Helm unittest module discovers and runs only files matching
`tests/**/*_test.yaml` or `tests/**/*_test.yml`. Helm CI uses the module's
discovery result to run or skip the step. Files such as `tests/e2e/kind.yaml`
do not enable the unittest step.

To replace the defaults, repeat `--unittest-suite-files` for each glob:

```bash
dagger -m ./scenarios/helm-ci call \
  --source=charts/app \
  verify-chart \
  --unittest-suite-files='tests/units/*_test.yaml' \
  --unittest-suite-files='tests/components/*_test.yml'
```

An explicit empty list selects no suites and skips Helm unittest. If no files
match the effective patterns, verification reports the unittest step as
skipped.

## Verify Changed Chart Components

Use the Git module to discover changed chart directories, then pass each directory to a separate `verify-chart` matrix job:

```bash
dagger -m ./modules/git call --silent --json \
  --source=. \
  get-changed-components \
  --base-ref=origin/master \
  --head-ref=HEAD \
  --component-roots='charts/*' \
  --component-roots='libs/*'
```

For each returned path, run:

```bash
dagger -m ./scenarios/helm-ci call \
  --source=charts/app \
  verify-chart
```

The CI provider owns matrix fan-out, retries, and per-chart logs.

`verify-chart` uses Helm and Helm unittest runtime image inputs. `publish-chart`
also uses the Git runtime image inputs because it checks and pushes the release
tag in the same call.

## Publish A Chart

```bash
GITHUB_TOKEN="$(gh auth token)" \
dagger -m ./scenarios/helm-ci call \
  --helm-image-tag=3.18.6 \
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

`registry-login` and `registry-password` are used only for OCI publication.
`git-token` is used to fetch and push the chart-scoped release tag. Supply both
registry fields together. The same GitHub token can be used for both secrets if
it has package write and repository contents write permissions.

`oci-url` specifies the complete destination without `oci://` or the chart name.
`registry-address` is optional; when omitted, Helm CI uses the host and optional
port from `oci-url` for registry login.

The scenario publishes the chart first, then calls the Git module to ensure the
release tag exists on the configured remote. It does not use GitHub APIs and
does not require a second Dagger invocation.

Use real Dagger secrets in CI instead of printing credentials in logs.
