## ADDED Requirements

### Requirement: Git module exposes a tested provider-neutral CI API

The Git module SHALL expose provider-neutral Dagger functions for CI workflows using Git refs, SHAs, paths, remotes, and credentials as inputs.

#### Scenario: Use Git module outside a specific CI provider

- **WHEN** a caller provides repository source and explicit Git refs or SHAs
- **THEN** the Git module SHALL compute results without requiring GitHub-specific, GitLab-specific, or Bitbucket-specific environment variables

#### Scenario: Public function names use verbs

- **WHEN** a public Git module function is added or renamed
- **THEN** the function name SHALL start with an action verb such as `get`, `has`, `with`, `create`, `push`, or `ensure`
- **AND** chainable state-transforming functions SHALL use `with_*` names and return an updated `Git` object

### Requirement: Git module has Dagger-native tests

The Git module SHALL have a neighboring Dagger test module that validates public Git behavior through the module public API.

#### Scenario: Run Git module tests

- **WHEN** a user or CI runs `make tests git`
- **THEN** the Git test module SHALL run its aggregate `all` function
- **AND** the tests SHALL call the parent Git module through a local Dagger dependency

#### Scenario: Implement Git module feature

- **WHEN** a Git module feature is implemented
- **THEN** the same implementation step SHALL add or update Dagger-native tests for that feature

### Requirement: Git module fetches refs and tags

The Git module SHALL provide fetch functions that make required refs and tags available inside the module container.

#### Scenario: Fetch refs for CI diff

- **WHEN** a caller calls `with_fetched_refs` with a remote and one or more refspecs
- **THEN** the module SHALL fetch those refs into the repository
- **AND** subsequent ref resolution and diff functions SHALL be able to use the fetched refs

#### Scenario: Fetch tags for release checks

- **WHEN** a caller calls `with_fetched_tags`
- **THEN** the module SHALL fetch tags from the selected remote
- **AND** tag listing and tag lookup functions SHALL include fetched remote tags

#### Scenario: Unshallow repository for history-dependent CI checks

- **WHEN** a caller calls `with_unshallow`
- **THEN** the module SHALL ensure the repository has full history when the repository is shallow
- **AND** the module SHALL leave already full-history repositories usable for subsequent Git functions

#### Scenario: Ensure required ref exists

- **WHEN** a caller calls `ensure_ref` for a missing ref
- **THEN** the module SHALL fail with a clear error that identifies the missing ref

### Requirement: Git module resolves repository metadata

The Git module SHALL expose functions for common repository metadata needed by CI.

#### Scenario: Get commit identifiers

- **WHEN** a caller requests the current commit identifiers
- **THEN** the module SHALL provide `get_head_sha` for the full `HEAD` SHA
- **AND** `get_short_commit_sha` for a configurable short SHA

#### Scenario: Get current ref metadata

- **WHEN** a caller requests current ref metadata
- **THEN** the module SHALL provide functions such as `get_current_branch`, `get_current_ref`, `get_remote_url`, and `get_default_branch`

#### Scenario: Check repository state

- **WHEN** a caller needs to verify the working tree state
- **THEN** the module SHALL provide functions such as `get_status_porcelain` and `has_clean_worktree`

### Requirement: Git module computes merge bases and changed files

The Git module SHALL provide reliable diff primitives for pull request, branch, and release workflows.

#### Scenario: Get merge base

- **WHEN** a caller provides `base_ref` and `head_ref`
- **THEN** `get_merge_base` SHALL return the merge-base commit shared by those refs

#### Scenario: Get changed files

- **WHEN** a caller provides `base_ref`, `head_ref`, and optional path filters
- **THEN** `get_changed_files` SHALL return changed file paths between those refs
- **AND** the caller SHALL be able to configure Git diff filters

#### Scenario: Get changed directories

- **WHEN** a caller provides `base_ref`, `head_ref`, and optional path filters
- **THEN** `get_changed_dirs` SHALL return unique changed directories at the requested depth or scope

#### Scenario: Check whether paths changed

- **WHEN** a caller provides paths and two refs
- **THEN** `has_changes` SHALL return whether any matching path changed between the refs

### Requirement: Git module maps changes to components

The Git module SHALL provide changed-component helpers for monorepos and single-component repositories.

#### Scenario: Get changed components in a monorepo

- **WHEN** a caller provides component roots and changed files
- **THEN** `get_changed_components` SHALL return the components whose files changed

#### Scenario: Shared path affects all components

- **WHEN** a changed file matches a configured shared path
- **THEN** `get_changed_components` SHALL return all discovered components

#### Scenario: Single-component repository changed

- **WHEN** a caller uses single-component mode and matching files changed
- **THEN** `get_changed_components` SHALL return `["."]`

#### Scenario: Discover components

- **WHEN** a caller provides component root patterns
- **THEN** `get_components` SHALL return matching component roots in a stable sorted order

### Requirement: Git module manages tags for CI releases

The Git module SHALL provide tested tag functions for release and publication workflows.

#### Scenario: List and check tags

- **WHEN** a caller requests tags
- **THEN** `get_tags` SHALL return matching tags
- **AND** `has_tag` SHALL return whether a tag exists

#### Scenario: Get latest matching tag

- **WHEN** a caller requests the latest tag for a pattern
- **THEN** `get_latest_tag` SHALL return the latest matching tag according to the selected sort mode

#### Scenario: Get tags pointing at a ref

- **WHEN** a caller requests tags pointing at a ref
- **THEN** `get_tags_pointing_at` SHALL return tags that point at that ref

#### Scenario: Create and push tag

- **WHEN** a caller creates and pushes a tag
- **THEN** `create_tag` SHALL create the tag locally
- **AND** `push_tag` SHALL push the tag to the selected remote

### Requirement: Git module configures portable authentication

The Git module SHALL support portable Git authentication for hosts such as GitHub, GitLab, and Bitbucket.

#### Scenario: Configure HTTPS token authentication

- **WHEN** a caller provides an HTTPS token secret and remote host
- **THEN** `with_https_token_auth` SHALL configure Git operations for that host without exposing the token in returned output

#### Scenario: Configure SSH key authentication

- **WHEN** a caller provides an SSH private key secret and known hosts data
- **THEN** `with_ssh_key_auth` SHALL configure Git SSH operations without exposing the key in returned output

### Requirement: Git module documentation matches implementation

The Git module README and repository documentation SHALL describe the actual public API and supported CI patterns.

#### Scenario: Read Git module documentation

- **WHEN** a user reads `modules/git/README.md`
- **THEN** every documented public function SHALL exist in the module implementation
- **AND** examples SHALL use verb-based function names
