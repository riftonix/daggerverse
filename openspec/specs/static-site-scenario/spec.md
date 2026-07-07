## Purpose

Define the provider-neutral static-site scenario contract for rendering,
verification, engine dispatch, and Hugo mount collision validation.
## Requirements
### Requirement: Static Site Scenario
The repository SHALL provide a `scenarios/static-site` Dagger scenario for provider-neutral static-site verification and rendering.

#### Scenario: Scenario exists
- **WHEN** a caller invokes the `static-site` scenario
- **THEN** the scenario exposes static-site functions backed by reusable modules

### Requirement: Engine Backed Verification
The static-site scenario SHALL verify static sites by composing the selected static-site engine module and using the constructor `source` directory as the site source tree.

#### Scenario: Scenario verifies a Hugo site
- **WHEN** a caller passes a site source directory to the static-site scenario constructor and passes selected engine and base URL to the scenario verification function
- **THEN** the scenario validates the site using the Hugo module
- **AND** the verification function SHALL NOT accept a separate `site` directory input

### Requirement: Engine Backed Rendering
The static-site scenario SHALL render static sites by composing the selected static-site engine module and returning the rendered directory from the constructor `source` tree.

#### Scenario: Scenario renders a Hugo site
- **WHEN** a caller passes a site source directory to the static-site scenario constructor and passes selected engine and base URL to the scenario render function
- **THEN** the scenario returns the rendered static-site directory using the Hugo module
- **AND** the render function SHALL NOT accept a separate `site` directory input

### Requirement: Extensible Static Site Engines
The static-site scenario SHALL be structured so future engines can be added for common static-site verification and rendering without replacing provider workflow commands.

#### Scenario: Unsupported engine is rejected
- **WHEN** a caller selects an engine that is not implemented
- **THEN** the scenario fails with a clear unsupported engine error

#### Scenario: Future engine can be added
- **WHEN** a new static-site engine module such as Jekyll is introduced
- **THEN** the scenario can route verification and rendering to that engine while preserving the provider-neutral publication boundary

### Requirement: Engine Specific Capabilities Stay Outside Scenario
The static-site scenario SHALL NOT require all engines to support Hugo-specific module operations.

#### Scenario: Hugo module preparation remains engine-specific
- **WHEN** a caller needs to initialize or resolve Hugo modules
- **THEN** the caller uses the Hugo module API instead of the static-site scenario API

#### Scenario: Jekyll support does not require Hugo module behavior
- **WHEN** a future Jekyll engine is added
- **THEN** it can support verification and rendering without implementing Hugo-style module preparation

### Requirement: Provider Neutral Inputs
The static-site scenario SHALL accept already computed site URLs and a caller-provided `source` tree and SHALL NOT derive GitHub or GitLab preview metadata from provider-specific environment variables.

#### Scenario: Caller supplies preview URL
- **WHEN** a GitHub Actions or GitLab CI workflow calls the scenario for a preview
- **THEN** the workflow passes the preview base URL explicitly
- **AND** the workflow passes the checked-out site tree through `source`
- **AND** the scenario SHALL NOT inspect provider-specific event environment variables or checkout policy

### Requirement: Provider Publication Boundary
The static-site scenario SHALL NOT publish to GitHub Pages, publish to GitLab Pages, manage deployment environments, delete previews, or comment on pull requests or merge requests.

#### Scenario: CI publishes scenario output
- **WHEN** the scenario returns a rendered static-site directory
- **THEN** the provider workflow remains responsible for publishing that directory and managing preview lifecycle

### Requirement: Dagger Native Static Site Tests
The static-site scenario SHALL include a Dagger test module that can be run through the repository scenario test target.

#### Scenario: Static-site tests are discoverable
- **WHEN** the repository test matrix scans scenario test directories
- **THEN** the static-site scenario is eligible because `scenarios/static-site/tests/dagger.json` exists

### Requirement: Multi Component Documentation Mount Layout
The static-site automation SHALL support a main Hugo site importing component `docs` and `openspec` Hugo modules with explicit mounts.

#### Scenario: Daggerverse docs module is mounted under component documentation
- **WHEN** the main site imports `github.com/riftonix/daggerverse/docs`
- **THEN** `content` from that module can be mounted to `content/docs/components/daggerverse`

