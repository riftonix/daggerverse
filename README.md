# Daggerverse

Collection of Dagger CI modules. Each module lives under `modules/` and can be used independently.

## Documentation

The main documentation source is [docs/README.md](docs/README.md). It includes the recommended learning path, how-to guides, reference material, and design explanations.

## Modules

- **helm** - linting, templating, packaging, and publishing Helm charts.
  - https://github.com/riftonix/daggerverse/modules/helm
- **kind** - base container with `kind` installed for local k8s usage.
  - https://github.com/riftonix/daggerverse/modules/kind
- **opentofu** - linting and validation for IaC via OpenTofu.
  - https://github.com/riftonix/daggerverse/modules/opentofu
- **ssh** - SSH client in a container with key setup helpers.
  - https://github.com/riftonix/daggerverse/modules/ssh
- **git** - detect changed paths/directories in a git repository.
  - https://github.com/riftonix/daggerverse/modules/git
- **pipelines** - CI orchestration on top of modules (currently helm + git).
  - https://github.com/riftonix/daggerverse/modules/pipelines

## Requirements

You need to install [dagger-ci](https://docs.dagger.io/getting-started/installation/) to start working with modules.

## Quick start

Example module call:

```bash
dagger -m ./modules/helm call --source=./modules/helm/tests/charts/ns-configurator lint
```
