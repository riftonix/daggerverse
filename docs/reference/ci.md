# CI And Module Test Conventions

## Pull Request CI

Pull request CI is defined in `.github/workflows/ci.yaml`.

The workflow targets pull requests to the repository default branch and uses `dagger/dagger-for-github` with Dagger CLI `0.20.6`.

CI discovers tested modules by looking for:

```text
modules/<module>/tests/dagger.json
```

Only modules with that file are included in the test matrix. Modules without Dagger test modules are skipped instead of failing CI.

## Module Test Layout

When adding Dagger-native tests for a module, place them next to the module:

```text
modules/<module>/tests/
├── dagger.json
├── pyproject.toml
└── src/
```

The test module should depend on its parent module through a local dependency and call the parent public API from test functions.

The test module should expose an aggregate function named `all` for CI.

For practical implementation guidance, see [Write Dagger CI modules and tests](../how-to/write-dagger-ci-modules-and-tests.md).

## Command Interface

The root `Makefile` is the canonical command interface for local and CI checks:

```bash
make tests <module>
make lint-check [module]
make format-check [module]
```

CI should call these commands instead of duplicating raw `dagger call` invocations in workflow YAML.
