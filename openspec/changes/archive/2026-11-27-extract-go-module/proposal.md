# Extract a Reusable Go Module and Release Go CI

## Why

The original `go-ci` owned both the Go toolchain setup and the verification workflow, so another Dagger caller could not reuse its individual Go checks. Kafgres needed to move its preview workflow from a commit SHA to the standard release-tagged CI flow.

## What Changes

### Scope

- Add a local `modules/go` with independently callable Go checks and the repository's runtime image and container user inputs.
- Make `scenarios/go-ci` delegate to that module, retain `verify-app` as its only public workflow, and expose `go_container_user_id` alongside the existing Go image inputs.
- Release the scenario and complete adoption in `kafgres` with a Renovate-managed scenario tag.

### Non-Goals

- Publish Go application binaries or OCI images, add build profiles, or change release workflows for the applications.
- Complete Kelm adoption or fix its remaining CI failure. [kelm #36](https://github.com/riftonix/kelm/pull/36) remains open for separate work.

## Capabilities

### New Capabilities

- `go-module`: Reusable Go formatting, testing, and application compilation primitives with configurable runtime selection.

### Modified Capabilities

- `go-ci-scenario`: Compose the local Go module, allow caller-selected Go container users, and complete tagged adoption in Kafgres.

## Impact

### Systems and Components

- Adds `modules/go` and its contract tests. Updates `scenarios/go-ci` and its contract tests.
- Updates the GitHub Actions workflow and Renovate configuration through [kafgres #27](https://github.com/riftonix/kafgres/pull/27).
