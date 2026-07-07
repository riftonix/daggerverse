## Purpose

Describe the existing repository structure and documentation baseline for Daggerverse.
## Requirements
### Requirement: Module repository layout

The repository SHALL organize reusable Dagger CI modules under the `modules/` directory.

#### Scenario: Locate a module
- **WHEN** a user looks for a module implementation
- **THEN** the module is available under `modules/<module-name>`
- **AND** each module directory contains its own Dagger module metadata and source code

### Requirement: Scenario repository layout

The repository SHALL organize reusable Dagger CI scenarios under the `scenarios/` directory.

#### Scenario: Locate a scenario
- **WHEN** a user looks for a scenario implementation
- **THEN** the scenario is available under `scenarios/<scenario-name>`
- **AND** each scenario directory contains its own Dagger module metadata and source code

### Requirement: Repository documentation

The repository SHALL keep English documentation under the `docs/` directory.

#### Scenario: Start reading documentation
- **WHEN** a user opens `docs/README.md`
- **THEN** the page explains the recommended learning path
- **AND** the page links to learning material, task guides, reference material, and design explanations

#### Scenario: Read container image CI documentation
- **WHEN** a user reads the repository documentation for container image CI
- **THEN** it SHALL explain that `modules/docker` provides reusable Docker and OCI primitives
- **AND** it SHALL explain that `scenarios/container-images` provides portable image verification and publication functions
- **AND** it SHALL explain that CI-provider workflows own event triggers, changed path selection, and tag-to-image-reference mapping

### Requirement: Module README links

Each module README SHALL point readers to the repository documentation.

#### Scenario: Read a module README
- **WHEN** a user opens `modules/<module-name>/README.md`
- **THEN** the README links to `docs/README.md`

### Requirement: OpenSpec baseline

The repository SHALL keep current-state specifications separate from planned change proposals.

#### Scenario: Document existing behavior
- **WHEN** behavior is already implemented
- **THEN** it is documented under `openspec/specs/`

#### Scenario: Document planned behavior
- **WHEN** behavior is planned but not implemented
- **THEN** it is documented under `openspec/changes/`

### Requirement: Repository command interface

The repository SHALL expose supported local and CI workflows through the root `Makefile`.

#### Scenario: Run module tests
- **WHEN** a user or CI needs to run tests for a module with a Dagger test module
- **THEN** the tests SHALL be runnable with `make tests module <module-name>`
- **AND** the target SHALL call the module test aggregate function

#### Scenario: Run scenario tests
- **WHEN** a user or CI needs to run tests for a scenario with a Dagger test module
- **THEN** the tests SHALL be runnable with `make tests scenario <scenario-name>`
- **AND** the target SHALL call the scenario test aggregate function

#### Scenario: Scenario has no tests
- **WHEN** a scenario has no Dagger test module
- **THEN** CI discovery SHALL NOT fail only because that scenario has no tests

#### Scenario: Remove legacy shorthand test command
- **WHEN** a user runs a legacy module-only shorthand such as `make tests docker`
- **THEN** the Makefile SHALL reject the command through the generic explicit-form usage validation
- **AND** it SHALL NOT translate the shorthand to `make tests module docker`

#### Scenario: Run lint for all Python components
- **WHEN** a user or CI runs `make lint` or `make lint-check` without a component selector
- **THEN** the command SHALL run Ruff against all existing Python component roots under `modules/` and `scenarios/`

#### Scenario: Run lint for one module
- **WHEN** a user or CI runs `make lint module docker` or `make lint-check module docker`
- **THEN** the command SHALL run Ruff only against `modules/docker`

#### Scenario: Run lint for one scenario
- **WHEN** a user or CI runs `make lint scenario container-images` or `make lint-check scenario container-images`
- **THEN** the command SHALL run Ruff only against `scenarios/container-images`

#### Scenario: Run format for all Python components
- **WHEN** a user or CI runs `make format` or `make format-check` without a component selector
- **THEN** the command SHALL run Ruff formatting against all existing Python component roots under `modules/` and `scenarios/`

#### Scenario: Shared Ruff configuration
- **WHEN** Ruff commands run from the repository root
- **THEN** Ruff SHALL use a shared repository-level configuration file
- **AND** the Ruff configuration SHALL NOT live under `modules/`

### Requirement: Dagger-native module tests

When module-specific tests are added for a reusable Dagger module, the repository SHALL implement them as a neighboring Dagger test module.

