## Context

The current Git module exposes a small subset of useful CI behavior. It can create a git container, list local tags, return a short commit SHA, and detect changed top-level paths against a target branch. However, `fetch_tags` and `create_and_push_tag` are documented but commented out, and `get_tags_pointing_at_head` calls the missing `fetch_tags` method.

For CI usage, the module must handle both monorepos and single-component repositories. It should work with GitHub Actions immediately, but the API must remain provider-neutral so GitLab and Bitbucket can pass equivalent refs, SHAs, remotes, and tokens later.

## Goals / Non-Goals

**Goals:**

- Provide a reliable Git Dagger module for CI decisions in monorepos and single-component repositories.
- Use provider-neutral Git inputs: refs, SHAs, paths, remotes, and credentials.
- Make every public function use a verb-based name.
- Implement feature and Dagger-native tests in the same task step.
- Keep the module usable from higher-level pipeline modules without shelling out to the Dagger CLI.
- Align `modules/git` with Dagger `v0.20.6`.

**Non-Goals:**

- Implement GitHub, GitLab, or Bitbucket API clients.
- Parse provider-specific event JSON inside the Git module.
- Build a full release automation system.
- Push commits or modify repository content beyond tag creation and tag push operations.

## Decisions

### Provider-Neutral API

The module will accept explicit Git refs and SHAs instead of reading `GITHUB_*`, `CI_*`, or Bitbucket environment variables directly. CI provider adapters may be added later in pipeline modules, but the Git module remains a reusable primitive.

Examples:

- `get_changed_files(base_ref, head_ref)`
- `get_merge_base(base_ref, head_ref)`
- `get_changed_components(base_ref, head_ref, component_roots, shared_paths)`

Alternative considered: provider-specific helpers such as `get_github_pull_request_changes`. This was rejected because it would couple a low-level Git module to one CI system and duplicate behavior for GitLab and Bitbucket.

### Feature And Tests Move Together

Each implementation task must include both the feature and its Dagger-native test coverage. The Git module will receive a neighboring test module under `modules/git/tests` before new behavior is considered complete.

Alternative considered: implement all behavior first, then test at the end. This was rejected because Git edge cases are easy to miss and the user explicitly wants each step covered immediately.

### Synthetic Git Fixtures

Tests should create deterministic local repositories inside Dagger containers or use checked-in fixture scripts/data that produce repositories with branches, merge bases, tags, untracked files, changed components, and shared-path changes.

Alternative considered: testing against the current repository only. This was rejected because the current repository state is not a stable fixture for merge-base, tag, and changed-component scenarios.

### Changed Components Are Built On Changed Files

The API should keep primitive functions and higher-level functions separate:

- Primitive functions return changed files and directories.
- Component functions map changed files to component roots.
- Pipeline modules decide what checks to run for returned components.

This keeps `modules/git` universal while still supporting monorepo CI.

### Authentication Is Generic

Authentication helpers should configure Git remotes with either HTTPS token credentials or SSH key material. They should not assume a single host.

Credentials must use `dagger.Secret` and must not be returned in stdout, logs, or artifact files.

## Risks / Trade-offs

- Shallow checkouts may not contain required refs or merge bases -> provide `fetch_refs`, `fetch_tags`, and clear failure messages from `ensure_ref`.
- Different CI providers expose different ref naming conventions -> keep provider-specific translation outside this module and accept explicit refs/SHAs.
- Component glob behavior can become ambiguous -> document accepted patterns and test root glob, explicit root, and shared-path scenarios.
- Tag sorting can be surprising for non-semver tags -> provide `get_latest_tag(pattern, semver=True)` with tested behavior and fallback lexical/version ordering.
- Tag push tests can require network remotes -> use local bare repositories as remotes in tests.

## Migration Plan

1. Add a Dagger-native Git test module and cover current behavior before changing APIs.
2. Restore or remove documented-but-missing functions so README and implementation match.
3. Add new verb-based APIs with tests.
4. Update dependent modules, especially `modules/pipelines`, to use the restored API.
5. Update docs after each API group is implemented.
6. Remove the legacy shell test once the Dagger-native test module is authoritative.
