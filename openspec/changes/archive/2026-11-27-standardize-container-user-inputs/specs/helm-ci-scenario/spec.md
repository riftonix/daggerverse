## ADDED Requirements

### Requirement: Helm CI Container User Inputs
The Helm CI scenario SHALL expose prefixed container execution user inputs for the Helm and Git modules it composes.

#### Scenario: Caller configures Helm container user through Helm CI
- **WHEN** a caller invokes Helm chart verification or publication through Helm CI with `helm_container_user_id`
- **THEN** the scenario SHALL pass that value to the Helm module as `container_user_id`

#### Scenario: Caller configures Git container user through Helm CI
- **WHEN** a caller publishes a chart through Helm CI with `git_container_user_id`
- **THEN** the scenario SHALL pass that value to the Git module as `container_user_id`

#### Scenario: Helm CI does not expose generic user_id
- **WHEN** a caller uses the updated Helm CI scenario API
- **THEN** the scenario SHALL NOT expose a generic `user_id` input for Helm or Git execution
- **AND** callers SHALL use prefixed inputs for the tool they need to configure

## MODIFIED Requirements

### Requirement: Helm CI Runtime Image Inputs
The Helm CI scenario SHALL expose runtime image inputs for the Helm, Git, and Updatecli modules it composes.

#### Scenario: Caller configures Helm runtime image
- **WHEN** a caller invokes Helm chart verification or publication through the Helm CI scenario
- **THEN** the scenario SHALL use `helm_image_registry`, `helm_image_repository`, and `helm_image_tag` when creating the Helm module

#### Scenario: Caller configures Git runtime image
- **WHEN** a caller publishes a chart through the Helm CI scenario
- **THEN** the scenario SHALL use `git_image_registry`, `git_image_repository`, and `git_image_tag` when creating the Git module for release tag operations

#### Scenario: Caller configures Updatecli runtime image
- **GIVEN** a caller provides `updatecli_image_registry`, `updatecli_image_repository`, `updatecli_image_tag`, or `updatecli_container_user_id`
- **WHEN** the caller runs any chart sync function
- **THEN** the scenario SHALL pass those values to the Updatecli module
- **AND** the default runtime image SHALL provide Updatecli, Helm, git, and Python with PyYAML

#### Scenario: Single-chart workflow does not require Git image inputs
- **WHEN** a caller invokes `verify-chart` for one chart directory
- **THEN** Git runtime image inputs SHALL remain available on the scenario API
- **AND** the scenario SHALL NOT invoke the Git module for verification

#### Scenario: Runtime inputs do not expose module object types
- **WHEN** callers configure Helm CI runtime images
- **THEN** they SHALL pass primitive image input values
- **AND** the scenario SHALL NOT require callers to pass Helm, Git, or Updatecli module object values
