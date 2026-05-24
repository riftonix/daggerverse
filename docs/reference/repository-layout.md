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
│   └── helm-ci/
├── README.md
└── LICENSE
```

## `docs/`

Repository-level documentation. This is the primary source for learning paths, cross-module workflows, reference material, and design explanations.

## `modules/`

Each child directory is an independent Dagger module. A module directory contains its own `dagger.json`, Python project files, source package, optional tests, and a short README.

When a module has Dagger-native tests, they live under `modules/<name>/tests` as a neighboring Dagger module.

Reusable modules should expose tool primitives, not complete provider-specific CI jobs.

## `scenarios/`

Ready-to-run CI jobs live under `scenarios/<name>`. Scenarios compose reusable modules for concrete workflows such as Helm chart verification or publication in GitHub Actions and GitLab CI.

The existing `modules/pipelines` directory is transitional. It is a temporary Helm CI wrapper for a future scenario, but the final `scenarios/` layout should be defined in a separate proposal.

## `.github/workflows/`

GitHub Actions workflows. Pull request CI discovers modules with `modules/<name>/tests/dagger.json` and runs their checks through the root `Makefile`.

## `current_docs/`

Local copy of upstream Dagger documentation material. It is not the primary documentation for this repository.
