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
