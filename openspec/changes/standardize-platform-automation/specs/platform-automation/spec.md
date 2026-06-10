## ADDED Requirements

### Requirement: Shared platform automation home

Riftonix SHALL provide a shared automation home for organization-level CI and dependency update conventions.

#### Scenario: Locate shared automation

- **WHEN** a maintainer needs to update reusable automation for Riftonix repositories
- **THEN** the reusable Renovate presets, reusable GitHub Actions workflows, composite actions, and migration documentation SHALL be available from one shared automation repository or organization automation repository
- **AND** consumer repositories SHALL reference that shared automation instead of copying full workflow and Renovate configuration bodies

#### Scenario: Explain platform boundary

- **WHEN** a contributor reads the shared automation documentation
- **THEN** the documentation SHALL explain that Dagger modules and scenarios own provider-neutral execution logic
- **AND** GitHub Actions workflows own provider event handling, permissions, job orchestration, and GitHub-specific publication mechanics
- **AND** Renovate presets own dependency update policy

### Requirement: Composable Renovate presets

The shared automation home SHALL provide composable Renovate presets for common Riftonix repository concerns.

#### Scenario: Configure a consumer repository

- **WHEN** a repository enables shared Renovate policy
- **THEN** its repository-local `renovate.json` SHALL extend one or more shared presets
- **AND** the repository-local file SHALL contain only repository-specific overrides that cannot reasonably live in a shared preset

#### Scenario: Select technology presets

- **WHEN** a repository uses a specific technology stack such as Dagger, Docker Bake, Hugo, Go, Terraform, or Helm
- **THEN** the repository SHALL opt into the matching shared preset for that technology
- **AND** unrelated technology presets SHALL NOT be required for that repository

#### Scenario: Update Dagger toolchain pins

- **WHEN** a repository opts into the Dagger Renovate preset
- **THEN** Renovate SHALL detect supported Dagger CLI pins in GitHub Actions workflows
- **AND** Renovate SHALL open dependency update pull requests according to the shared preset policy

#### Scenario: Update Daggerverse references

- **WHEN** a repository opts into the Daggerverse Renovate preset
- **THEN** Renovate SHALL detect supported released Daggerverse module and scenario references in repository automation
- **AND** Renovate SHALL extract versions from Daggerverse release tags

### Requirement: Reusable GitHub Actions workflows

The shared automation home SHALL provide reusable GitHub Actions workflows for common Riftonix repository workflows.

#### Scenario: Call reusable workflow from consumer repository

- **WHEN** a consumer repository needs a common CI or publication workflow
- **THEN** the repository SHALL define a thin workflow that calls a shared reusable workflow through a versioned `uses` reference
- **AND** the repository SHALL pass repository-specific values through explicit workflow inputs and secrets

#### Scenario: Keep repository-owned workflow policy visible

- **WHEN** a consumer repository defines a workflow that calls shared automation
- **THEN** the repository workflow SHALL keep repository-specific triggers, branch filters, path filters, permissions, and concurrency policy visible in the consumer repository
- **AND** the shared reusable workflow SHALL NOT require repository owners to hide those policies inside the shared automation repository

#### Scenario: Preserve provider-neutral Dagger logic

- **WHEN** a reusable workflow performs domain work such as image verification, static-site rendering, Helm checks, or component publication
- **THEN** it SHALL call an appropriate Dagger module or scenario for provider-neutral execution logic
- **AND** it SHALL NOT reimplement existing Dagger scenario behavior in workflow shell code

### Requirement: Composite GitHub Actions

The shared automation home SHALL provide composite GitHub Actions only for reusable step-level behavior.

#### Scenario: Share Dagger setup steps

- **WHEN** multiple reusable workflows need to install or configure Dagger
- **THEN** they SHALL be able to call a shared composite action for Dagger setup
- **AND** the composite action SHALL accept the Dagger version as an explicit input

#### Scenario: Share local act source detection

