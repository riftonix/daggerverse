# Add Go CI Verification

## Why

The pull request workflows in `riftonix/kelm` and `riftonix/kafgres` currently report success without checking the Go code. Both repositories have one root Go module and one application, so they can share a single verification entrypoint without the component discovery or matrix used by `helm-ci`.

## What Changes

### Goals

- Give both repositories a provider-neutral verification workflow that can run locally or on a pull request.

### Scope

- Add `scenarios/go-ci` with one public workflow, `verify-app`, for formatting checks, tests, and compilation of a caller-selected Go application.
- Add Dagger-native tests and a scenario README with call examples for both consumers.
- Replace the placeholder pull request checks in `kelm` and `kafgres` with calls to the same versioned scenario, and configure Renovate to keep those scenario pins up to date.

### Non-Goals

- Publish binaries or OCI images, create release tags, or select a release version. A future change will cover both publication outputs and the migration from `ko` to [Cloud Native Buildpacks](https://buildpacks.io/).
- Add Updatecli, component discovery, changed-path filtering, or monorepo matrix orchestration.
- Add Helm checks for Kelm or start external services for Kafgres integration tests.

## Capabilities

### New Capabilities

- `go-ci-scenario`: Verify one Go application from one root module and define how the first two GitHub Actions consumers adopt and update the scenario pin.

### Modified Capabilities

None.

## Impact

### Users and Business Processes

- Pull requests to `master` in `riftonix/kelm` and `riftonix/kafgres` use the shared verification entrypoint instead of an unconditional success check.

### Systems and Components

- Adds a new scenario under `scenarios/go-ci`, with no changes to existing scenario or module APIs.
- Updates `.github/workflows/ci.yaml` and `renovate.json` in both consumer repositories; `helm-shared` remains unchanged.
