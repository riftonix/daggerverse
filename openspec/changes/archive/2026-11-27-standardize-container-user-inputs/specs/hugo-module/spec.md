## ADDED Requirements

### Requirement: Hugo Container User Input
The Hugo module SHALL expose container execution user configuration through `container_user_id`.

#### Scenario: Caller configures Hugo container user
- **WHEN** a caller creates the Hugo module with `container_user_id`
- **THEN** the Hugo module SHALL run Hugo and mount the site source using that container user ID

#### Scenario: Hugo user_id input is removed
- **WHEN** a caller uses the updated Hugo module API
- **THEN** the public constructor SHALL NOT accept `user_id` for container execution user behavior
- **AND** callers SHALL use `container_user_id` instead

#### Scenario: Hugo image identity remains separate
- **WHEN** a caller configures the Hugo runtime image
- **THEN** image registry, repository, and tag inputs SHALL remain separate from `container_user_id`

## MODIFIED Requirements

### Requirement: Hugo Runtime Image Inputs
The Hugo module SHALL expose the standard runtime image inputs for the container used to execute Hugo.

#### Scenario: Caller overrides Hugo image tag
- **WHEN** a caller creates the Hugo module with `image_registry`, `image_repository`, or `image_tag`
- **THEN** the module SHALL use those values when constructing the Hugo execution container

#### Scenario: Caller uses default Hugo image
- **WHEN** a caller creates the Hugo module without overriding runtime image inputs
- **THEN** the module SHALL continue using the prepared Hugo Autoprefixer image defaults

#### Scenario: Hugo runtime image is visible to callers
- **WHEN** CI needs to synchronize Hugo site configuration with the image used to render the site
- **THEN** the required Hugo image tag SHALL be available as a public module input

#### Scenario: Hugo tests use configured runtime image inputs
- **WHEN** the Hugo test module runs direct Hugo module integration checks
- **THEN** direct Hugo module calls SHALL use the test module constructor runtime image inputs
- **AND** component module import rendering SHALL be covered in the Hugo test module rather than in the static-site scenario tests
