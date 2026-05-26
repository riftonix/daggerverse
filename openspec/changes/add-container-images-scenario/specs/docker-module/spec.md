## ADDED Requirements

### Requirement: Docker module builds container images
The Docker module SHALL expose Dagger-native functions for building container images from caller-provided build contexts without requiring a Docker daemon.

#### Scenario: Build image from context
- **WHEN** a caller provides a source directory, context path, and Dockerfile path
- **THEN** the Docker module SHALL build the image using Dagger-native container build behavior
- **AND** build failures SHALL fail the function call

#### Scenario: Build image with optional parameters
- **WHEN** a caller provides optional target or build arguments
- **THEN** the Docker module SHALL apply those options to the image build

### Requirement: Docker module configures registry login
The Docker module SHALL expose a chainable `with_registry_login` function for registry authentication.

#### Scenario: Configure registry credentials
- **WHEN** a caller provides a registry address, username, and password secret
- **THEN** `with_registry_login` SHALL return a Docker module instance configured for subsequent registry operations
- **AND** the password SHALL NOT be exposed in returned output

### Requirement: Docker module publishes container images
The Docker module SHALL publish built images to caller-provided OCI image references.

#### Scenario: Publish image to OCI registry
- **WHEN** a caller provides a build context and destination image reference
- **THEN** the Docker module SHALL build the image and publish it to that image reference
- **AND** the returned result SHALL identify the published image reference or digest

#### Scenario: Publish image with registry login
- **WHEN** a caller configures registry login before publishing
- **THEN** the Docker module SHALL use those credentials for the publish operation

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
- **WHEN** a user or CI runs `make tests docker`
- **THEN** the Docker test module SHALL run its aggregate `all` function
- **AND** the tests SHALL call the parent Docker module through a local Dagger dependency

#### Scenario: Verify publish without external registry credentials
- **WHEN** the Docker test module verifies image publication
- **THEN** it SHALL publish to a local OCI registry service
- **AND** it SHALL NOT require GitHub Container Registry credentials