#### Scenario: Add tests for a module
- **WHEN** tests are added for `modules/<module-name>`
- **THEN** the tests SHOULD live under `modules/<module-name>/tests`
- **AND** the test directory SHOULD be a Dagger module
- **AND** the test module SHOULD depend on the parent module through a local dependency
- **AND** test functions SHOULD call the parent module public API rather than shelling out to the Dagger CLI to call the parent module

#### Scenario: Document test implementation guidance
- **WHEN** a contributor needs to add Dagger-native tests for a module
- **THEN** repository documentation SHALL include practical guidance for writing Dagger CI modules and tests
- **AND** the guidance SHALL describe the neighboring test module pattern
- **AND** the guidance SHALL describe calling parent module APIs through local Dagger dependencies

#### Scenario: Implement Git module feature
- **WHEN** a feature is implemented for `modules/git`
- **THEN** the same implementation step SHALL add or update Dagger-native tests for that feature
- **AND** the Git test module SHALL remain runnable with `make tests module git`

#### Scenario: Run all tests for a tested module
- **WHEN** a module has a Dagger test module
- **THEN** the test module SHOULD expose an aggregate function suitable for CI
- **AND** the aggregate function SHOULD run the module checks that are expected to gate pull requests

### Requirement: Helm module Dagger tests

The Helm module SHALL have a Dagger test module that verifies the existing fixture chart through the Helm module public API.

#### Scenario: Verify Helm lint
- **WHEN** the Helm test module aggregate test runs
- **THEN** it SHALL run Helm lint against the existing fixture chart
- **AND** lint failures SHALL fail the test

#### Scenario: Verify Helm template
- **WHEN** the Helm test module aggregate test runs
- **THEN** it SHALL run Helm template against the existing fixture chart
- **AND** template failures SHALL fail the test

#### Scenario: Verify Helm package
- **WHEN** the Helm test module aggregate test runs
- **THEN** it SHALL package the existing fixture chart
- **AND** package failures SHALL fail the test

#### Scenario: Verify Helm push
- **WHEN** the Helm test module aggregate test runs
- **THEN** it SHALL push the existing fixture chart to a local OCI registry service
- **AND** push failures SHALL fail the test
- **AND** the test SHALL NOT require GitHub Container Registry credentials

#### Scenario: Verify Helm publication lookup
- **WHEN** the Helm test module aggregate test runs after pushing the fixture chart to a local OCI registry service
- **THEN** it SHALL verify the pushed chart version through the Helm module publication lookup function
- **AND** lookup failures SHALL fail the test
- **AND** the test SHALL NOT depend on pre-existing external registry state

### Requirement: GitHub pull request CI for available module tests

The repository SHALL run the in-scope Dagger module tests in GitHub Actions for pull requests targeting the repository default branch.

#### Scenario: Pull request targets default branch
- **WHEN** a pull request targets the repository default branch
- **THEN** GitHub Actions SHALL discover modules with Dagger test modules
- **AND** GitHub Actions SHALL run each discovered module through `make tests module <module-name>`
- **AND** the workflow SHALL use the repository-aligned Dagger CLI version

#### Scenario: A module does not yet have Dagger tests
- **WHEN** a module has no Dagger test module
- **THEN** GitHub Actions SHALL NOT fail only because that module has no tests
- **AND** the module MAY be skipped until tests are added for it

#### Scenario: Module tests fail
- **WHEN** a module Dagger test fails in pull request CI
- **THEN** the pull request CI SHALL fail

### Requirement: GitHub pull request CI for available scenario tests

The repository SHALL run available Dagger scenario tests in GitHub Actions for pull requests targeting the repository default branch.

#### Scenario: Pull request targets default branch
- **WHEN** a pull request targets the repository default branch
- **THEN** GitHub Actions SHALL discover scenarios with Dagger test modules under `scenarios/<scenario-name>/tests`
- **AND** GitHub Actions SHALL run each discovered scenario test aggregate function

#### Scenario: Scenario tests fail
- **WHEN** a scenario Dagger test fails in pull request CI
- **THEN** the pull request CI SHALL fail

### Requirement: Scenario publication workflow

The repository SHALL publish Dagger scenarios through GitHub Actions using rules analogous to module publication.

#### Scenario: Publish all scenarios on default branch push
- **WHEN** changes are pushed to the default branch
- **THEN** GitHub Actions SHALL discover scenarios under `scenarios/<scenario-name>` with Dagger module metadata
- **AND** GitHub Actions SHALL publish each discovered scenario

