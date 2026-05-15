# Run Module Checks

Use the root `Makefile` as the local entrypoint for supported module checks.

## Run Tests

Run tests for a module that has a Dagger test module:

```bash
make tests helm
```

This enters `modules/helm/tests` and calls the test module aggregate function.

Modules without `modules/<name>/tests/dagger.json` do not have Dagger-native tests yet. Add a neighboring test module before wiring them into `make tests <module>`.

## Run Lint And Format

Run Ruff lint for all modules:

```bash
make lint
```

Run Ruff lint for one module:

```bash
make lint helm
```

Format all modules:

```bash
make format
```

Check formatting for one module:

```bash
make format-check helm
```

## CI Entry Point

GitHub Actions uses the same command shape as local development. The pull request workflow discovers modules with Dagger test modules and runs:

```bash
make tests <module>
```

At the moment, `helm` is the tested module.
