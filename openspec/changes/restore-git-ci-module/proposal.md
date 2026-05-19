## Why

`modules/git` is intended to support CI decisions, but its current implementation is incomplete: documented functions are commented out, tag lookup is not reliable in shallow checkouts, and changed-path detection is too narrow for pull request and release workflows.

Repository CI modules need a universal Git foundation that works for GitHub now and can also support GitLab and Bitbucket later by operating on Git refs, commits, tags, and paths rather than provider-specific event payloads.

## What Changes

- Restore `modules/git` so documented functions are either implemented and tested or removed from the public contract.
- Align the Git module with the repository Dagger version and Dagger-native test pattern.
- Add Git primitives for fetching refs and tags, resolving commits, computing merge bases, and inspecting repository metadata.
- Add changed-file and changed-directory APIs with explicit base/head inputs.
- Add changed-component APIs for monorepos, including shared-path behavior and a single-component mode.
- Add tag and release helper APIs using verb-based function names, such as `get_latest_tag`, `has_tag`, `get_tags_pointing_at`, `create_tag`, and `push_tag`.
- Add authentication configuration that is portable across Git hosts by using generic HTTPS token or SSH credentials.
- Add Dagger-native tests for each feature as it is implemented.
- Update README and repository documentation to match the actual Git module API.
- **BREAKING**: Replace or deprecate ambiguous function names where needed so public functions consistently use verbs.

## Capabilities

### New Capabilities

- `git-ci-module`: Defines the restored Git Dagger module contract for universal CI use across single-component repositories and monorepos.

### Modified Capabilities

- `daggerverse`: The repository module testing baseline is extended so the Git module follows the same Dagger-native test module and CI command conventions as Helm.

## Impact

- Affected code: `modules/git`, `modules/git/tests`, `modules/pipelines`, root `Makefile`, and related docs.
- Affected APIs: Git module public Dagger functions for changed paths, refs, tags, metadata, and authentication.
- Affected tests: replace shell smoke tests with a Dagger-native Git test module using synthetic Git repository fixtures.
- Affected docs: `modules/git/README.md`, module reference, CI conventions, and Git CI usage guidance.
