# Go Module Delta Specification

## Purpose

Provide independently callable Go checks for Dagger callers that verify source trees containing a root Go module.

## ADDED Requirements

### Requirement: Select the Go module runtime

The system SHALL expose `modules/go` as a reusable Dagger module with a required `source` directory and optional `image_registry`, `image_repository`, `image_tag`, and `container_user_id` inputs. The module SHALL provide a pinned public default image and run Go operations as the configured container user with separate module and build caches. Go SHALL use the toolchain from the selected image and ignore workspace configuration.

#### Scenario: Use the default runtime

- **WHEN** a caller runs a Go operation without runtime overrides
- **THEN** the module uses the pinned image and the default non-root user
- **AND** the execution user can write Go cache and temporary files

#### Scenario: Override the runtime image or user

- **WHEN** a caller supplies a compatible image or numeric container UID override
- **THEN** the module runs the operation with that selection and its writable caches

#### Scenario: Reject a toolchain below the module minimum

- **WHEN** the caller selects an image whose Go version is below the root `go.mod` minimum and runs an operation that loads the Go module
- **THEN** the operation fails with the Go version diagnostic without downloading another toolchain

### Requirement: Run Go checks independently

The system SHALL expose separate operations to validate an executable package, check formatting, run the root module's tests, and compile one executable. Each operation SHALL run independently, report its own failures, and leave the caller's source unchanged. Operations that load the Go module SHALL require a root `go.mod` and retain Go diagnostics on failure.

#### Scenario: Validate a local executable package

- **WHEN** a caller requests package validation for `.` or a path relative to the source root
- **THEN** validation succeeds only for one `main` package belonging to the root Go module
- **AND** a missing package, a package pattern, or a path outside the source is rejected with a package diagnostic

#### Scenario: Check source formatting

- **WHEN** the caller runs the formatting check
- **THEN** it reports the paths of unformatted Go files outside `.git` and `vendor` without rewriting them

#### Scenario: Run root module tests

- **WHEN** the caller runs the test operation
- **THEN** it runs `go test ./...` from the source root and fails if any selected test fails

#### Scenario: Compile an executable

- **WHEN** the caller requests compilation of one valid local `main` package
- **THEN** the module builds it using the selected toolchain's normal CGO and linker settings, with files such as `go:embed` inputs available
- **AND** a compilation or linking error fails the operation with a Go diagnostic

#### Scenario: Run module contract tests

- **WHEN** a contributor runs `make tests module go`
- **THEN** a neighboring Dagger test module invokes the Go module's public API through a local dependency
