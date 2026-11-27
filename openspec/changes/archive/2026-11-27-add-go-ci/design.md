# Add Go CI Verification Design

## Glossary and References

### References

- [`helm-ci` scenario](../../../../scenarios/helm-ci/README.md): reference for a provider-neutral Dagger verification entrypoint.
- [Daggerverse authoring guide](../../../../docs/how-to/write-dagger-ci-modules-and-tests.md): reference for source inputs, public Dagger types, and local contract tests.
- [`kelm/go.mod`](https://github.com/riftonix/kelm/blob/master/go.mod) and [`kafgres/go.mod`](https://github.com/riftonix/kafgres/blob/master/go.mod): toolchain requirements for the initial consumers.
- [`helm-shared` CI workflow](https://github.com/riftonix/helm-shared/blob/master/.github/workflows/ci.yaml) and [Renovate configuration](https://github.com/riftonix/helm-shared/blob/master/renovate.json): reference for pinned Dagger dependencies and the `CI Passed` job.
- [Upstream Dagger Go module](https://daggerverse.dev/mod/github.com/dagger/dagger/modules/go): alternative considered for test and build operations.

## Context

### Existing Technical Constraints

The checked `kelm` source declares `go 1.26.11`. The checked `kafgres` source declares `go 1.24.0` and separately recommends `toolchain go1.27.4`. In Go, the `go` directive sets the minimum and `toolchain` recommends a toolchain; the latter is not treated as another minimum in this scenario.

## Goals / Non-Goals

### Goals

- Keep verification reproducible: use the same selected toolchain and source snapshot for all steps.
- Keep the verification API independent of the future image builder and release workflow.

### Non-Goals

- Add a general-purpose Go tooling API or configure workspaces, private module credentials, integration services, or cross-compilation.

## Architecture and Component Boundaries

### Component Responsibilities

- `scenarios/go-ci` uses the Python SDK, like `helm-ci`. A private helper constructs the Go container; no additional runtime entrypoints are public.
- The caller supplies the checkout, selects the package, and decides when verification runs. The scenario does not check out repositories or interpret CI events.
- The consumer GitHub Actions workflows are thin adapters. Each checks out the pull request using `actions/checkout`, sets up the compatible Dagger CLI with `dagger/dagger-for-github`, and invokes one verification job with its fixed package path. Keep `permissions: contents: read`; no Git or registry publication tokens are needed.

## Interfaces

### Command-Line Interface

```bash
dagger -m ./scenarios/go-ci call --source=../kelm verify-app --package=./cmd/kelm
dagger -m ./scenarios/go-ci call --source=../kafgres verify-app --package=./cmd/kafgres
```

Use `--go-image-tag` before `verify-app` to override the default toolchain. The scenario exposes a text summary, not the internal container or its files.

## Error Handling

### Error Propagation and Mapping

Report an absent root `go.mod` before running the Go tools. Accept `.` or a path to a single package directory relative to the module root. Normalize the path and reject empty values, absolute paths, paths that escape the module, and package patterns before invoking Go. Use `go list` with the selected build environment to confirm the package is inside the root module and is `main`. Retain Go diagnostics when validation, testing, or compilation fails. On formatting failure, report the file list rather than rewriting the files or continuing to tests.

## Decisions

### Decision: Run the Go tools directly in one scenario-local container

Use `docker.io/library/golang:1.27.4` as the starting default because it covers the observed minimums and matches the Kafgres toolchain recommendation. Declare the default as split `DEFAULT_GO_IMAGE_*` constants with the repository's Docker Renovate annotation. Set `GOTOOLCHAIN=local` for image-based selection and `GOWORK=off` for root-module isolation. Mount the source at a fixed work directory and keep `GOMODCACHE` and `GOCACHE` on separate Dagger cache volumes outside it.

The upstream Dagger Go module has reusable test and build operations, but its default environment is Wolfi-based. To reuse it here, the scenario would still need a custom base image and a separate formatting check. Direct commands keep these three checks in one environment without adopting another module's runtime or creating a local `modules/go` wrapper before there is a second use case.

### Decision: Check formatting, tests, and compilation without producing release artifacts

Run `gofmt -l` over project Go files while excluding `.git` and `vendor` from the formatting scan. Keep the rest of the source available for both tests and compilation, including non-Go inputs and any vendored dependencies. Run package resolution, tests, and compilation in the same runtime environment. Set `-buildvcs=false` on test and build commands so their behavior does not depend on a Git checkout. Compile one application with `go build -o` to a temporary path outside the source directory and materialize the build before returning the summary. Do not return the binary from `verify-app`; a later release workflow can define its own binary and image artifacts without changing this API.

### Decision: Pin the scenario and preserve the CI gate

Replace the placeholder in each consumer's `.github/workflows/ci.yaml` with a `verify` job. Keep `ci-passed` and its display name `CI Passed`; use `needs: verify` and `if: ${{ always() }}` so the gate fails explicitly unless `needs.verify.result` is `success`. Unlike the Helm matrix, there is no valid skipped verification for a run of this workflow.

The preview pull requests pin `GO_CI_SCENARIO` to `github.com/riftonix/daggerverse/scenarios/go-ci@8f33d37296aa3f94c07ea344f301ab92fe070542`. The SHA pin has no `github-tags` annotation. `DAGGER_VERSION` uses the scenario-compatible CLI version and the Dagger datasource annotation used by `helm-shared`.

In both consumers' `renovate.json`, align the GitHub reference pattern in the existing CI regex manager with `helm-shared`: change `(?<currentValue>v?[0-9][^/\s]*)` to `v?(?<currentValue>[0-9][^/\s]*)` in the regular expression (preserve JSON escaping). The tag extractor returns numbers without `v`; keeping `v` outside `currentValue` preserves it when Renovate writes the next version. Leave the numeric pin pattern, other Renovate settings, and `helm-shared` unchanged.

## Risks / Trade-offs

- Existing source formatting or test failures will become visible when the consumer workflows adopt the scenario. Verify each consumer before making the new check a required status.
- A consumer can raise its minimum Go version before the default image is updated. It can select a compatible image tag explicitly without waiting for a scenario release.

## Migration Plan

### Rollout

The change ends with [kelm #36](https://github.com/riftonix/kelm/pull/36) and [kafgres #27](https://github.com/riftonix/kafgres/pull/27) open on the SHA pin. Kafgres passed the preview checks. Kelm passed formatting after a fix but its test run reported missing `go.sum` entries. The follow-up `extract-go-module` owns resolving the failed check, publishing a scenario tag, and completing adoption.

### Rollback

If downstream adoption needs to be rolled back, revert the downstream workflow change. No persisted data or existing Dagger API needs to be migrated.
