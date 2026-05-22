## 1. First steps

- [x] 1.1 Restore README/API consistency for `modules/git` by removing functions from documentation when they are not implemented.
- [x] 1.2 Align `modules/git` with Dagger `v0.20.6` and add a Dagger-native test module under `modules/git/tests` with an aggregate `all` function.
- [x] 1.3 Restore `fetch_tags` and fix `get_tags_pointing_at` with tests that use a local synthetic repository and local bare remote.
- [x] 1.4 Replace or wrap ambiguous public names with verb-based names, including `get_tags`, `get_tags_pointing_at`, and `get_short_commit_sha`, and cover compatibility behavior with tests.

## 2. PR Diff And Changed Paths

- [x] 2.1 Implement `get_merge_base(base_ref, head_ref)` and tests for diverged branches.
- [ ] 2.2 Implement `get_changed_files(base_ref, head_ref, paths=None, diff_filter='ACMRTUXB')` and tests for added, copied, modified, renamed, type-changed, unmerged, unknown, and broken files where practical.
- [ ] 2.3 Implement `get_changed_dirs(base_ref, head_ref, paths=None, depth=1, diff_filter='ACMRTUXB')` and tests for root-scoped and subdirectory-scoped changes.
- [ ] 2.4 Implement `has_changes(base_ref, head_ref, paths=None, diff_filter='ACMRTUXB')` and tests for changed and unchanged paths.

## 3. Fetch Refs And Tags

- [ ] 3.1 Implement `fetch_refs(remote='origin', refspecs=None, depth=None, prune=False)` and tests that fetch a missing branch from a local bare remote.
- [ ] 3.2 Implement `fetch_tags(remote='origin', prune=False)` and tests that list tags unavailable before fetch.
- [ ] 3.3 Implement `ensure_ref(ref)` and tests that verify both successful resolution and clear failure for a missing ref.
- [ ] 3.4 Implement `unshallow(remote='origin')` or an equivalent full-history fetch helper and tests for shallow-repository behavior if Dagger fixture support is practical.

## 4. Merge-Base Workflows

- [ ] 4.1 Implement `get_changed_files_since_merge_base(base_ref, head_ref='HEAD', paths=None, diff_filter='ACMRTUXB')` with tests for pull request style branches.
- [ ] 4.2 Implement `get_changed_dirs_since_merge_base(base_ref, head_ref='HEAD', paths=None, depth=1, diff_filter='ACMRTUXB')` with tests for monorepo path scopes.
- [ ] 4.3 Update higher-level pipeline code to use merge-base diff helpers where appropriate and cover the integration with tests.

## 5. Component Discovery For Monorepos And Single-Component Repos

- [ ] 5.1 Implement `get_components(component_roots)` and tests for explicit roots and glob-like component root patterns.
- [ ] 5.2 Implement `get_changed_components(base_ref, head_ref, component_roots, shared_paths=None, single_component=False)` and tests for changed component roots.
- [ ] 5.3 Add shared-path behavior so a shared path change returns all discovered components, with tests.
- [ ] 5.4 Add single-component behavior that returns `['.']` when matching files changed, with tests.
- [ ] 5.5 Document component discovery examples for monorepos and single-component repositories.

## 6. Tags And Versions

- [ ] 6.1 Implement `get_tags(pattern='*', sort='version')` as the verb-based replacement for `list_tags`, with tests.
- [ ] 6.2 Implement `has_tag(tag)` and tests for existing and missing tags.
- [ ] 6.3 Implement `get_latest_tag(pattern='*', semver=True)` and tests for semver and non-semver tag sets.
- [ ] 6.4 Implement `get_tags_pointing_at(ref='HEAD')` and tests for HEAD and non-HEAD refs.
- [ ] 6.5 Implement `create_tag(tag, message=None, user_name='dagger-ci', user_email='dagger-ci@example.local')` and tests for lightweight and annotated tags.
- [ ] 6.6 Implement `push_tag(tag, remote='origin')` and tests that push to a local bare remote.

## 7. Portable Authentication

- [ ] 7.1 Implement `configure_https_token_auth(host, token, username=None)` using `dagger.Secret`, and tests that verify configuration without exposing the token.
- [ ] 7.2 Implement `configure_ssh_key_auth(private_key, known_hosts, host=None)` using `dagger.Secret`, and tests that verify file permissions and non-disclosure of key material.
- [ ] 7.3 Update tag push and fetch documentation to show generic Git host usage for GitHub, GitLab, and Bitbucket.

## 8. Repository Metadata

- [ ] 8.1 Implement `get_head_sha()` and tests for full SHA output.
- [ ] 8.2 Implement `get_current_branch()` and `get_current_ref()` with tests for branch and detached HEAD states.
- [ ] 8.3 Implement `get_remote_url(remote='origin')` and `get_default_branch(remote='origin')` with tests against a local bare remote.
- [ ] 8.4 Implement `get_status_porcelain()` and `has_clean_worktree()` with tests for clean and dirty worktrees.

## 9. Files At Ref

- [ ] 9.1 Implement `has_file_at_ref(ref, path)` and tests for existing and missing files.
- [ ] 9.2 Implement `get_file_contents_at_ref(ref, path)` and tests for reading a file from a non-HEAD ref.

## 10. Documentation And Integration

- [ ] 10.1 Update `modules/git/README.md` so every documented function exists and every example uses verb-based names.
- [ ] 10.2 Update repository docs and module reference for Git CI use cases.
- [ ] 10.3 Update `modules/pipelines` to use restored Git APIs and add tests for any changed pipeline behavior.
- [ ] 10.4 Remove the legacy `modules/git/tests/test.sh` after the Dagger-native test module is the canonical test path.
- [ ] 10.5 Run `make tests git`, `make lint git`, `make format-check git`, and `openspec validate --all --strict`.
