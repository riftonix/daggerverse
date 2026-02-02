# Daggerverse

Collection of Dagger CI modules. Each module lives in its own directory and can be used independently.

## Modules

- **helm** — linting, templating, packaging, and publishing Helm charts.
  - https://github.com/riftonix/daggerverse/helm
- **kind** — base container with `kind` installed for local k8s usage.
  - https://github.com/riftonix/daggerverse/kind
- **opentofu** — linting and validation for IaC via OpenTofu.
  - https://github.com/riftonix/daggerverse/opentofu
- **ssh** — SSH client in a container with key setup helpers.
  - https://github.com/riftonix/daggerverse/ssh
- **git** — detect changed paths/directories in a git repository.
  - https://github.com/riftonix/daggerverse/git
- **pipelines** — CI orchestration on top of modules (currently helm + git).
  - https://github.com/riftonix/daggerverse/pipelines

## Requirements

You need to install [dagger-ci](https://docs.dagger.io/getting-started/installation/) to start working with modules.

## Quick start

Example module call:

```bash
dagger -m ./helm call --source=./helm/tests/charts/ns-configurator lint
```
