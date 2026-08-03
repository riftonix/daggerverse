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

`verify-chart` uses the resolved chart directory only. `publish-chart` uses the
resolved chart directory for Helm operations and scenario-level `source` as the
Git repository for release tag operations.

Because these inputs are part of the public scenario API, release changes to
them under a new scenario tag.

## License

See the repository root LICENSE file.
