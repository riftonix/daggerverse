## ADDED Requirements

### Requirement: Helm CI Runtime Image Inputs
The Helm CI scenario SHALL expose runtime image inputs for the Helm and Git modules it composes.

#### Scenario: Caller configures Helm runtime image
- **WHEN** a caller invokes Helm chart verification or publication through the Helm CI scenario
- **THEN** the scenario SHALL use `helm_image_registry`, `helm_image_repository`, `helm_image_tag`, and `helm_container_user_id` when creating the Helm module

#### Scenario: Caller configures Git runtime image
- **WHEN** a caller invokes changed-chart verification through the Helm CI scenario
- **THEN** the scenario SHALL use `git_image_registry`, `git_image_repository`, `git_image_tag`, and `git_container_user_id` when creating the Git module

#### Scenario: Single-chart workflow does not require Git image inputs
- **WHEN** a caller invokes `helm-verify` or `helm-publish` for one chart directory
- **THEN** Git runtime image inputs SHALL remain available on the scenario API
- **AND** the scenario SHALL NOT invoke the Git module for those operations

#### Scenario: Runtime inputs do not expose module object types
- **WHEN** callers configure Helm CI runtime images
- **THEN** they SHALL pass primitive image input values
- **AND** the scenario SHALL NOT require callers to pass Helm or Git module object values
