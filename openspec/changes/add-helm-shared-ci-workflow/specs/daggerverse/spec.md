## ADDED Requirements

### Requirement: New image-backed modules use split runtime image inputs
New reusable Dagger modules that execute a tool from a container image SHALL expose runtime image identity and container user settings through split constructor inputs.

#### Scenario: Construct new image-backed module
- **WHEN** a new reusable module wraps a containerized tool runtime
- **THEN** its public constructor SHALL expose `image_registry`, `image_repository`, `image_tag`, and `container_user_id` inputs
- **AND** it SHALL NOT expose `user_id` for new public APIs
- **AND** it SHALL NOT require callers to pass a combined image reference string for the runtime image

#### Scenario: Build runtime image reference
- **WHEN** the module creates the runtime container
- **THEN** it SHALL build the image reference from `image_registry`, `image_repository`, and `image_tag`
- **AND** it SHALL set the container user from `container_user_id`

### Requirement: New image-backed modules define runtime image defaults as constants
New reusable Dagger modules that execute a tool from a container image SHALL define module-level constants for runtime image defaults.

#### Scenario: Define default runtime constants
- **WHEN** a new image-backed module is implemented
- **THEN** it SHALL define `DEFAULT_IMAGE_REGISTRY`, `DEFAULT_IMAGE_REPOSITORY`, `DEFAULT_IMAGE_TAG`, and `DEFAULT_CONTAINER_USER_ID`
- **AND** the constructor default values SHALL reference those constants

#### Scenario: Use pinned public runtime defaults
- **WHEN** a new image-backed module defines default runtime image values
- **THEN** the default runtime image SHALL be public unless a design explicitly justifies a private default
- **AND** `DEFAULT_IMAGE_TAG` SHALL be pinned to a concrete tag instead of `latest`

### Requirement: New image-backed module tests cover runtime defaults and overrides
New reusable Dagger modules that execute a tool from a container image SHALL test their default runtime image behavior and override inputs when practical.

#### Scenario: Test default runtime image
- **WHEN** Dagger-native tests are added for a new image-backed module
- **THEN** the tests SHALL exercise the module with default runtime image inputs
- **AND** default runtime image failures SHALL fail the module test aggregate

#### Scenario: Test runtime image override contract
- **WHEN** a new image-backed module exposes runtime image override inputs
- **THEN** Dagger-native tests SHALL cover override wiring when a deterministic test image or tag is available
- **AND** tests SHALL verify that overriding image identity or `container_user_id` does not require changing the module public function contract
