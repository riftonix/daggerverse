## ADDED Requirements

### Requirement: Helm CI Container User Inputs
The Helm CI scenario SHALL expose prefixed container execution user inputs for the Helm and Git modules it composes.

#### Scenario: Caller configures Helm container user through Helm CI
- **WHEN** a caller invokes Helm chart verification or publication through Helm CI with `helm_container_user_id`
- **THEN** the scenario SHALL pass that value to the Helm module as `container_user_id`

#### Scenario: Caller configures Git container user through Helm CI
- **WHEN** a caller invokes changed-chart verification through Helm CI with `git_container_user_id`
- **THEN** the scenario SHALL pass that value to the Git module as `container_user_id`

#### Scenario: Helm CI does not expose generic user_id
- **WHEN** a caller uses the updated Helm CI scenario API
- **THEN** the scenario SHALL NOT expose a generic `user_id` input for Helm or Git execution
- **AND** callers SHALL use prefixed inputs for the tool they need to configure
