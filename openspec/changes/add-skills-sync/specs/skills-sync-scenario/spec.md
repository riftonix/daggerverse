# Skills Sync Scenario Delta Specification

## Purpose

Keep a published agent skills index and its skill directories synchronized with their upstream git repositories and npm packages, and propose upstream updates as reviewable pull requests.

## ADDED Requirements

### Requirement: Skills sync scenario location and inputs
The system SHALL provide the skills sync scenario under `scenarios/skills-sync`. It SHALL accept the site repository tree as `source`, the index location as `index_path` (default `static/.well-known/skills/index.json`), and prefixed Updatecli runtime image inputs passed to the Updatecli module.

#### Scenario: Use the default index location
- **GIVEN** a caller provides `source` without `index_path`
- **WHEN** the caller runs any scenario function
- **THEN** the scenario SHALL read `static/.well-known/skills/index.json` from `source`
- **AND** it SHALL treat `<index directory>/<entry name>` as the directory of each skill

#### Scenario: Override the Updatecli runtime image
- **GIVEN** a caller provides `updatecli_image_registry`, `updatecli_image_repository`, `updatecli_image_tag`, or `updatecli_container_user_id`
- **WHEN** the caller runs any scenario function
- **THEN** the scenario SHALL pass those values to the Updatecli module

### Requirement: Skills index provenance metadata
The system SHALL read upstream provenance from string-valued keys in each index entry `metadata`: `sourceType`, `source`, `path`, `ref`, and `revision`. `sourceType` SHALL be `git` or `npm`. These keys are a Riftonix convention and are not defined by the Agent Skills specification or the Agent Skills Discovery RFC.

#### Scenario: Git provenance
- **GIVEN** an entry with `sourceType` `git`
- **WHEN** the scenario reads the entry
- **THEN** it SHALL interpret `source` as the repository URL, `path` as the skill directory inside the repository, `ref` as the tracked branch, and `revision` as the synchronized commit SHA

#### Scenario: Npm provenance
- **GIVEN** an entry with `sourceType` `npm`
- **WHEN** the scenario reads the entry
- **THEN** it SHALL interpret `source` as the package name, `path` as the skill directory inside the package tree, `ref` as the tracked dist-tag, and `revision` as the synchronized package version

#### Scenario: Empty ref and revision
- **GIVEN** an entry with an empty or missing `ref` or `revision`
- **WHEN** the scenario resolves the upstream revision
- **THEN** an empty `ref` SHALL mean the repository default branch for `git` and the `latest` dist-tag for `npm`
- **AND** an empty `revision` SHALL mean the skill has never been synchronized

### Requirement: Skills index validation
The system SHALL validate the index before rendering pipelines and SHALL fail with a message that names every invalid entry.

#### Scenario: Entry without provenance
- **GIVEN** an index entry without `sourceType`, `source`, or `path`
- **WHEN** the caller runs any scenario function
- **THEN** the call SHALL fail and name that entry

#### Scenario: Unsupported source type
- **GIVEN** an index entry whose `sourceType` is not `git` or `npm`
- **WHEN** the caller runs any scenario function
- **THEN** the call SHALL fail and name that entry and value

#### Scenario: Duplicate skill names
- **GIVEN** two index entries with the same `name`
- **WHEN** the caller runs any scenario function
- **THEN** the call SHALL fail and name the duplicated skill

### Requirement: Upstream source groups
The system SHALL group index entries by `sourceType`, `source`, and effective `ref`, resolve the upstream revision once per group, and treat each group as one independent synchronization unit.

#### Scenario: Several skills share an upstream
- **GIVEN** 30 entries that share one git repository and branch
- **WHEN** the scenario synchronizes the index
- **THEN** it SHALL resolve the upstream revision once for those entries
- **AND** it SHALL propose their updates together

#### Scenario: One group fails
- **GIVEN** one upstream source is unreachable
- **WHEN** the scenario synchronizes the index
- **THEN** the other groups SHALL still be synchronized
- **AND** the function call SHALL fail and report the failed group

