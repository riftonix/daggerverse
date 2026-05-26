## ADDED Requirements

### Requirement: Container images scenario verifies explicit image contexts
The `scenarios/container-images` scenario SHALL verify container image contexts supplied explicitly by the caller.

#### Scenario: Verify one image context
- **WHEN** a caller provides a repository source and context path
- **THEN** the scenario SHALL build that image context through the Docker module
- **AND** build failures SHALL fail the scenario function call

#### Scenario: Verify multiple image contexts
- **WHEN** a caller provides multiple image context paths
- **THEN** the scenario SHALL verify each context through the Docker module
- **AND** the scenario SHALL fail if any context fails verification

#### Scenario: Verify with smoke command
- **WHEN** a caller provides a smoke command for an image context
- **THEN** the scenario SHALL run the smoke command through the Docker module after building the image

### Requirement: Container images scenario publishes explicit image refs
The `scenarios/container-images` scenario SHALL publish images using destination image references supplied explicitly by the caller.

#### Scenario: Publish one image
- **WHEN** a caller provides a source directory, context path, and image reference
- **THEN** the scenario SHALL publish the built image to that image reference through the Docker module

#### Scenario: Publish multiple images
- **WHEN** a caller provides multiple context path and image reference pairs
- **THEN** the scenario SHALL publish each image through the Docker module
- **AND** the scenario SHALL fail if any publication fails

#### Scenario: Publish to GHCR as OCI registry
- **WHEN** a caller provides an image reference under `ghcr.io`
- **THEN** the scenario SHALL pass that reference to the Docker module as a normal OCI image reference
- **AND** the scenario SHALL NOT require GHCR-specific logic

### Requirement: Container images scenario remains CI-provider portable
The `scenarios/container-images` scenario SHALL avoid CI-provider-specific trigger, tag, and changed-path policy.

#### Scenario: Caller controls changed image selection
- **WHEN** a CI workflow wants to verify changed images
- **THEN** the workflow SHALL provide the selected image context paths to the scenario
- **AND** the scenario SHALL NOT compute changed directories itself

#### Scenario: Caller controls tag-to-image mapping
- **WHEN** a CI workflow wants to publish from a repository tag
- **THEN** the workflow SHALL provide the destination image reference to the scenario
- **AND** the scenario SHALL NOT parse provider-specific tag policy such as `docker/<image-name>/<version>`

#### Scenario: Caller controls publish timing
- **WHEN** a CI workflow decides whether publication should run
- **THEN** the scenario SHALL only perform publication when called with explicit publish inputs
- **AND** the scenario SHALL NOT inspect GitHub Actions or GitLab CI event environment variables

### Requirement: Container images scenario documents CI integration pattern
The `scenarios/container-images` README SHALL describe how CI systems compose Git selection, tag policy, and image verification or publication.

#### Scenario: Read scenario documentation
- **WHEN** a user reads the scenario README
- **THEN** it SHALL show examples using explicit `context_path` and `image_ref` inputs
- **AND** it SHALL explain that CI provider workflows own event rules and tag parsing

### Requirement: Container images scenario has Dagger-native tests
The `scenarios/container-images` scenario SHALL have Dagger-native tests that validate public scenario behavior through its public API.

#### Scenario: Run container images scenario tests
- **WHEN** a user or CI runs tests for the `container-images` scenario
- **THEN** the scenario test module SHALL run its aggregate `all` function
- **AND** the tests SHALL call the scenario through a local Dagger dependency

#### Scenario: Test scenario verification
- **WHEN** single-image or multi-image verification behavior is implemented
- **THEN** the same implementation step SHALL add or update Dagger-native tests for that verification behavior

#### Scenario: Test scenario publication
- **WHEN** single-image or multi-image publication behavior is implemented
- **THEN** the same implementation step SHALL add or update Dagger-native tests for that publication behavior
- **AND** publication tests SHALL use a local OCI registry service
