# updatecli-module Specification

## Purpose

Describe the current Updatecli module behavior for running Updatecli manifests in a configurable runtime container.

## Requirements

### Requirement: Updatecli module accepts a custom runtime container
The system SHALL let callers replace the runtime container with a caller-provided container, such as the module container with bound services. Later runtime additions and Updatecli commands SHALL use the replaced container.

#### Scenario: Run Updatecli in a custom container
- **GIVEN** a caller takes the module container, adds an environment variable to it, and passes the result to `with_container`
- **WHEN** the caller previews or applies a manifest whose shell resource reads that variable
- **THEN** Updatecli SHALL run in the provided container and the returned output SHALL contain the variable value
