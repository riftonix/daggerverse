## ADDED Requirements

### Requirement: Static Site Scenario
The repository SHALL provide a `scenarios/static-site` Dagger scenario for provider-neutral static-site verification and rendering.

#### Scenario: Scenario exists
- **WHEN** a caller invokes the `static-site` scenario
- **THEN** the scenario exposes static-site functions backed by reusable modules

### Requirement: Engine Backed Verification
The static-site scenario SHALL verify static sites by composing the selected static-site engine module.

#### Scenario: Scenario verifies a Hugo site
- **WHEN** a caller passes a Hugo site directory, selected engine, and base URL to the scenario verification function
- **THEN** the scenario validates the site using the Hugo module

### Requirement: Engine Backed Rendering
The static-site scenario SHALL render static sites by composing the selected static-site engine module and returning the rendered directory.

#### Scenario: Scenario renders a Hugo site
- **WHEN** a caller passes a Hugo site directory, selected engine, and base URL to the scenario render function
- **THEN** the scenario returns the rendered static-site directory using the Hugo module

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
The static-site scenario SHALL accept already computed site URLs and SHALL NOT derive GitHub or GitLab preview metadata from provider-specific environment variables.

#### Scenario: Caller supplies preview URL
- **WHEN** a GitHub Actions or GitLab CI workflow calls the scenario for a preview
- **THEN** the workflow passes the preview base URL explicitly

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

### Requirement: Merged OpenSpec Path Collision Validation
The static-site automation SHALL detect conflicting virtual paths when multiple OpenSpec modules mount into shared specs or changes archive targets.

#### Scenario: Unique spec paths pass
- **WHEN** multiple OpenSpec modules contribute different paths under `specs`
- **THEN** the static-site automation accepts the merged specs target

#### Scenario: Duplicate spec paths fail
- **WHEN** multiple OpenSpec modules contribute the same virtual path under `content/docs/specs`
- **THEN** the static-site automation fails with a collision error that identifies the conflicting modules and path

#### Scenario: Duplicate archive paths fail
- **WHEN** multiple OpenSpec modules contribute the same virtual path under `content/docs/changes/archive`
- **THEN** the static-site automation fails with a collision error that identifies the conflicting modules and path
