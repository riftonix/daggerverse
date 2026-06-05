# Repository Layout

```text
.
├── docs/
│   ├── tutorials/
│   ├── how-to/
│   ├── reference/
│   └── explanation/
├── modules/
│   ├── git/
│   ├── helm/
│   ├── hugo/
│   ├── kind/
│   ├── opentofu/
│   └── ssh/
├── scenarios/
│   ├── container-images/
│   └── helm-ci/
├── README.md
└── LICENSE
```

## `docs/`

Repository-level documentation. This is the primary source for learning paths, cross-module workflows, reference material, and design explanations.

## `modules/`

Each child directory is an independent Dagger module. A module directory contains its own `dagger.json`, Python project files, source package, optional tests, and a short README.

When a module has Dagger-native tests, they live under `modules/<name>/tests` as a neighboring Dagger module.

Reusable modules should expose tool primitives, not complete provider-specific CI jobs. Modules are leaf building blocks: they must not import repository scenarios or other repository modules.

## `scenarios/`

Ready-to-run CI jobs live under `scenarios/<name>`. Scenarios compose reusable modules or other scenarios for concrete workflows such as Helm chart verification, container image verification, or publication in GitHub Actions and GitLab CI.

Scenarios should pin and test the versions of the building blocks they compose. A scenario may use module-specific objects internally, but its public API should expose stable Dagger primitives or scenario-owned spec/result objects rather than object types from implementation modules. This lets users compose released scenarios and modules independently without type collisions between different versions of the same module.

`scenarios/helm-ci` composes the Helm and Git modules into portable Helm chart verification and publication workflows.

## `.github/workflows/`

GitHub Actions workflows. Pull request CI discovers modules with `modules/<name>/tests/dagger.json` and scenarios with `scenarios/<name>/tests/dagger.json`, then runs their checks through the root `Makefile`.

## `current_docs/`

Local copy of upstream Dagger documentation material. It is not the primary documentation for this repository.
