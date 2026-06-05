# Daggerverse

Collection of reusable Dagger CI modules and ready-to-run scenarios.

Modules live under `modules/` and are self-contained building blocks. Scenarios
live under `scenarios/` and compose modules or other scenarios into concrete CI
workflows.

## Documentation

The main documentation source is [docs/README.md](docs/README.md). It includes the recommended learning path, how-to guides, reference material, and design explanations.

## Modules

- **docker** - Dagger-native Docker and OCI image build, smoke check, registry auth, and publish primitives.
  - https://github.com/riftonix/daggerverse/modules/docker
- **git** - detect changed paths/directories in a git repository.
  - https://github.com/riftonix/daggerverse/modules/git
- **helm** - linting, templating, packaging, and publishing Helm charts.
  - https://github.com/riftonix/daggerverse/modules/helm
- **kind** - base container with `kind` installed for local k8s usage.
  - https://github.com/riftonix/daggerverse/modules/kind
- **opentofu** - linting and validation for IaC via OpenTofu.
  - https://github.com/riftonix/daggerverse/modules/opentofu
- **ssh** - SSH client in a container with key setup helpers.
  - https://github.com/riftonix/daggerverse/modules/ssh

## Scenarios

- **container-images** - portable image verification and publication workflow using explicit context paths and image references.
  - https://github.com/riftonix/daggerverse/scenarios/container-images
- **helm-ci** - portable Helm chart verification and publication workflow using the Helm and Git modules.
  - https://github.com/riftonix/daggerverse/scenarios/helm-ci
- **static-site** - provider-neutral static-site verification and rendering workflow backed by static-site engine modules.
  - https://github.com/riftonix/daggerverse/scenarios/static-site

## Requirements

You need to install [dagger-ci](https://docs.dagger.io/getting-started/installation/) to start working with modules.

## Quick start

Example module call:

```bash
dagger -m ./modules/helm call --source=./modules/helm/tests/charts/ns-configurator lint
```

Run checks through the explicit component command form:

```bash
make tests module docker
make tests scenario container-images
make tests scenario helm-ci
make lint-check
make format-check
```
