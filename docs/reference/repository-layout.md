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
│   ├── pipelines/
│   └── ssh/
├── README.md
└── LICENSE
```

## `docs/`

Repository-level documentation. This is the primary source for learning paths, cross-module workflows, reference material, and design explanations.

## `modules/`

Each child directory is an independent Dagger module. A module directory contains its own `dagger.json`, Python project files, source package, optional tests, and a short README.

When a module has Dagger-native tests, they live under `modules/<name>/tests` as a neighboring Dagger module.

## `.github/workflows/`

GitHub Actions workflows. Pull request CI discovers modules with `modules/<name>/tests/dagger.json` and runs their checks through the root `Makefile`.

## `current_docs/`

Local copy of upstream Dagger documentation material. It is not the primary documentation for this repository.
