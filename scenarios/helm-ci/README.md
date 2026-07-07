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
- Helm chart publish to OCI
- Run checks only for changed directories through the Git module
- Verify changed charts from charts/libs directories

## Quick Start

Verify a single chart:

```bash
dagger -m ./scenarios/helm-ci call \
  --helm-image-tag=3.18.6 \
  helm-verify \
  --source=./modules/helm/tests/charts/ns-configurator
```

Verify changed chart directories:

```bash
dagger -m ./scenarios/helm-ci call \
  --helm-image-tag=3.18.6 \
  --git-image-tag=2.52.0 \
  helm-verify-changed-charts \
  --source=. \
  --target-branch=master \
  --charts-path=modules/helm/tests/charts
```

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

`helm-verify` and `helm-publish` do not invoke Git. Pin both Helm and Git image
tags for reproducible changed-chart checks or mirrored-registry runs.

Because these inputs are part of the public scenario API, release changes to
them under a new scenario tag.

## License

See the repository root LICENSE file.
