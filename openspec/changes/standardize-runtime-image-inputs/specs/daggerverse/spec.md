## ADDED Requirements

### Requirement: Runtime Image Input Convention
New and updated image-backed Dagger modules and scenarios SHALL expose runtime tool image selection through explicit public inputs instead of hidden or combined image references.

#### Scenario: New image-backed module accepts runtime image inputs
- **WHEN** a new module runs a fixed tool container as its execution environment
- **THEN** the public constructor SHALL expose `image_registry`, `image_repository`, `image_tag`, and `user_id`
- **AND** documentation examples SHALL show how callers can override at least the image tag

#### Scenario: Updated image-backed module accepts runtime image inputs
- **WHEN** an existing image-backed module API is updated
- **THEN** it SHALL use `image_registry`, `image_repository`, `image_tag`, and `user_id` for the runtime tool image
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

### Requirement: Runtime Image Input Documentation
The repository documentation SHALL describe the runtime image input convention for modules and scenarios.

#### Scenario: Contributor reads runtime image guidance
- **WHEN** a contributor reads repository guidance for adding or updating modules and scenarios
- **THEN** the documentation SHALL explain the standard runtime image inputs
- **AND** it SHALL explain when to use prefixed image inputs in scenarios
- **AND** it SHALL identify Docker build metadata as an exception to the runtime image input convention

#### Scenario: Breaking runtime image API is documented
- **WHEN** an existing released module or scenario changes public runtime image inputs
- **THEN** documentation SHALL describe the migration
- **AND** the changed module or scenario SHALL require a new release tag

### Requirement: Dagger Test Module Public Shape
Dagger test modules SHALL expose predictable public entrypoints for repository CI and SHALL follow the runtime image naming convention when tests expose helper service image inputs.

#### Scenario: Test module exposes aggregate entrypoint
- **WHEN** a module or scenario has a Dagger test module
- **THEN** the test module SHALL expose an aggregate `all()` function suitable for CI
- **AND** `all()` SHALL require no caller-provided inputs unless the exception is documented in the test module or repository docs

#### Scenario: Test module uses local fixtures
- **WHEN** tests need fixture source files from the component repository
- **THEN** the tests SHALL read fixtures through `dag.current_module().source()`
- **AND** they SHALL NOT require a public `source` input unless the test intentionally validates caller-provided source behavior and documents that exception

#### Scenario: Git test module uses synthetic repositories
- **WHEN** Git module tests need a repository source to validate metadata such as HEAD SHA or short commit SHA
- **THEN** the tests SHALL use a local synthetic Git repository fixture
- **AND** the aggregate `all()` function SHALL NOT require a public `source` input for those metadata checks

#### Scenario: Test helper service image inputs are prefixed
- **WHEN** a test function exposes runtime image inputs for a helper service container
- **THEN** those inputs SHALL be prefixed with the helper purpose
- **AND** names SHALL be unambiguous, such as `registry_image_registry`, `registry_image_repository`, and `registry_image_tag`

#### Scenario: Test module supports mirrored runtime images
- **WHEN** a Dagger test module needs to run image-backed tools or helper services in an offline or mirrored-registry environment
- **THEN** it SHALL expose optional constructor-level runtime image inputs for those images
- **AND** the aggregate `all()` SHALL remain callable without required runtime image arguments

#### Scenario: Test runtime user is configurable
- **WHEN** a tested runtime or helper service image supports a configurable user
- **THEN** the test module runtime image inputs SHALL include the matching optional `user_id` input
- **AND** prefixed helper images SHALL use prefixed names such as `registry_user_id` when a user override is relevant

#### Scenario: Test module defaults match tested component defaults
- **WHEN** a test module exposes runtime image inputs for a tested module or scenario
- **THEN** the test module defaults SHALL match the tested component defaults
- **AND** the implementation SHALL avoid independent version drift by using shared constants, Renovate-managed duplicate defaults, pass-through construction, or tests that assert the configured values are passed through

#### Scenario: Renovate synchronizes duplicate runtime defaults
- **WHEN** the same runtime image default appears in production code, scenario code, test code, documentation, or downstream workflow examples
- **THEN** every duplicate occurrence SHALL be trackable by Renovate using the same dependency identity and datasource
- **AND** Renovate SHALL update the full runtime image tag atomically

#### Scenario: Constants are optional for defaults
- **WHEN** a runtime image default is used only in a constructor signature or a small local scope
- **THEN** the implementation MAY keep the default as a Renovate-trackable literal
- **AND** repository guidance SHALL NOT require constants solely for default version storage

#### Scenario: Hugo minimum version follows runtime image source
- **WHEN** downstream site configuration uses `module.hugoVersion.min` to describe the Hugo version available in the runtime builder
- **THEN** Renovate SHALL track that minimum version from the same Docker image stream used by the runtime base image
- **AND** for the current Hugo runtime that source SHALL be `hugomods/hugo` Docker tags extracted with `^exts-(?<version>.+)$`
- **AND** it SHALL NOT track `gohugoio/hugo` GitHub releases for that builder-coupled minimum version

#### Scenario: Test module image metadata remains separate from publish refs
- **WHEN** tests validate image build or publication outputs
- **THEN** output references SHALL keep names such as `image_ref`, `image_refs`, and `tags`
- **AND** those output references SHALL NOT be split into runtime image input fields
