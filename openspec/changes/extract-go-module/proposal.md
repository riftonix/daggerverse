# Extract a Reusable Go Module and Release Go CI

## Why

`go-ci` currently owns both the Go toolchain setup and the verification workflow, so another Dagger caller cannot reuse its individual Go checks. The first two consumers are still testing commit-pinned workflows in open pull requests; they need to move to the standard release-tagged CI flow.

## What Changes

### Scope

- Add a local `modules/go` with independently callable Go checks and the repository's runtime image and container user inputs.
- Make `scenarios/go-ci` delegate to that module, retain `verify-app` as its only public workflow, and expose `go_container_user_id` alongside the existing Go image inputs.
- Resolve the consumer verification blockers, release the scenario, and finish adoption in the existing `kelm` and `kafgres` pull requests with Renovate-managed scenario tags.

### Non-Goals

- Publish Go application binaries or OCI images, add build profiles, or change release workflows for the applications.

## Capabilities

### New Capabilities

- `go-module`: Reusable Go formatting, testing, and application compilation primitives with configurable runtime selection.

### Modified Capabilities

- `go-ci-scenario`: Compose the local Go module, allow caller-selected Go container users, and complete tagged adoption in the two consumer workflows.

## Impact

### Systems and Components

- Adds `modules/go` and its contract tests. Updates `scenarios/go-ci` and its contract tests.
- Updates [kelm #36](https://github.com/riftonix/kelm/pull/36) and [kafgres #27](https://github.com/riftonix/kafgres/pull/27), including their GitHub Actions workflows and Renovate configuration where needed.
