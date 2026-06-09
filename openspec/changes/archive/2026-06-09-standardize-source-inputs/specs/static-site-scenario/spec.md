## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: Provider Neutral Inputs
The static-site scenario SHALL accept already computed site URLs and a caller-provided `source` tree and SHALL NOT derive GitHub or GitLab preview metadata from provider-specific environment variables.

#### Scenario: Caller supplies preview URL
- **WHEN** a GitHub Actions or GitLab CI workflow calls the scenario for a preview
- **THEN** the workflow passes the preview base URL explicitly
- **AND** the workflow passes the checked-out site tree through `source`
- **AND** the scenario SHALL NOT inspect provider-specific event environment variables or checkout policy
