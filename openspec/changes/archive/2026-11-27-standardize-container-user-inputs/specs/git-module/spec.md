## ADDED Requirements

### Requirement: Git Container User Input
The Git module SHALL expose container execution user configuration through `container_user_id`.

#### Scenario: Caller configures Git container user
- **WHEN** a caller creates the Git module with `container_user_id`
- **THEN** the Git module SHALL run Git operations and set repository/auth file ownership using that container user ID

#### Scenario: Git user_id input is removed
- **WHEN** a caller uses the updated Git module API
- **THEN** the public constructor SHALL NOT accept `user_id` for container execution user behavior
- **AND** callers SHALL use `container_user_id` instead

#### Scenario: Git domain users keep names
- **WHEN** a caller creates annotated tags or configures Git identity
- **THEN** inputs such as `user_name` and `user_email` SHALL keep their Git-domain names
- **AND** they SHALL NOT be renamed to `container_user_id`
