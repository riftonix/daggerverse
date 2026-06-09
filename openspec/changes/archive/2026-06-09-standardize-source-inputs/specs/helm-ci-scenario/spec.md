## MODIFIED Requirements

### Requirement: Helm CI scenario verifies one chart
The `scenarios/helm-ci` scenario SHALL verify a Helm chart directory supplied explicitly by the caller through the public input named `source`.

#### Scenario: Verify one chart
- **WHEN** a caller provides a Helm chart directory to the `helm-verify` function as `source`
- **THEN** the scenario SHALL run Helm lint through the Helm module
- **AND** it SHALL run Helm template through the Helm module
- **AND** lint or template failures SHALL fail the scenario function call

#### Scenario: Verify one chart with values
- **WHEN** a caller provides an optional values file or release name
- **THEN** the scenario SHALL pass those inputs to the Helm template operation

### Requirement: Helm CI scenario publishes one chart
The `scenarios/helm-ci` scenario SHALL publish a Helm chart supplied through the public input named `source` to an OCI registry using destination and version inputs supplied explicitly by the caller.

#### Scenario: Publish one chart
- **WHEN** a caller provides a chart directory as `source`, OCI registry URL, and chart version to the `helm-publish` function
- **THEN** the scenario SHALL package and push the chart through the Helm module
- **AND** publication failures SHALL fail the scenario function call

#### Scenario: Publish with registry credentials
- **WHEN** a caller provides registry username and password inputs
- **THEN** the scenario SHALL authenticate through the Helm module before pushing
- **AND** the scenario SHALL NOT expose registry secrets in returned output

### Requirement: Helm CI scenario verifies changed charts
The `scenarios/helm-ci` scenario SHALL verify changed Helm chart directories selected through provider-neutral Git and path inputs, with the repository checkout supplied through the public input named `source`.

#### Scenario: Verify changed chart directories
- **WHEN** a caller provides a repository source, target branch, and chart path to the `helm-verify-changed-charts` function
- **THEN** the scenario SHALL ask the Git module for changed directories since the merge base with the target branch
- **AND** it SHALL run Helm verification for each changed chart directory
- **AND** it SHALL return an empty list when no chart directories changed
- **AND** `charts_path` SHALL remain a secondary path inside the repository source rather than a replacement for `source`

#### Scenario: Verify changed library directories
- **WHEN** a caller provides a library path as an additional diff root
- **THEN** the scenario SHALL include changed directories under that library path when selecting charts to verify
- **AND** `libs_path` SHALL remain a secondary path inside the repository source rather than a replacement for `source`

#### Scenario: Skip charts without required metadata
- **WHEN** a changed chart directory has no chart name or version in `Chart.yaml`
- **THEN** the scenario SHALL skip that chart directory
- **AND** it SHALL include a returned message explaining that required metadata is missing
