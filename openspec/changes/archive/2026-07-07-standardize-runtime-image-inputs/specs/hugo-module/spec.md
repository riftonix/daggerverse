## ADDED Requirements

### Requirement: Hugo Runtime Image Inputs
The Hugo module SHALL expose the standard runtime image inputs for the container used to execute Hugo.

#### Scenario: Caller overrides Hugo image tag
- **WHEN** a caller creates the Hugo module with `image_registry`, `image_repository`, `image_tag`, or `user_id`
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
