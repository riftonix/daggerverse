## ADDED Requirements

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
