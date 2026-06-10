## ADDED Requirements

### Requirement: Helm Container User Input
The Helm module SHALL expose container execution user configuration through `container_user_id`.

#### Scenario: Caller configures Helm container user
- **WHEN** a caller creates the Helm module with `container_user_id`
- **THEN** the Helm module SHALL run Helm and set chart/package file ownership using that container user ID

#### Scenario: Helm user_id input is removed
- **WHEN** a caller uses the updated Helm module API
- **THEN** the public constructor SHALL NOT accept `user_id` for container execution user behavior
- **AND** callers SHALL use `container_user_id` instead

#### Scenario: Helm registry username keeps name
- **WHEN** a caller configures Helm registry authentication
- **THEN** registry login inputs such as `username` SHALL keep registry-specific names
- **AND** they SHALL NOT be renamed to `container_user_id`

### Requirement: Helm Module Public Contract
The Helm module SHALL provide reusable Helm chart operations for linting, templating, packaging, pushing, and publication lookup.

#### Scenario: Helm chart operations use source chart
- **WHEN** a caller creates the Helm module with a chart directory as `source`
- **THEN** Helm operations SHALL run against that chart source tree
