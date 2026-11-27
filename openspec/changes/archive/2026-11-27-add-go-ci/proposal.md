# Add Go CI Verification

## Why

The pull request workflows in `riftonix/kelm` and `riftonix/kafgres` currently report success without checking the Go code. Both repositories have one root Go module and one application, so they can share a single verification entrypoint without the component discovery or matrix used by `helm-ci`.

## What Changes

### Goals

- Give both repositories a provider-neutral verification workflow that can run locally or on a pull request.

### Scope

- Add `scenarios/go-ci` with one public workflow, `verify-app`, for formatting checks, tests, and compilation of a caller-selected Go application.
- Add Dagger-native tests and a scenario README with call examples for both consumers.
- Open pull requests in `kelm` and `kafgres` that replace the placeholder checks with calls to the scenario pinned by commit SHA and prepare the Renovate regex for versioned references.

### Non-Goals

- Publish binaries or OCI images, create release tags, or merge the consumer workflows. Scenario release and final adoption move to `extract-go-module`. Publication outputs and the migration from `ko` to [Cloud Native Buildpacks](https://buildpacks.io/) remain separate.
- Add Updatecli, component discovery, changed-path filtering, or monorepo matrix orchestration.
- Add Helm checks for Kelm or start external services for Kafgres integration tests.

## Capabilities

### New Capabilities

- `go-ci-scenario`: Verify one Go application from one root module.

### Modified Capabilities

None.

## Impact

### Users and Business Processes

- The open consumer pull requests exercise the shared verification entrypoint ahead of adoption on `master`.

### Systems and Components

- Adds a new scenario under `scenarios/go-ci`, with no changes to existing scenario or module APIs.
- Updates `.github/workflows/ci.yaml` and `renovate.json` in both consumer repositories; `helm-shared` remains unchanged.