#### Scenario: Container images docs module is mounted under component documentation
- **WHEN** the main site imports `github.com/riftonix/container-images/docs`
- **THEN** `content` from that module can be mounted to `content/docs/components/container-images`

#### Scenario: OpenSpec specs are mounted under shared specs
- **WHEN** the main site imports a component `openspec` module
- **THEN** `specs` from that module can be mounted to `content/docs/specs`

#### Scenario: OpenSpec archive is mounted under shared changes archive
- **WHEN** the main site imports a component `openspec` module
- **THEN** `changes/archive` from that module can be mounted to `content/docs/changes/archive`

#### Scenario: Main site render validates composed modules
- **WHEN** static-site automation renders the main Hugo site
- **THEN** the rendered site includes component documentation, shared specs, and shared archived changes from the imported modules

### Requirement: Hugo Mount Path Collision Validation
The static-site automation SHALL detect conflicting virtual paths when multiple Hugo modules mount into shared targets.

#### Scenario: Unique mounted paths pass
- **WHEN** multiple Hugo modules contribute different virtual paths through the configured mounts
- **THEN** the static-site automation accepts the mount layout

#### Scenario: Duplicate mounted paths fail
- **WHEN** multiple Hugo modules contribute the same virtual path through the configured mounts
- **THEN** the static-site automation fails with a collision error that identifies the conflicting modules and path

### Requirement: Static Site Source Constructor
The static-site scenario SHALL accept its primary site source directory through a constructor input named `source`.

#### Scenario: Construct static-site scenario with source
- **WHEN** a caller constructs the static-site scenario with a site directory
- **THEN** the public constructor input SHALL be named `source`
- **AND** static-site operations SHALL use that directory as the site source tree

#### Scenario: Static-site CLI uses source before function name
- **WHEN** a caller invokes the static-site scenario from the Dagger CLI
- **THEN** the documented command shape SHALL pass the site directory as `call --source=<dir> <function>`
- **AND** the command SHALL NOT require a function-level `--site` directory input

### Requirement: Required Hugo Theme URL
The static-site scenario SHALL require callers to provide the Hugo theme URL used for Hugo-backed verification and rendering.

#### Scenario: Use provided Hugo theme URL
- **WHEN** a caller constructs the static-site scenario with a Hugo theme URL and verifies or renders a Hugo site
- **THEN** Hugo-backed verification and rendering SHALL pass that configured theme URL to the Hugo module

#### Scenario: Reject missing Hugo theme URL
- **WHEN** a caller selects the Hugo engine without providing a non-empty Hugo theme URL
- **THEN** the scenario SHALL fail clearly before invoking the Hugo module

### Requirement: Static Site Hugo Runtime Image Inputs
The static-site scenario SHALL expose Hugo runtime image inputs on its public constructor when Hugo is a supported engine.

#### Scenario: Construct static-site scenario with Hugo image inputs
- **WHEN** a caller constructs the static-site scenario for Hugo-backed operations
- **THEN** the constructor SHALL accept `hugo_image_registry`, `hugo_image_repository`, `hugo_image_tag`, and `hugo_container_user_id`
- **AND** each input SHALL default to the Hugo module default for the same runtime image field

#### Scenario: Verify passes Hugo image inputs
- **WHEN** a caller verifies a Hugo site through the static-site scenario
- **THEN** the scenario SHALL pass the configured Hugo runtime image inputs to the Hugo module
- **AND** the scenario SHALL pass the configured Hugo theme URL to the Hugo module

#### Scenario: Render passes Hugo image inputs
- **WHEN** a caller renders a Hugo site through the static-site scenario
- **THEN** the scenario SHALL pass the configured Hugo runtime image inputs to the Hugo module
- **AND** the rendered output SHALL come from the configured Hugo execution image

#### Scenario: Static-site workflow pins Hugo image tag
- **WHEN** a CI workflow needs reproducible Hugo rendering
- **THEN** it SHALL be able to pin the Hugo runtime through `hugo_image_tag`
- **AND** the pin SHALL be visible in the workflow rather than hidden in the Hugo module dependency default

#### Scenario: Static-site tests avoid direct Hugo module calls
- **WHEN** static-site scenario tests exercise Hugo-backed scenario operations
- **THEN** they SHALL call the static-site scenario API with configured Hugo runtime image inputs
- **AND** direct Hugo module integration checks SHALL live in the Hugo module tests
