## MODIFIED Requirements

### Requirement: OpenTofu Runtime Image Inputs
The OpenTofu module SHALL expose the standard runtime image inputs for the container used to execute the IaC tool.

#### Scenario: Caller overrides OpenTofu image tag
- **WHEN** a caller creates the OpenTofu module with `image_registry`, `image_repository`, or `image_tag`
- **THEN** the module SHALL use those values when constructing the OpenTofu execution container

#### Scenario: Caller uses default OpenTofu image
- **WHEN** a caller creates the OpenTofu module without overriding runtime image inputs
- **THEN** the module SHALL use the repository default OpenTofu image values

#### Scenario: Combined container image input is removed
- **WHEN** a caller uses the updated OpenTofu module API
- **THEN** the public constructor SHALL NOT accept `container_image` for the runtime image
- **AND** callers SHALL use `image_registry`, `image_repository`, and `image_tag` instead

## ADDED Requirements

### Requirement: OpenTofu Container User Input
The OpenTofu module SHALL expose `container_user_id` as an optional execution UID, separate from runtime image identity and `executor`.

#### Scenario: Caller configures OpenTofu container user
- **WHEN** a caller creates the OpenTofu module with `container_user_id`
- **THEN** the module SHALL run the configured IaC executor as that UID
- **AND** the public constructor SHALL NOT accept the legacy `user_id` input

#### Scenario: Caller uses the default OpenTofu container user
- **WHEN** a caller omits `container_user_id`
- **THEN** the module SHALL run as UID `65532`
