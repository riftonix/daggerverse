## Purpose

Runtime container image defaults in Dagger modules, scenarios, and tests are declared consistently and are discoverable by Renovate for coordinated dependency updates.

## Requirements

### Requirement: Runtime image defaults are declared as image constants

Dagger modules, scenarios, and tests that expose runtime container image defaults MUST declare each managed image as separate registry, repository, and tag constants using names that end in `_IMAGE_REGISTRY`, `_IMAGE_REPOSITORY`, and `_IMAGE_TAG`.

#### Scenario: Module runtime image defaults use constants
- **WHEN** a module exposes a default runtime image through Dagger inputs
- **THEN** the default registry, repository, and tag values are provided by module-level image constants instead of inline string literals

#### Scenario: Test-only runtime image defaults use constants
- **WHEN** a test requires an additional runtime image that is not the module default image
- **THEN** the test image registry, repository, and tag values are provided by test module image constants instead of inline function default literals

#### Scenario: New module introduces a runtime image default
- **WHEN** a new Python Dagger module, scenario, or test introduces a default runtime image
- **THEN** the new code declares registry, repository, and tag values with the repository image constants convention instead of inline string literals

### Requirement: Module tests use module image defaults by default

Tests for a module MUST rely on the module default runtime image unless the test needs a distinct image input for that test behavior.

#### Scenario: Test exercises module default image
- **WHEN** a module test does not need to override the module runtime image
- **THEN** the test invokes the module without passing duplicated image registry, repository, or tag arguments

#### Scenario: Test needs an additional runtime image
- **WHEN** a module test needs an additional runtime image that is separate from the module default image
- **THEN** the additional image is declared with its own image constants and Renovate-managed tag annotation

### Requirement: Renovate annotations identify managed image tags

Every Renovate-managed runtime image tag constant MUST be immediately preceded by a one-line Renovate annotation comment in the strict format `# renovate: datasource=<datasource> depName=<depName>`.

#### Scenario: Image tag constant has an annotation
- **WHEN** a Python assignment sets a Renovate-managed `*_IMAGE_TAG` value
- **THEN** the line immediately before the assignment contains only a `# renovate: datasource=docker depName=<depName>` annotation

#### Scenario: Matching images use matching dependency names
- **WHEN** the same runtime image is declared in a module, a scenario, and related tests
- **THEN** each annotation uses the same `datasource` and `depName` so Renovate can update them together

### Requirement: Renovate extracts annotated Python image tags

The Renovate configuration MUST include a Python custom manager that extracts annotated `*_IMAGE_TAG` assignments and updates their string values using the dependency metadata from the preceding annotation.

#### Scenario: Renovate finds an annotated image tag
- **WHEN** Renovate scans a Python file containing a supported image tag annotation followed by a `*_IMAGE_TAG` assignment
- **THEN** Renovate treats the assignment value as the current Docker image tag for the annotated dependency

#### Scenario: Renovate updates repeated dependency declarations together
- **WHEN** multiple annotated Python image tag constants have the same Docker dependency identity
- **THEN** Renovate includes the matching tag updates in the same dependency update MR unless package rules explicitly split them

### Requirement: Runtime image convention is documented for authors

The repository documentation MUST describe the runtime image constants and Renovate annotation convention for authors of new modules, scenarios, and tests.

#### Scenario: Author adds a new runtime image default
- **WHEN** a contributor reads the repository documentation for authoring modules or scenarios
- **THEN** the documentation explains the required `*_IMAGE_REGISTRY`, `*_IMAGE_REPOSITORY`, `*_IMAGE_TAG`, and `# renovate: datasource=docker depName=<depName>` pattern
