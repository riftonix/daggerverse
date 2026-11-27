## ADDED Requirements

### Requirement: Container Execution User Input Convention
New and updated modules, scenarios, and Dagger test modules SHALL name container execution UID inputs `container_user_id` when the value configures container user, file ownership, secret ownership, or container home setup.

#### Scenario: Module exposes container execution user
- **WHEN** a module uses a public input to call `.with_user()` or set ownership for mounted files, directories, or secrets
- **THEN** the public input SHALL be named `container_user_id`
- **AND** the module SHALL NOT expose the same behavior as a generic `user_id` input
- **AND** `container_user_id` SHALL be optional and independent of image selection

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

## MODIFIED Requirements

### Requirement: Runtime Image Input Convention
New and updated image-backed Dagger modules and scenarios SHALL expose runtime tool image selection through explicit public inputs instead of hidden or combined image references.

#### Scenario: New image-backed module accepts runtime image inputs
- **WHEN** a new module runs a fixed tool container as its execution environment
- **THEN** the public constructor SHALL expose `image_registry`, `image_repository`, and `image_tag`
- **AND** documentation examples SHALL show how callers can override at least the image tag

#### Scenario: Updated image-backed module accepts runtime image inputs
- **WHEN** an existing image-backed module API is updated
- **THEN** it SHALL use `image_registry`, `image_repository`, and `image_tag` for the runtime tool image
- **AND** it SHALL NOT introduce or keep a combined `container_image` public input for the same runtime image

#### Scenario: Scenario exposes composed runtime image inputs
- **WHEN** a scenario composes an image-backed module and exposes a public workflow around that module
- **THEN** the scenario SHALL expose public inputs for the composed module runtime image
- **AND** the scenario SHALL pass those inputs to the composed module instead of relying only on hidden module defaults

#### Scenario: Multi-tool scenario uses prefixed image inputs
- **WHEN** a scenario composes more than one image-backed tool module
- **THEN** each runtime image input set SHALL be prefixed with the tool or engine name
- **AND** names SHALL be unambiguous, such as `hugo_image_tag`, `helm_image_tag`, or `git_image_tag`

#### Scenario: Docker build references keep build-specific names
- **WHEN** a module or scenario describes images being built, tagged, or published
- **THEN** build and publication inputs SHALL keep names such as `image_ref`, `image_refs`, `tags`, `context_path`, `dockerfile_path`, `bake_path`, and `variable_overrides`
- **AND** those build metadata inputs SHALL NOT be renamed to runtime image input names