#### Scenario: Publish one scenario from release tag
- **WHEN** a tag matching `scenarios/<scenario-name>/vX.Y.Z` is pushed
- **THEN** GitHub Actions SHALL publish only the named scenario
- **AND** the workflow SHALL fail clearly if the tag references an unknown scenario

### Requirement: Dagger version alignment

The repository SHALL align Dagger module metadata and CI on the repository Dagger version.

#### Scenario: Dagger module metadata is updated
- **WHEN** Dagger module metadata is updated
- **THEN** affected Dagger module metadata SHALL use the repository-aligned engine version
- **AND** generated SDK artifacts SHALL be consistent with that engine version

### Requirement: Helm CI scenario repository layout
The repository SHALL place Helm CI orchestration under `scenarios/helm-ci`.

#### Scenario: Locate Helm CI scenario
- **WHEN** a user looks for Helm CI workflow implementation
- **THEN** the implementation SHALL be available under `scenarios/helm-ci`
- **AND** the scenario directory SHALL contain its own Dagger module metadata and source code
- **AND** the repository SHALL NOT keep the Helm CI workflow implementation under `modules/pipelines`

#### Scenario: Run Helm CI scenario tests
- **WHEN** a user or CI needs to run Helm CI scenario tests
- **THEN** the tests SHALL be runnable with `make tests scenario helm-ci`
- **AND** the command SHALL call the scenario test aggregate function

### Requirement: Repository documentation includes Helm CI scenario
The repository documentation SHALL describe Helm CI orchestration as a scenario.

#### Scenario: Read Helm CI documentation
- **WHEN** a user reads the repository documentation for Helm CI checks
- **THEN** it SHALL explain that `modules/helm` provides reusable Helm primitives
- **AND** it SHALL explain that `scenarios/helm-ci` provides portable Helm verification and publication workflows
- **AND** it SHALL explain that CI-provider workflows own event triggers, branch selection, changed path selection, and publish timing

#### Scenario: Read root repository overview
- **WHEN** a user opens the root README
- **THEN** the module list SHALL NOT include `pipelines`
- **AND** the scenario list SHALL include `helm-ci`

### Requirement: Primary Source Directory Input Convention
New and updated Dagger modules and scenarios SHALL name the primary input directory `source` when that directory represents the main project, chart, site, repository checkout, or other source tree being operated on.

#### Scenario: New module accepts a primary source tree
- **WHEN** a new module function or constructor needs the main input directory for its operation
- **THEN** the public input SHALL be named `source`
- **AND** documentation examples SHALL show callers passing that directory with `--source=<dir>`

#### Scenario: Updated scenario accepts a primary source tree
- **WHEN** an existing scenario API is updated and it accepts the main input directory for its operation
- **THEN** the public input SHALL be named `source`
- **AND** specialized primary directory names such as `site`, `chart`, or repository-source variants SHALL be removed from the public API

#### Scenario: Secondary path inputs keep descriptive names
- **WHEN** a module or scenario accepts additional path-like inputs that are not the primary input tree
- **THEN** those inputs SHALL keep descriptive names such as values file, output directory, chart path, Dockerfile path, target branch, or registry URL
- **AND** they SHALL NOT be renamed to `source`

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
- **THEN** the test module runtime image inputs SHALL include the matching optional container user input
- **AND** prefixed helper images SHALL use prefixed names such as `registry_container_user_id` when a user override is relevant

#### Scenario: Test module defaults match tested component defaults
- **WHEN** a test module exposes runtime image inputs for a tested module or scenario
- **THEN** the test module defaults SHALL match the tested component defaults
- **AND** the implementation SHALL avoid independent version drift by using shared constants, Renovate-managed duplicate defaults, or pass-through construction

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

### Requirement: Source Input Documentation
The repository documentation SHALL describe `source` as the standard public input for primary source trees in new and updated modules and scenarios.

#### Scenario: Read source input guidance
- **WHEN** a user reads repository documentation for calling or authoring Dagger modules and scenarios
- **THEN** the documentation SHALL explain that `source` identifies the caller-provided input tree
- **AND** examples SHALL use `dagger -m <module-or-scenario> call --source=<dir> <function> ...`

#### Scenario: Provider CI policy remains outside source input
- **WHEN** a CI provider workflow calls a module or scenario with `source`
- **THEN** provider-specific event selection, checkout policy, preview URL derivation, publication, cleanup, and comments SHALL remain outside the module or scenario contract
- **AND** `source` SHALL NOT imply provider event or checkout behavior
