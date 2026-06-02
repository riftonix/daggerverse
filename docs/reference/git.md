# Git Module Reference

The Git module exposes provider-neutral Git primitives for CI workflows. Callers pass explicit refs, SHAs, paths, remotes, and credentials; provider-specific event parsing belongs in scenarios or CI adapters.

## Module Path

```bash
dagger -m ./modules/git call <function> --source=.
```

Defaults:

- `image_registry`: `docker.io`
- `image_repository`: `alpine/git`
- `image_tag`: `2.52.0`
- `user_id`: `65532`
- `source`: current directory

## Core Functions

- `container() -> dagger.Container`
- `get_changed_paths(target_branch='master', diff_path='.') -> list[str]`
- `get_merge_base(base_ref, head_ref) -> str`
- `ensure_ref(ref) -> str`

## Fetch And History

- `with_fetched_refs(remote='origin', refspecs=None, depth=None, prune=False) -> Git`
- `with_fetched_tags(remote='origin', prune=False) -> Git`
- `with_unshallow(remote='origin') -> Git`

Chain `with_*` functions before follow-up calls that need the updated Git state:

```bash
dagger -m ./modules/git call \
  with-fetched-tags --source=. --remote=origin \
  get-tags
```

## Diff Functions

- `get_changed_files(base_ref, head_ref, paths=None, diff_filter='ACMRTUXB') -> list[str]`
- `get_changed_dirs(base_ref, head_ref, paths=None, depth=1, diff_filter='ACMRTUXB') -> list[str]`
- `has_changes(base_ref, head_ref, paths=None, diff_filter='ACMRTUXB') -> bool`
- `get_changed_files_since_merge_base(base_ref, head_ref='HEAD', paths=None, diff_filter='ACMRTUXB') -> list[str]`
- `get_changed_dirs_since_merge_base(base_ref, head_ref='HEAD', paths=None, depth=1, diff_filter='ACMRTUXB') -> list[str]`

Example:

```bash
dagger -m ./modules/git call get-changed-dirs \
  --source=. \
  --base-ref=origin/main \
  --head-ref=HEAD \
  --depth=2
```

### Pull Request Diff

Use merge-base helpers for pull request checks. They ignore unrelated drift on the base branch and return the changes introduced by the head ref:

```bash
dagger -m ./modules/git call get-changed-files-since-merge-base \
  --source=. \
  --base-ref=origin/main \
  --head-ref=HEAD
```

Scope the same check to a path when only part of the repository should gate a job:

```bash
dagger -m ./modules/git call has-changes \
  --source=. \
  --base-ref=origin/main \
  --head-ref=HEAD \
  --paths=modules/git
```

For shallow CI checkouts, fetch the refs needed by the diff before computing changes:

```bash
dagger -m ./modules/git call \
  with-fetched-refs --source=. --remote=origin \
    --refspecs=refs/heads/main:refs/remotes/origin/main \
  get-changed-files-since-merge-base --base-ref=origin/main --head-ref=HEAD
```

## Components

- `get_components(component_roots) -> list[str]`
- `get_changed_components(base_ref, head_ref, component_roots, shared_paths=None, single_component=False) -> list[str]`

Monorepo example:

```bash
dagger -m ./modules/git call get-changed-components \
  --source=. \
  --base-ref=origin/main \
  --head-ref=HEAD \
  --component-roots=services/* \
  --component-roots=packages/* \
  --shared-paths=.github/workflows
```

Single-component repository example:

```bash
dagger -m ./modules/git call get-changed-components \
  --source=. \
  --base-ref=origin/main \
  --head-ref=HEAD \
  --component-roots=. \
  --single-component=true
```

Use changed components to build a CI matrix outside the Git module. The module returns component roots; the surrounding scenario or workflow decides which checks to run for each returned root.

## Tags

- `get_tags(pattern='*', sort='version') -> list[str]`
- `has_tag(tag) -> bool`
- `get_latest_tag(pattern='*', semver=True) -> str`
- `get_tags_pointing_at(ref='HEAD') -> list[str]`
- `ensure_pushed_tag(tag, remote='origin') -> str`
- `create_tag(tag, message=None, user_name='dagger-ci', user_email='dagger-ci@example.local') -> Git`
- `push_tag(tag, remote='origin') -> Git`

