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
dagger -m ./scenarios/helm-ci call helm-verify \
  --source=./modules/helm/tests/charts/ns-configurator
```

Verify changed chart directories:

```bash
dagger -m ./scenarios/helm-ci call helm-verify-changed-charts \
  --source=. \
  --target-branch=master \
  --charts-path=modules/helm/tests/charts
```

## License

See the repository root LICENSE file.
