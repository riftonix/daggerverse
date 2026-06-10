## ADDED Requirements

### Requirement: Static Site Hugo Runtime Image Inputs
The static-site scenario SHALL expose Hugo runtime image inputs on its public constructor when Hugo is a supported engine.

#### Scenario: Construct static-site scenario with Hugo image inputs
- **WHEN** a caller constructs the static-site scenario for Hugo-backed operations
- **THEN** the constructor SHALL accept `hugo_image_registry`, `hugo_image_repository`, `hugo_image_tag`, and `hugo_user_id`
- **AND** each input SHALL default to the Hugo module default for the same runtime image field

#### Scenario: Verify passes Hugo image inputs
- **WHEN** a caller verifies a Hugo site through the static-site scenario
- **THEN** the scenario SHALL pass the configured Hugo runtime image inputs to the Hugo module
- **AND** the scenario SHALL pass the configured Hugo theme URL to the Hugo module

#### Scenario: Render passes Hugo image inputs
- **WHEN** a caller renders a Hugo site through the static-site scenario
- **THEN** the scenario SHALL pass the configured Hugo runtime image inputs to the Hugo module
- **AND** the rendered output SHALL come from the configured Hugo execution image

#### Scenario: Static-site workflow pins Hugo image tag
- **WHEN** a CI workflow needs reproducible Hugo rendering
- **THEN** it SHALL be able to pin the Hugo runtime through `hugo_image_tag`
- **AND** the pin SHALL be visible in the workflow rather than hidden in the Hugo module dependency default
