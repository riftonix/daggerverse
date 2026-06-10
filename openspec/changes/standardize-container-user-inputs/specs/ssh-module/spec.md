## ADDED Requirements

### Requirement: SSH Container User Input
The SSH module SHALL expose container execution user configuration through `container_user_id`.

#### Scenario: Caller configures SSH container user
- **WHEN** a caller creates the SSH module with `container_user_id`
- **THEN** the SSH module SHALL create or use the container home directory and key ownership for that container user ID

#### Scenario: SSH user_id input is removed
- **WHEN** a caller uses the updated SSH module API
- **THEN** the public constructor SHALL NOT accept `user_id` for container execution user behavior
- **AND** callers SHALL use `container_user_id` instead

#### Scenario: SSH login user keeps name
- **WHEN** a caller configures the remote SSH login user
- **THEN** the public input SHALL keep a domain-specific name such as `ssh_user`
- **AND** it SHALL NOT be renamed to `container_user_id`

### Requirement: SSH Module Public Contract
The SSH module SHALL provide containerized SSH client operations with caller-provided key material.

#### Scenario: SSH command executes with configured destination
- **WHEN** a caller provides an SSH destination and command inputs
- **THEN** the module SHALL execute the SSH command from the configured SSH client container
