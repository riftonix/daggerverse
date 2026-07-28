# Helm Unittest Module Reference

`modules/helm-unittest` runs Helm chart unit tests with the public `helmunittest/helm-unittest` runtime image.

## Runtime Defaults

- Path: `modules/helm-unittest`
- Main source: `modules/helm-unittest/src/helm_unittest/main.py`
- Default image registry: `docker.io`
- Default image repository: `helmunittest/helm-unittest`
- Default image tag: `4.2.0-1.1.0`
- Default container user: `65532`
- Chart workdir: `/tmp/helm-unittest/chart`

The module exposes `image_registry`, `image_repository`, `image_tag`, and `container_user_id` constructor inputs so callers can use mirrored runtimes without changing the public function contract.

## Functions

- `container()` returns the configured runtime container with the chart mounted at `/tmp/helm-unittest/chart`.
- `with_dependency_update()` runs `helm dependency update .` before later Helm unittest calls and returns the module instance for chaining.
- `has_suites(suite_files: list[str] | None = None)` reports whether the chart contains a suite matching the effective patterns.
- `test(color: bool = False, suite_files: list[str] | None = None)` runs Helm unittest for the supplied chart directory and returns command output on success.

When `suite_files` is omitted, both discovery and execution use
`tests/**/*_test.yaml` and `tests/**/*_test.yml`. Custom patterns replace those
defaults. Each effective pattern is passed through a separate `-f` option. An
explicit empty list makes `has_suites()` return false so composing workflows can
skip execution.

## Example

```bash
dagger -m ./modules/helm-unittest call \
  --source=./charts/mychart \
  test
```

Run dependency update first when the chart declares dependencies:

```bash
dagger -m ./modules/helm-unittest call \
  --source=./charts/mychart \
  with-dependency-update \
  test
```

Select one or more suite patterns:

```bash
dagger -m ./modules/helm-unittest call \
  --source=./charts/mychart \
  test \
  --suite-files='tests/units/*_test.yaml' \
  --suite-files='tests/components/*_test.yml'
```

## Tests

Run the module tests from the repository root:

```bash
make tests module helm-unittest
```
