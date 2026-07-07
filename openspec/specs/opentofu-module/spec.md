## Purpose

Define the OpenTofu Dagger module contract for containerized IaC formatting,
initialization, and validation.

## Requirements

### Requirement: OpenTofu Runtime Image Inputs
The OpenTofu module SHALL expose the standard runtime image inputs for the container used to execute the IaC tool.

#### Scenario: Caller overrides OpenTofu image tag
- **WHEN** a caller creates the OpenTofu module with `image_registry`, `image_repository`, `image_tag`, or `user_id`
- **THEN** the module SHALL use those values when constructing the OpenTofu execution container

#### Scenario: Caller uses default OpenTofu image
- **WHEN** a caller creates the OpenTofu module without overriding runtime image inputs
- **THEN** the module SHALL use the repository default OpenTofu image values

#### Scenario: Combined container image input is removed
- **WHEN** a caller uses the updated OpenTofu module API
- **THEN** the public constructor SHALL NOT accept `container_image` for the runtime image
- **AND** callers SHALL use `image_registry`, `image_repository`, and `image_tag` instead

### Requirement: OpenTofu Executor Input
The OpenTofu module SHALL keep the IaC command selection separate from runtime image identity.

#### Scenario: Caller selects executor command
- **WHEN** a caller creates the OpenTofu module with `executor`
- **THEN** linting SHALL invoke that command inside the configured runtime image
- **AND** the executor value SHALL NOT change image registry, repository, tag, or user

#### Scenario: Executor command failure is reported against the configured image
- **WHEN** the OpenTofu module test invokes `lint` with the default runtime image and a non-existent `executor` command
- **THEN** the failure SHALL reference the non-existent executor command
- **AND** the default runtime image SHALL remain the configured image, proving executor selection is separate from image identity
