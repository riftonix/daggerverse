## Purpose

Describe the current Docker module behavior for reusable container image build, verification, registry authentication, and publication workflows.

## Requirements

### Requirement: Docker module builds container images

The Docker module SHALL expose Dagger-native functions for building container images from caller-provided build contexts without requiring a Docker daemon.

#### Scenario: Build image from context
- **WHEN** a caller provides a source directory, context path, and Dockerfile path
- **THEN** the Docker module SHALL build the image using Dagger-native container build behavior
- **AND** the build function SHALL return a `DockerBuild` object
- **AND** build failures SHALL fail the function call

#### Scenario: Build image with target and build arguments
- **WHEN** a caller provides optional target or build arguments in `KEY=VALUE` form
- **THEN** the Docker module SHALL apply those options to the image build
- **AND** build argument values containing `=` SHALL remain valid

#### Scenario: Reject invalid build argument
- **WHEN** a caller provides a build argument without a non-empty key and `=` separator
- **THEN** the Docker module SHALL fail with a clear validation error

#### Scenario: Build image for explicit platforms
- **WHEN** a caller provides one or more target platforms
- **THEN** the Docker module SHALL build platform variants for those platforms
- **AND** the build result SHALL retain the variants for publication

### Requirement: Docker module exposes build and image result objects

The Docker module SHALL model image workflows with separate `Docker`, `DockerBuild`, and `DockerImage` objects.

#### Scenario: Access built container
- **WHEN** a caller has a `DockerBuild` object
- **THEN** the caller SHALL be able to access the built container for the default platform

#### Scenario: Return published image object
- **WHEN** a caller publishes a `DockerBuild`
- **THEN** the publish function SHALL return a `DockerImage` object
- **AND** the object SHALL expose the published image reference

### Requirement: Docker module configures registry auth

The Docker module SHALL expose a chainable `with_registry_auth` function for registry authentication.

#### Scenario: Configure registry auth
- **WHEN** a caller provides a registry address, username, and password secret
- **THEN** `with_registry_auth` SHALL return a Docker module instance configured for subsequent registry operations
- **AND** the password SHALL NOT be exposed in returned output

### Requirement: Docker module publishes container images

The Docker module SHALL publish built images to caller-provided OCI image references through Dagger-native publish behavior.

#### Scenario: Publish image to OCI registry
- **WHEN** a caller provides a `DockerBuild` and one or more destination image references
- **THEN** the Docker module SHALL publish the image to those references
- **AND** the returned `DockerImage` SHALL identify the published image reference

#### Scenario: Publish image with registry auth
- **WHEN** a caller configures registry auth before publishing
- **THEN** the Docker module SHALL use those credentials for the publish operation

#### Scenario: Publish platform variants
- **WHEN** a `DockerBuild` contains platform variants
- **THEN** publication SHALL include those variants in the published image

#### Scenario: Dry-run publish wiring
- **WHEN** Docker module tests need to validate publish input and result wiring without a registry reachable by the Dagger engine
- **THEN** the Docker module SHALL provide a dry-run publish mode on `DockerBuild`
- **AND** dry-run publication SHALL validate image references and return a `DockerImage` without calling `Container.publish`

### Requirement: Docker module runs smoke checks

The Docker module SHALL provide an optional smoke-check function that runs a caller-provided command in the built image.

#### Scenario: Run smoke command
- **WHEN** a caller provides a build context and smoke command
- **THEN** the Docker module SHALL build the image and execute the command in the resulting container
- **AND** command failures SHALL fail the function call

#### Scenario: Skip smoke command
- **WHEN** a caller does not provide a smoke command
- **THEN** image verification SHALL require only a successful image build

### Requirement: Docker module has Dagger-native tests

The Docker module SHALL have a neighboring Dagger test module that validates public Docker behavior through the module public API.

#### Scenario: Run Docker module tests
- **WHEN** a user or CI runs `make tests module docker`
- **THEN** the Docker test module SHALL run its aggregate `all` function
- **AND** the tests SHALL call the parent Docker module through a local Dagger dependency

#### Scenario: Verify publish wiring without external registry credentials
- **WHEN** the Docker test module runs its default aggregate tests
- **THEN** it SHALL verify publish input and result wiring without requiring a real registry or GitHub Container Registry credentials
- **AND** it SHALL NOT require an ephemeral Dagger service registry for `Container.publish`
