## ADDED Requirements

### Requirement: Container Execution User Input Convention
New and updated modules, scenarios, and Dagger test modules SHALL name container execution UID inputs `container_user_id` when the value configures container user, file ownership, secret ownership, or container home setup.

#### Scenario: Module exposes container execution user
- **WHEN** a module uses a public input to call `.with_user()` or set ownership for mounted files, directories, or secrets
- **THEN** the public input SHALL be named `container_user_id`
- **AND** the module SHALL NOT expose the same behavior as a generic `user_id` input

#### Scenario: Module does not use container execution user
- **WHEN** a module does not use caller-provided container user or ownership behavior
- **THEN** it SHALL NOT expose `container_user_id`
- **AND** it SHALL NOT expose `user_id` only for naming consistency

#### Scenario: Scenario prefixes composed container users
- **WHEN** a scenario composes modules that expose `container_user_id`
- **THEN** the scenario SHALL expose prefixed inputs for each composed tool that needs the value
- **AND** names SHALL be unambiguous, such as `hugo_container_user_id`, `helm_container_user_id`, or `git_container_user_id`

#### Scenario: Domain users keep descriptive names
- **WHEN** a public input represents a registry username, SSH login user, Git author name, Git author email, or provider actor
- **THEN** it SHALL keep a domain-specific name
- **AND** it SHALL NOT be renamed to `container_user_id`

#### Scenario: Test module helper container user is prefixed
- **WHEN** a Dagger test module exposes a container user input for a helper service image
- **THEN** the input SHALL be prefixed with the helper purpose
- **AND** names SHALL be unambiguous, such as `registry_container_user_id` when such a user override is relevant

### Requirement: Kind Module Removed
The repository SHALL NOT keep the current `modules/kind` module as a public module.

#### Scenario: Kind module is absent from module discovery
- **WHEN** repository module discovery scans `modules/`
- **THEN** it SHALL NOT discover a `kind` module
- **AND** repository documentation SHALL NOT list Kind as an available module

#### Scenario: Future Talos work is separate
- **WHEN** Kubernetes cluster lifecycle work is introduced later
- **THEN** it SHALL be proposed as a new module such as Talos instead of extending the removed Kind module
