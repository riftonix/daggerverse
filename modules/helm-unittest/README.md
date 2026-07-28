# Helm Unittest Dagger Module

Containerized Helm unittest tooling for Dagger pipelines. This module wraps the public `helmunittest/helm-unittest` runtime and exposes chart unit test execution with optional dependency update chaining.

Run suites matching the module defaults, `tests/**/*_test.yaml` and
`tests/**/*_test.yml`:

```bash
dagger -m ./modules/helm-unittest call \
  --source=./charts/mychart \
  test
```

Select suites by repeating `--suite-files`:

```bash
dagger -m ./modules/helm-unittest call \
  --source=./charts/mychart \
  test \
  --suite-files='tests/units/*_test.yaml' \
  --suite-files='tests/components/*_test.yml'
```

The module uses the same effective patterns for `has-suites` discovery and
`test` execution. Custom patterns replace the defaults, and an explicit empty
list makes `has-suites` return false.

For full repository documentation, see [../../docs/README.md](../../docs/README.md). For Helm unittest details, see [../../docs/reference/helm-unittest.md](../../docs/reference/helm-unittest.md).