Create and push a release tag:

```bash
dagger -m ./modules/git call \
  create-tag --source=. --tag=v1.2.3 --message="Release v1.2.3" \
  push-tag --tag=v1.2.3 --remote=origin
```

Idempotently create and push a lightweight release tag when it is missing:

```bash
dagger -m ./modules/git call ensure-pushed-tag \
  --source=. \
  --tag=v1.2.3 \
  --remote=origin
```

`ensure-pushed-tag` fetches remote tags first. It returns the requested tag
without pushing when the tag already exists, otherwise it creates the tag on
`HEAD`, pushes it, and returns the tag name.

### Release Checks

Fetch tags before release checks in shallow or minimal CI clones:

```bash
dagger -m ./modules/git call \
  with-fetched-tags --source=. --remote=origin \
  get-latest-tag --pattern='v*'
```

Check whether the current commit already has a release tag:

```bash
dagger -m ./modules/git call get-tags-pointing-at \
  --source=. \
  --ref=HEAD
```

## Repository Metadata

- `get_head_sha() -> str`
- `get_short_commit_sha(length=8) -> str`
- `get_current_branch() -> str`
- `get_current_ref() -> str`
- `get_remote_url(remote='origin') -> str`
- `get_default_branch(remote='origin') -> str`
- `get_status_porcelain() -> str`
- `has_clean_worktree() -> bool`

Use metadata helpers for CI labels, cache keys, release names, and guard checks:

```bash
dagger -m ./modules/git call get-short-commit-sha --source=. --length=12
dagger -m ./modules/git call get-default-branch --source=. --remote=origin
dagger -m ./modules/git call has-clean-worktree --source=.
```

## Files At Ref

- `has_file_at_ref(ref, path) -> bool`
- `get_file_contents_at_ref(ref, path) -> str`

Example:

```bash
dagger -m ./modules/git call get-file-contents-at-ref \
  --source=. \
  --ref=origin/main \
  --path=README.md
```

Use files-at-ref helpers when a CI decision depends on repository configuration from a specific branch or tag, such as whether a component manifest exists on the default branch.

## Authentication

- `with_https_token_auth(host, token, username=None) -> Git`
- `with_ssh_key_auth(private_key, known_hosts, host=None) -> Git`

Use HTTPS token authentication for GitHub, GitLab, and Bitbucket HTTPS remotes. Pass the token as a `dagger.Secret`; the module configures Git credential prompting without returning the token in output.

Common host and username values:

```text
GitHub:    host=github.com        username=x-access-token
GitLab:    host=gitlab.com        username=oauth2
Bitbucket: host=bitbucket.org     username=x-token-auth
```

Python SDK example:

```python
token = dag.set_secret("GIT_TOKEN", token_value)
git = dag.git(source=repo).with_https_token_auth(
    host="github.com",
    token=token,
    username="x-access-token",
)
await git.with_fetched_tags(remote="origin").create_tag(
    tag="v1.2.3",
    message="Release v1.2.3",
).push_tag(tag="v1.2.3")
```

Use SSH key authentication for SSH remotes. Pass both the private key and `known_hosts` as `dagger.Secret` values.

```python
private_key = dag.set_secret("GIT_SSH_KEY", private_key_value)
known_hosts = dag.set_secret("GIT_KNOWN_HOSTS", known_hosts_value)
git = dag.git(source=repo).with_ssh_key_auth(
    private_key=private_key,
    known_hosts=known_hosts,
    host="git@github.com:org/repo.git",
)
```

## CI Provider Integration

Keep provider-specific environment parsing outside the Git module. Translate CI variables into explicit refs, remotes, paths, and secrets before calling the module.

Typical inputs from a GitHub pull request job:

- `base_ref`: `origin/main` after fetching the base branch
- `head_ref`: `HEAD`
- `remote`: `origin`
- token secret: GitHub token passed to `with_https_token_auth`

GitLab and Bitbucket adapters should produce the same shape: an explicit base ref, head ref, remote name, and optional credentials. The Git module should not need to know which provider supplied those values.
