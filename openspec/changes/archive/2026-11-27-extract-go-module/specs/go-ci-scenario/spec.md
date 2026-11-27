# Go CI Scenario Delta Specification

## MODIFIED Requirements

### Requirement: Follow the Daggerverse component standard

The system SHALL implement `go-ci` as a provider-neutral Dagger scenario under `scenarios/`, composing the reusable Go operations from `modules/go` as a local dependency. CI-provider adapters SHALL own event triggers and checkout policy. The scenario SHALL expose `verify-app` as its only public workflow and SHALL NOT expose dependency-owned types.

#### Scenario: Locate the Go CI component and its runtime inputs

- **WHEN** a contributor inspects the Go CI implementation
- **THEN** `scenarios/go-ci` contains its own `dagger.json`, Python SDK source and project metadata, and a README with CLI examples
- **AND** the primary input is a Dagger `Directory` named `source`
- **AND** the default tool image is pinned and Renovate-managed, with separate, tool-prefixed registry, repository, tag, and container user overrides
- **AND** the scenario delegates individual Go operations to `modules/go`

#### Scenario: Run Go CI contract tests

- **WHEN** a contributor or repository CI runs `make tests scenario go-ci`
- **THEN** it invokes `all` in the neighboring Dagger test module under `scenarios/go-ci/tests` without requiring caller inputs
- **AND** the test module exercises the scenario's public API through a local Dagger dependency

### Requirement: Select the verification runtime explicitly

The system SHALL provide a pinned public Go runtime image by default and accept `go_image_registry`, `go_image_repository`, `go_image_tag`, and `go_container_user_id` overrides. All verification steps SHALL use the selected runtime and user without automatically downloading a different Go toolchain or enabling workspace mode.

#### Scenario: Override the default runtime image

- **WHEN** the caller supplies a compatible alternate image registry, repository, or tag
- **THEN** verification uses that selection for formatting, testing, and building

#### Scenario: Override the Go container user

- **WHEN** a caller sets `go_container_user_id` to a supported numeric UID
- **THEN** all Go checks run as that UID and can use the module cache, build cache, and temporary build output

#### Scenario: Reject an insufficient Go version

- **GIVEN** the selected image contains a Go version below the minimum required by the root `go.mod`
- **WHEN** the caller invokes `verify-app`
- **THEN** verification fails with a toolchain diagnostic and does not download another Go version

## ADDED Requirements

### Requirement: Adopt Go CI in the Kafgres workflow

The system SHALL run `verify-app` once for pull requests targeting `master` in `riftonix/kafgres`. The workflow SHALL pass its repository root and application package to a released `go-ci` scenario. The existing `CI Passed` status SHALL report success only if verification succeeds.

#### Scenario: Verify the Kafgres application

- **GIVEN** a pull request targets `master` in `kafgres`
- **WHEN** its GitHub Actions CI workflow runs
- **THEN** it calls the released scenario once with `source=.` and `package=./cmd/kafgres`
- **AND** `CI Passed` fails if verification fails, is cancelled, or is skipped
- **AND** the workflow requires only read access to repository contents and no publication credentials

#### Scenario: Update only the Go CI scenario release pin

- **GIVEN** the Kafgres workflow pins `@scenarios/go-ci/vX.Y.Z`
- **WHEN** Renovate finds a newer compatible version from Git tags in `riftonix/daggerverse`
- **THEN** it considers only tags under `scenarios/go-ci/v`
- **AND** it replaces the version while preserving the `@scenarios/go-ci/v` prefix
