# Get Started With The Helm Module

This tutorial runs the Helm module against the sample chart that is stored in this repository.

## Prerequisites

- Dagger CLI is installed.
- Docker or another Dagger-compatible container runtime is available.
- You are running commands from the repository root.

## Run Helm Lint

Run the lint function against the sample chart:

```bash
dagger -m ./modules/helm call lint --source=./modules/helm/tests/charts/ns-configurator --strict=true
```

The command mounts the sample chart into the Helm module container and runs `helm lint . --strict`.

## Render Templates

Render the same chart:

```bash
dagger -m ./modules/helm call template --source=./modules/helm/tests/charts/ns-configurator --release-name=ci-release
```

The output should contain the rendered Kubernetes manifests for the sample chart.

## Run The Pipeline Wrapper

Run the higher-level pipelines module, which calls the Helm module internally:

```bash
dagger -m ./modules/pipelines call helm-verify --source=./modules/helm/tests/charts/ns-configurator
```

Use this command shape when you want the same check that CI orchestration uses.