### Requirement: Upstream revision resolution
The system SHALL resolve a `git` group to the commit SHA at the head of its effective branch and an `npm` group to the package version of its effective dist-tag.

#### Scenario: Group is up to date
- **GIVEN** every entry in a group has a `revision` equal to the resolved upstream revision
- **WHEN** the scenario synchronizes the index
- **THEN** it SHALL leave the group skill directories and index entries unchanged
- **AND** it SHALL NOT propose a change for that group

#### Scenario: Group has a new upstream revision
- **GIVEN** at least one entry in a group has a `revision` different from the resolved upstream revision
- **AND** the upstream content of at least one skill in the group differs from the published skill or index entry
- **WHEN** the scenario synchronizes the index
- **THEN** it SHALL synchronize every entry in that group to the resolved revision

#### Scenario: Upstream revision moved without skill changes
- **GIVEN** a group whose upstream revision changed only in files outside every tracked skill `path`
- **AND** every entry already has a non-empty `revision`
- **WHEN** the scenario synchronizes the index
- **THEN** it SHALL leave the group skill directories and index entries unchanged, including `revision`
- **AND** it SHALL NOT propose a change for that group

### Requirement: Npm package trees
The system SHALL build an npm skill tree from the unpacked package contents, except for `@fission-ai/openspec`, whose tree SHALL be the output of the OpenSpec CLI `init` command at the resolved version, run non-interactively with telemetry and update checks disabled.

#### Scenario: Generate OpenSpec skills
- **GIVEN** an npm group for `@fission-ai/openspec`
- **WHEN** the scenario synchronizes the group
- **THEN** it SHALL generate skills with the `openspec_tools` input (default `cursor`) and the `openspec_profile` input (default `core`)
- **AND** each entry `path` SHALL select a directory in the generated output, such as `.cursor/skills/openspec-explore`

#### Scenario: Reproduce published OpenSpec text
- **GIVEN** OpenSpec version 1.12.0 and the default generator inputs
- **WHEN** the scenario generates `openspec-explore`
- **THEN** the generated `SKILL.md` SHALL be byte-identical to the `openspec-explore` skill currently published by `riftonix.github.io`

### Requirement: Skill directory synchronization
The system SHALL replace each synchronized skill directory with the files of its upstream `path` at the resolved revision, excluding `__pycache__` directories, `*.pyc` files, and files or directories whose name starts with `.`, and SHALL NOT modify file content except the frontmatter `name`.

#### Scenario: Upstream adds, changes, and removes files
- **GIVEN** an upstream skill directory that added, changed, and removed files since the recorded revision
- **WHEN** the scenario synchronizes the skill
- **THEN** the local skill directory SHALL contain exactly the upstream files after exclusions
- **AND** each copied file SHALL be byte-identical to upstream except for the frontmatter `name` line in `SKILL.md`

#### Scenario: Skill is renamed locally
- **GIVEN** an entry named `confluence-content-management` whose upstream `SKILL.md` frontmatter has `name: confluence`
- **WHEN** the scenario synchronizes the skill
- **THEN** the local `SKILL.md` frontmatter `name` SHALL be `confluence-content-management`

#### Scenario: Upstream path has no SKILL.md
- **GIVEN** an upstream `path` that exists but contains no `SKILL.md`
- **WHEN** the scenario synchronizes the skill
- **THEN** the group SHALL fail and name the skill and path

### Requirement: Index entry synchronization
The system SHALL rewrite each synchronized index entry from the upstream `SKILL.md` frontmatter: `description`, `license`, `metadata`, and `files`. It SHALL keep `name` and `path`, drop other fields, and SHALL NOT add values that upstream does not declare.

#### Scenario: Metadata comes from upstream frontmatter
- **GIVEN** an upstream frontmatter `metadata` with `author`, `version`, `tools`, and `category`
- **WHEN** the scenario synchronizes the entry
- **THEN** the entry `metadata` SHALL contain exactly those upstream keys and values as strings plus the provenance keys

