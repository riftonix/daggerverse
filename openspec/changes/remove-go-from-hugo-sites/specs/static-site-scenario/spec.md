## ADDED Requirements

### Requirement: Explicit Content Composition
The static-site scenario SHALL accept aligned external content source, source path, target path, and contributor inputs and materialize their files in the Hugo site tree before verification or rendering.

#### Scenario: External content is rendered at the selected target
- **WHEN** a caller supplies a directory, source path, target path, and contributor name as a content mount
- **THEN** the scenario includes the source files under the target path in the rendered site

#### Scenario: Site renders without Go metadata
- **WHEN** a caller composes external content into an npm-based Hugo site with no Go module files
- **THEN** verification and rendering complete without Hugo Module resolution

### Requirement: Content Mount Collision Validation
The static-site scenario SHALL reject content mounts when more than one contributor maps a file to the same target path.

#### Scenario: Unique content paths pass
- **WHEN** all mounted files have unique target paths
- **THEN** the scenario accepts and composes the mounts

#### Scenario: Duplicate content paths fail
- **WHEN** two or more mounts map files to the same target path
- **THEN** the scenario fails before invoking Hugo and identifies the conflicting path and contributors

## MODIFIED Requirements

### Requirement: Engine Backed Verification
The static-site scenario SHALL verify static sites by composing explicit content mounts into the constructor `source` directory and passing the resulting site tree to the selected static-site engine module.

#### Scenario: Scenario verifies a Hugo site
- **WHEN** a caller passes an npm-based site source, optional content mounts, selected engine, and base URL to the static-site scenario
- **THEN** the scenario validates the composed site using the Hugo module
- **AND** the verification function SHALL NOT accept a separate site directory input

### Requirement: Engine Backed Rendering
The static-site scenario SHALL render static sites by composing explicit content mounts into the constructor `source` directory and returning the rendered directory from the selected engine module.

#### Scenario: Scenario renders a Hugo site
- **WHEN** a caller passes an npm-based site source, optional content mounts, selected engine, and base URL to the static-site scenario
- **THEN** the scenario returns the rendered composed site using the Hugo module
- **AND** the render function SHALL NOT accept a separate site directory input

### Requirement: Multi Component Documentation Mount Layout
The static-site automation SHALL support composing component documentation and OpenSpec content through explicit directory mounts without Hugo Modules.

#### Scenario: Daggerverse docs module is mounted under component documentation
- **WHEN** a caller mounts a component `docs/content` directory
- **THEN** the caller can select a target such as `content/docs/components/daggerverse`

#### Scenario: Container images docs module is mounted under component documentation
- **WHEN** a caller mounts the container images `docs/content` directory
- **THEN** the caller can select `content/docs/components/container-images` as its target

#### Scenario: OpenSpec specs are mounted under shared specs
- **WHEN** a caller mounts component `openspec/specs` and `openspec/changes/archive` directories
- **THEN** the caller can select `content/docs/specs` as the specs target

#### Scenario: OpenSpec archive is mounted under shared changes archive
- **WHEN** a caller mounts a component `openspec/changes/archive` directory
- **THEN** the caller can select `content/docs/changes/archive` as its target

#### Scenario: Main site render validates composed modules
- **WHEN** static-site automation renders the main Hugo site with explicit content mounts
- **THEN** the rendered site includes component documentation, shared specs, and shared archived changes

### Requirement: Static Site Hugo Runtime Image Inputs
The static-site scenario SHALL expose Hugo runtime image and npm registry inputs on its public constructor when Hugo is a supported engine.

#### Scenario: Construct static-site scenario with Hugo image inputs
- **WHEN** a caller constructs the static-site scenario for Hugo-backed operations
- **THEN** the constructor SHALL accept `hugo_image_registry`, `hugo_image_repository`, `hugo_image_tag`, `hugo_container_user_id`, and `npm_registry`
- **AND** each image input SHALL default to the Hugo module default for the same runtime image field

#### Scenario: Verify passes Hugo image inputs
- **WHEN** a caller verifies a Hugo site through the static-site scenario
- **THEN** the scenario SHALL pass the configured Hugo runtime image and npm registry inputs to the Hugo module

#### Scenario: Render passes Hugo image inputs
- **WHEN** a caller renders a Hugo site through the static-site scenario
- **THEN** the scenario SHALL pass the configured Hugo runtime image and npm registry inputs to the Hugo module
- **AND** the rendered output SHALL come from the configured Hugo execution image

#### Scenario: Static-site workflow pins Hugo image tag
- **WHEN** a CI workflow needs reproducible Hugo rendering
- **THEN** it SHALL be able to pin the Hugo runtime through `hugo_image_tag`
- **AND** the pin SHALL be visible in the workflow rather than hidden in the Hugo module dependency default

#### Scenario: Static-site tests avoid direct Hugo module calls
- **WHEN** static-site scenario tests exercise Hugo-backed scenario operations
- **THEN** they SHALL call the static-site scenario API with configured Hugo runtime inputs
- **AND** direct Hugo module integration checks SHALL live in the Hugo module tests

## REMOVED Requirements

### Requirement: Engine Specific Capabilities Stay Outside Scenario
**Reason:** Hugo Module preparation is removed rather than retained as an engine-specific capability.

**Migration:** Use npm for theme dependencies and static-site content mounts for external content.

### Requirement: Hugo Mount Path Collision Validation
**Reason:** Collision validation now applies to explicit static-site content mounts rather than Hugo `module.imports`.

**Migration:** Replace Hugo import configuration and ordered module arguments with explicit content mount inputs.

### Requirement: Required Hugo Theme URL
**Reason:** The site owns its npm theme dependency and Hugo configuration, so the scenario no longer resolves a theme URL.

**Migration:** Declare `@docsy/theme` in `package.json`, commit `package-lock.json`, and configure `theme` and `themesDir` in the Hugo configuration.
