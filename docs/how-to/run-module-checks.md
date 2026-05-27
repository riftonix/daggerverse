# Run Module And Scenario Checks

Use the root `Makefile` as the local entrypoint for supported module and scenario checks.

## Run Tests

Run tests for a module that has a Dagger test module:

```bash
make tests module helm
```

Run tests for a scenario that has a Dagger test module:

```bash
make tests scenario container-images
```

These commands enter the neighboring `tests` Dagger module and call its aggregate `all` function.

Components without `<root>/<name>/tests/dagger.json` do not have Dagger-native tests yet. Add a neighboring test module before wiring them into `make tests <module|scenario> <name>`.

## Run Lint And Format

Fix Ruff lint issues for all Python components under `modules/` and `scenarios/`:

```bash
make lint
```

Fix Ruff lint issues for one module:

```bash
make lint module helm
```

Fix Ruff lint issues for one scenario:

```bash
make lint scenario container-images
```

Format all Python components:

```bash
make format
```

Format one module:

```bash
make format module docker
```

Format one scenario:

```bash
make format scenario container-images
```

Check Ruff lint for all Python components:

```bash
make lint-check
```

Check Ruff lint for one module:

```bash
make lint-check module helm
```

Check Ruff lint for one scenario:

```bash
make lint-check scenario container-images
```

Check formatting for one module:

```bash
make format-check module helm
```

Check formatting for one scenario:

```bash
make format-check scenario container-images
```

## CI Entry Point

GitHub Actions uses the same command shape as local development. The pull request workflow discovers modules with Dagger test modules and runs:

```bash
make lint-check
make format-check
make tests <kind> <name>
```

The explicit component kind keeps module and scenario names unambiguous.
