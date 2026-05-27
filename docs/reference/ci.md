# CI And Component Test Conventions

## Pull Request CI

Pull request CI is defined in `.github/workflows/ci.yaml`.

The workflow targets pull requests to the repository default branch and uses `dagger/dagger-for-github` with Dagger CLI `0.20.8`.

CI discovers tested modules and scenarios by looking for:

```text
modules/<module>/tests/dagger.json
scenarios/<scenario>/tests/dagger.json
```

Only components with that file are included in the test matrix. Modules or scenarios without Dagger test modules are skipped instead of failing CI.

## Test Layout

When adding Dagger-native tests for a module or scenario, place them next to the component:

```text
modules/<module>/tests/
├── dagger.json
├── pyproject.toml
└── src/
```

```text
scenarios/<scenario>/tests/
├── dagger.json
├── pyproject.toml
└── src/
```

The test module should depend on its parent component through a local dependency and call the parent public API from test functions.

The test module should expose an aggregate function named `all` for CI.

For practical implementation guidance, see [Write Dagger CI modules and tests](../how-to/write-dagger-ci-modules-and-tests.md).

## Command Interface

The root `Makefile` is the canonical command interface for local and CI checks:

```bash
make tests module <name>
make tests scenario <name>
make lint-check
make lint-check module <name>
make lint-check scenario <name>
make format-check
make format-check module <name>
make format-check scenario <name>
```

CI should call these commands instead of duplicating raw `dagger call` invocations in workflow YAML.
