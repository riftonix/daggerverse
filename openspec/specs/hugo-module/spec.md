## Purpose

Define the Hugo Dagger module contract for reproducible Hugo site rendering,
strict validation, and Hugo module preparation.

## Requirements

### Requirement: Prepared Hugo Autoprefixer Image
The Hugo module SHALL use `ghcr.io/riftonix/container-images/hugo-autoprefixer:0.154.5-10.5.0` as its default container image.

#### Scenario: Default container image is used
- **WHEN** a caller creates the Hugo module without overriding image parameters
- **THEN** the module uses the prepared Hugo Autoprefixer image from GHCR

### Requirement: No Runtime Npm Install in Normal Build
The Hugo module SHALL NOT install npm packages during its normal build or validation path.

#### Scenario: Build uses prepared tools
- **WHEN** a caller builds a Hugo site through the normal build function
- **THEN** the module runs Hugo using tools already present in the container image

### Requirement: Hugo Site Build
The Hugo module SHALL render a Hugo site to a Dagger directory using the caller-provided base URL.

#### Scenario: Site renders with base URL
- **WHEN** a caller builds a valid Hugo site with `site_base_url` set
- **THEN** the module returns the rendered output directory for that base URL

### Requirement: Strict Hugo Validation
The Hugo module SHALL provide a validation function that runs Hugo with strict warning and path checks suitable for CI.

#### Scenario: Valid site passes validation
- **WHEN** a caller validates a valid Hugo site
- **THEN** validation completes successfully

#### Scenario: Invalid site fails validation
- **WHEN** a caller validates a Hugo site that Hugo cannot render
- **THEN** validation fails with Hugo command output

### Requirement: Dagger Native Hugo Tests
The Hugo module SHALL include a Dagger test module that can be run through the repository component test target.

#### Scenario: Hugo tests are discoverable
- **WHEN** the repository test matrix scans module test directories
- **THEN** the Hugo module is eligible because `modules/hugo/tests/dagger.json` exists

#### Scenario: Hugo tests build Docsy fixture
- **WHEN** `make tests module hugo` runs
- **THEN** the tests build and validate the Docsy fixture site through the Hugo module

### Requirement: Hugo Module Preparation
The Hugo module SHALL provide operations for creating or preparing Hugo modules without requiring static-site publication.

#### Scenario: Hugo module can be initialized
- **WHEN** a caller requests Hugo module preparation for a source directory
- **THEN** the module can initialize or update Hugo module metadata without rendering a public site

#### Scenario: Hugo module imports can be resolved
- **WHEN** a caller prepares a Hugo source with module imports
- **THEN** the module resolves the Hugo module dependencies without publishing a site

### Requirement: Content Module Path Neutrality
The Hugo module SHALL support content-only Hugo modules that do not encode their final path within an importing site.

#### Scenario: Content module exposes standard content directory
- **WHEN** a reusable documentation module contains Hugo content
- **THEN** it can expose that content through the standard `content` component directory

#### Scenario: Importing site chooses content mount target
- **WHEN** an importing site needs the documentation under a site-specific path
- **THEN** the importing site configures the import mount target instead of requiring the content module to know that path

### Requirement: Multiple Hugo Module Roots
The Hugo module SHALL support preparing independent Hugo module roots so a composed site can import them separately.

#### Scenario: Docs module is prepared independently
- **WHEN** a caller prepares the `docs` module root
- **THEN** the module validates Hugo module metadata for `docs` without requiring the main site

#### Scenario: OpenSpec module is prepared independently
- **WHEN** a caller prepares the `openspec` module root
- **THEN** the module validates Hugo module metadata for `openspec` without requiring the main site

### Requirement: Hugo Runtime Image Inputs
The Hugo module SHALL expose the standard runtime image inputs for the container used to execute Hugo.

#### Scenario: Caller overrides Hugo image tag
- **WHEN** a caller creates the Hugo module with `image_registry`, `image_repository`, `image_tag`, or `user_id`
- **THEN** the module SHALL use those values when constructing the Hugo execution container

#### Scenario: Caller uses default Hugo image
- **WHEN** a caller creates the Hugo module without overriding runtime image inputs
- **THEN** the module SHALL continue using the prepared Hugo Autoprefixer image defaults

#### Scenario: Hugo runtime image is visible to callers
- **WHEN** CI needs to synchronize Hugo site configuration with the image used to render the site
- **THEN** the required Hugo image tag SHALL be available as a public module input

#### Scenario: Hugo tests use configured runtime image inputs
- **WHEN** the Hugo test module runs direct Hugo module integration checks
- **THEN** direct Hugo module calls SHALL use the test module constructor runtime image inputs
- **AND** component module import rendering SHALL be covered in the Hugo test module rather than in the static-site scenario tests
