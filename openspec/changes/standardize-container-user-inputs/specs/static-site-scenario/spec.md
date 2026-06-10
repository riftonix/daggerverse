## ADDED Requirements

### Requirement: Static Site Hugo Container User Input
The static-site scenario SHALL expose a prefixed Hugo container execution user input because it composes the Hugo module for Hugo-backed operations.

#### Scenario: Caller configures Hugo container user through static-site
- **WHEN** a caller constructs the static-site scenario with `hugo_container_user_id`
- **THEN** Hugo-backed verify and render operations SHALL pass that value to the Hugo module as `container_user_id`

#### Scenario: Static-site does not expose generic user_id
- **WHEN** a caller uses the updated static-site scenario API
- **THEN** the scenario SHALL NOT expose a generic `user_id` input for Hugo execution
- **AND** callers SHALL use `hugo_container_user_id` when they need to configure Hugo container execution user