- **WHEN** a reusable workflow supports local execution through `act`
- **THEN** it SHALL be able to call a shared composite action or documented step sequence that resolves the bound local source directory
- **AND** the workflow SHALL use that source directory instead of assuming a GitHub checkout path during local execution

#### Scenario: Keep job graphs in reusable workflows

- **WHEN** automation needs matrices, job dependencies, reusable workflow outputs, or job-level permissions
- **THEN** that automation SHALL be implemented as a reusable workflow
- **AND** it SHALL NOT be implemented only as a composite action

### Requirement: Local act support

Shared workflows SHALL support local `act` execution where the workflow behavior can reasonably run outside GitHub-hosted infrastructure.

#### Scenario: Run supported workflow locally

- **WHEN** a repository workflow is documented as `act`-supported
- **THEN** the repository SHALL include or reference the needed `act` configuration and event fixture
- **AND** local execution SHALL run the same reusable workflow path as hosted GitHub Actions

#### Scenario: Skip provider-only steps locally

- **WHEN** a supported local `act` run reaches a step that requires GitHub-only infrastructure
- **THEN** the workflow SHALL skip or replace that step for local execution
- **AND** the workflow SHALL keep local verification behavior meaningful

#### Scenario: Document unsupported local execution

- **WHEN** a workflow cannot reasonably run through `act`
- **THEN** the shared automation documentation SHALL state that limitation
- **AND** the documentation SHALL explain which hosted GitHub feature prevents local execution

### Requirement: Versioned automation references

Consumer repositories SHALL reference shared automation through stable versioned references after initial adoption.

#### Scenario: Pin reusable workflow

- **WHEN** a consumer repository calls a shared reusable workflow
- **THEN** the `uses` reference SHALL point to a stable tag or release branch
- **AND** routine changes in the shared automation repository SHALL NOT affect the consumer until the reference is updated

#### Scenario: Upgrade shared automation

- **WHEN** a shared automation version is updated
- **THEN** Renovate or an equivalent documented process SHALL open or guide a pull request in consumer repositories
- **AND** the pull request SHALL show the automation reference being changed

### Requirement: Makefile retirement

Riftonix repositories SHALL remove or demote Makefile automation only after equivalent workflow and local execution paths exist.

#### Scenario: Retire a repository Makefile

- **WHEN** a repository removes a Makefile target that was used for CI or local verification
- **THEN** an equivalent GitHub Actions workflow path SHALL exist
- **AND** a documented local `act` command or documented replacement command SHALL exist
- **AND** branch protection or CI required checks SHALL continue to validate the same behavior

#### Scenario: Keep transitional Makefile

- **WHEN** a repository has not yet migrated a Makefile-backed workflow to shared automation
- **THEN** the Makefile MAY remain temporarily
- **AND** the migration tasks SHALL identify the workflow or Dagger scenario that will replace each remaining target

### Requirement: Migration examples

The shared automation documentation SHALL include migration examples for representative Riftonix repository archetypes.

#### Scenario: Migrate static site repository

- **WHEN** a maintainer migrates `riftonix.github.io` or another static-site repository
- **THEN** the documentation SHALL show the shared Renovate presets and reusable static-site workflows needed for CI, preview, production publish, and local `act` execution

#### Scenario: Migrate container image repository

- **WHEN** a maintainer migrates `container-images` or another image monorepo
- **THEN** the documentation SHALL show the shared Renovate presets and reusable container image workflows needed for changed target verification, publication, registry authentication, and release tag publication

#### Scenario: Migrate Daggerverse repository

- **WHEN** a maintainer migrates `daggerverse`
- **THEN** the documentation SHALL show the reusable workflows needed for quality checks, component test discovery, module and scenario publication, and tag-triggered release publication

#### Scenario: Migrate older repository archetypes

- **WHEN** a maintainer migrates Go, Terraform, or Helm repositories
- **THEN** the documentation SHALL identify the matching shared workflow and Renovate preset combination for that repository archetype
