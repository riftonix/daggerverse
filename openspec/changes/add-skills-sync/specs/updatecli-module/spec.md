# Updatecli Module Delta Specification

## Purpose

Provide a reusable Dagger module that runs Updatecli manifests in a configurable runtime container, so modules, scenarios, and CI workflows can detect and apply dependency or content updates without installing Updatecli locally.

## ADDED Requirements

### Requirement: Updatecli module location and runtime image inputs
The system SHALL provide the Updatecli module under `modules/updatecli` with public constructor inputs `image_registry`, `image_repository`, `image_tag`, and `container_user_id`. The default runtime image SHALL be the official Updatecli image at a Renovate-managed tag.

#### Scenario: Use the default runtime image
- **GIVEN** a caller does not provide runtime image inputs
- **WHEN** the caller runs any Updatecli module function
- **THEN** the module SHALL run Updatecli from `ghcr.io/updatecli/updatecli` at the module default tag

#### Scenario: Skip the Updatecli version check
- **GIVEN** any runtime image
- **WHEN** the caller runs any Updatecli module function that executes Updatecli
- **THEN** Updatecli SHALL run with its release version check disabled

#### Scenario: Override the runtime image
- **GIVEN** a caller provides `image_registry`, `image_repository`, `image_tag`, or `container_user_id`
- **WHEN** the caller runs any Updatecli module function
- **THEN** the module SHALL run Updatecli from the provided image reference as the provided container user

### Requirement: Updatecli module previews manifest changes
The system SHALL expose a function that runs a caller-provided Updatecli manifest with optional values files in dry-run mode and returns the Updatecli report.

#### Scenario: Preview a manifest with pending changes
- **GIVEN** a manifest whose target differs from its source value
- **WHEN** the caller runs the preview function
- **THEN** the returned report SHALL describe the pending change
- **AND** the working tree returned by the module SHALL remain unchanged

#### Scenario: Preview fails
- **GIVEN** a manifest that Updatecli cannot load or whose pipeline Updatecli reports as failed
- **WHEN** the caller runs the preview function
- **THEN** the function call SHALL fail with the Updatecli error output

#### Scenario: Preview a skipped pipeline
- **GIVEN** a manifest whose pipeline Updatecli reports as skipped, for example because its source failed
- **WHEN** the caller runs the preview function
- **THEN** the function call SHALL succeed
- **AND** the returned report SHALL contain the Updatecli output for the skipped pipeline

### Requirement: Updatecli module applies manifest changes
The system SHALL expose a function that runs a caller-provided Updatecli manifest with optional values files in apply mode and returns the Updatecli report.

#### Scenario: Apply a manifest with pending changes
- **GIVEN** a manifest whose target differs from its source value
- **WHEN** the caller runs the apply function
- **THEN** Updatecli SHALL apply the change, including any SCM commits and actions declared in the manifest
- **AND** the returned report SHALL describe the applied change

#### Scenario: Apply fails
- **GIVEN** a manifest whose pipeline Updatecli reports as failed
- **WHEN** the caller runs the apply function
- **THEN** the function call SHALL fail with the Updatecli error output

#### Scenario: Apply a skipped pipeline
- **GIVEN** a manifest whose pipeline Updatecli reports as skipped, for example because its source failed
- **WHEN** the caller runs the apply function
- **THEN** the function call SHALL succeed
- **AND** the returned report SHALL contain the Updatecli output for the skipped pipeline

### Requirement: Updatecli module operates on a caller-provided working tree
The system SHALL accept an optional `source` directory as the working directory for pipelines without an SCM and SHALL expose a function that returns that directory after applying a manifest.

#### Scenario: Return the updated working tree
- **GIVEN** a caller provides `source` and a manifest whose target writes a file relative to the working directory
- **WHEN** the caller requests the applied working tree
- **THEN** the returned directory SHALL contain the file changes made by the manifest

#### Scenario: Run without a working tree
- **GIVEN** a caller does not provide `source`
- **WHEN** the caller runs a manifest that uses only SCM-backed targets
- **THEN** the module SHALL run the manifest in an empty working directory

### Requirement: Updatecli module renders manifests
The system SHALL expose a function that returns the Updatecli rendering of a caller-provided manifest with optional values files, without running pipelines.

#### Scenario: Render a templated manifest
- **GIVEN** a templated manifest and a values file
- **WHEN** the caller runs the render function
- **THEN** the returned output SHALL contain the manifest with template values resolved

### Requirement: Updatecli module accepts secrets and runtime additions
The system SHALL let callers add secret environment variables, plain environment variables, and directories to the runtime container before running Updatecli. Secret values SHALL NOT appear in returned output.

#### Scenario: Provide an SCM token
- **GIVEN** a caller adds a secret environment variable named `UPDATECLI_GITHUB_TOKEN`
- **WHEN** the caller runs a manifest with a GitHub SCM
- **THEN** Updatecli SHALL receive the token through that environment variable
- **AND** the token value SHALL NOT appear in the returned report

#### Scenario: Provide helper files
- **GIVEN** a caller adds a directory with helper scripts at a container path
- **WHEN** a manifest shell resource calls a script from that path
- **THEN** the script SHALL be available to the shell resource

### Requirement: Updatecli module Dagger tests
The system SHALL provide a Dagger test module under `modules/updatecli/tests` whose aggregate `all()` function verifies preview, apply, applied working tree, and rendering without network access or credentials.

#### Scenario: Run Updatecli module tests
- **GIVEN** the Updatecli module test module
- **WHEN** a user or CI runs `make tests module updatecli`
- **THEN** the aggregate test SHALL run offline manifests that use local sources and targets
- **AND** any failed check SHALL fail the test run