#### Scenario: Upstream declares no version
- **GIVEN** an upstream frontmatter without `metadata.version`
- **WHEN** the scenario synchronizes the entry
- **THEN** the entry `metadata` SHALL NOT contain `version`
- **AND** fields outside `name`, `description`, `license`, `metadata`, `path`, and `files`, such as a top-level `version`, SHALL be removed

#### Scenario: Upstream metadata collides with provenance keys
- **GIVEN** an upstream frontmatter `metadata` that contains a provenance key such as `source`
- **WHEN** the scenario synchronizes the entry
- **THEN** the entry `metadata` SHALL keep the provenance value
- **AND** the scenario function output SHALL contain a warning that names the skill and key
- **AND** the published `SKILL.md` SHALL keep the upstream value

#### Scenario: Revision and files are updated
- **GIVEN** a synchronized skill
- **WHEN** the scenario writes the entry
- **THEN** `metadata.revision` SHALL be the resolved upstream revision
- **AND** `files` SHALL list every published file of the skill relative to its directory in sorted order

### Requirement: Upstream skill removal
The system SHALL remove a skill directory and its index entry when the entry `path` no longer exists in the upstream tree at the resolved revision.

#### Scenario: Upstream removed a skill
- **GIVEN** an entry for `k8s-browser` whose upstream path no longer exists
- **WHEN** the scenario synchronizes its group
- **THEN** the `k8s-browser` directory and index entry SHALL be removed
- **AND** the removal SHALL be part of the group's proposed change

### Requirement: Local preview and synchronization
The system SHALL expose a preview function that reports pending changes without modifying files and a synchronization function that returns the `source` tree with all groups synchronized, both without SCM access or credentials.

#### Scenario: Preview pending updates
- **GIVEN** an index with outdated groups
- **WHEN** the caller runs the preview function
- **THEN** the report SHALL name each outdated group, its current and resolved revisions, and the affected skills

#### Scenario: Synchronize locally
- **GIVEN** an index with outdated groups
- **WHEN** the caller runs the local synchronization function
- **THEN** the returned directory SHALL contain the synchronized skill directories and index

### Requirement: Pull request proposal
The system SHALL expose an update function that takes `github_token` as a secret, `repository` as `owner/name`, and `branch`, and creates or updates one pull request per changed group against `branch`, from a working branch name that is stable for the group.

#### Scenario: Group changed upstream
- **GIVEN** a group with a new upstream revision
- **WHEN** the caller runs the update function
- **THEN** a pull request against `branch` SHALL contain the group's file changes, removals, and index changes
- **AND** a later run for the same group SHALL update the same pull request

#### Scenario: Built-in CI token
- **GIVEN** the caller passes a GitHub Actions built-in token with contents and pull request write permissions
- **WHEN** the caller runs the update function
- **THEN** the scenario SHALL create commits and pull requests without any other credential
- **AND** the token value SHALL NOT appear in returned output

#### Scenario: Nothing changed upstream
- **GIVEN** every group is up to date
- **WHEN** the caller runs the update function
- **THEN** no pull request SHALL be created or updated

### Requirement: Skills sync scenario remains CI-provider portable
The system SHALL leave scheduling, pull request CI triggering, review, and merging to the caller workflow.

#### Scenario: Scheduled caller
- **GIVEN** a caller workflow that runs the update function on a schedule
- **WHEN** the scenario creates or updates pull requests
- **THEN** the scenario SHALL NOT trigger CI workflows, enable auto-merge, or merge pull requests

### Requirement: Skills sync scenario Dagger tests
The system SHALL provide a Dagger test module under `scenarios/skills-sync/tests` whose aggregate `all()` function verifies validation, grouping, synchronization, renaming, removal, and metadata rules using local fixtures and no credentials.

#### Scenario: Run skills sync scenario tests
- **GIVEN** the skills sync scenario test module
- **WHEN** a user or CI runs `make tests scenario skills-sync`
- **THEN** the aggregate test SHALL use local git repository and npm package fixtures
- **AND** any failed check SHALL fail the test run
