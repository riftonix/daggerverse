# Git Dagger Module

Module to get a list of changed paths/directories in a git repository. Uses a git container and includes untracked files.

For full repository documentation, see [../../docs/README.md](../../docs/README.md). For module overview and paths, see [../../docs/reference/modules.md](../../docs/reference/modules.md).

## Features
- Containerized git
- Changed path detection vs a target branch
- Includes untracked files
- Scope diff to a subdirectory (`diff_path`)
- Local tag listing
- Remote tag fetching
- Tags pointing at `HEAD`
- Short `HEAD` commit SHA lookup
- Merge-base lookup for explicit refs

## Defaults
- image_registry: `docker.io`
- image_repository: `alpine/git`
- image_tag: `2.52.0`
- container_user: `65532`
- source: current directory (`DefaultPath('./')`)

## API

- create(source, image_registry, image_repository, image_tag, container_user)
  - Returns a configured Git instance.

- container() -> dagger.Container
  - Returns a container with git and the mounted repository.

- get_changed_paths(target_branch: str = 'master', diff_path: str = '.') -> list[str]
  - Returns top‑level paths (directories) that changed between `target_branch` and `HEAD`, including untracked.

- get_merge_base(base_ref: str, head_ref: str) -> str
  - Returns the merge-base commit shared by two refs.

- with_fetched_refs(remote: str = 'origin', refspecs: list[str] | None = None, depth: int | None = None, prune: bool = False) -> Git
  - Fetches refs from the remote repository and returns the updated Git instance.

- with_fetched_tags(remote: str = 'origin', prune: bool = False) -> Git
  - Fetches tags from the remote repository and returns the updated Git instance.

- with_unshallow(remote: str = 'origin') -> Git
  - Ensures a shallow repository has full history and returns the updated Git instance.

- ensure_ref(ref: str) -> str
  - Resolves a ref to a SHA or fails with a clear missing-ref error.

- get_components(component_roots: list[str]) -> list[str]
  - Returns discovered component roots in stable sorted order.

- get_changed_components(base_ref: str, head_ref: str, component_roots: list[str], shared_paths: list[str] | None = None, single_component: bool = False) -> list[str]
  - Returns component roots whose files changed between two refs. In single-component mode, returns `["."]` when matching files changed.

- get_tags(pattern: str = '*', sort: str = 'version') -> list[str]
  - Lists tags, optionally filtered by a glob pattern (e.g. `chartname/1.2.3`) and sorted by version by default.

- has_tag(tag: str) -> bool
  - Returns whether an exact tag exists in the repository.

- get_latest_tag(pattern: str = '*', semver: bool = True) -> str
  - Returns the latest matching tag, or an empty string when no tag matches. In semver mode, only semantic version tags are considered.

- get_short_commit_sha(length: int = 8) -> str
  - Returns the short SHA of the current `HEAD` commit.

- get_tags_pointing_at(ref: str = 'HEAD') -> list[str]
  - Returns tags that point at `ref`.

- create_tag(tag: str, message: str | None = None, user_name: str = 'dagger-ci', user_email: str = 'dagger-ci@example.local') -> Git
  - Creates a local lightweight tag when `message` is omitted, or an annotated tag when `message` is provided.

- push_tag(tag: str, remote: str = 'origin') -> Git
  - Pushes a local tag to the selected remote.

- with_https_token_auth(host: str, token: Secret, username: str | None = None) -> Git
  - Configures HTTPS token authentication for Git operations against a host without exposing the token in returned output.

- with_ssh_key_auth(private_key: Secret, known_hosts: Secret, host: str | None = None) -> Git
  - Configures SSH key authentication for Git operations using secret-mounted key material and known hosts data.

## Usage (Python SDK)

```python
import asyncio
import dagger
from dagger import dag
from git import Git

async def main():
    async with dagger.Connection(dag) as client:
        repo = client.host().directory(".")
        git = await Git.create(source=repo)
        changed = await git.get_changed_paths(target_branch="master", diff_path=".")
        print(changed)

asyncio.run(main())
```

## Usage (CLI)

List changed directories:

```bash
dagger -m ./modules/git call get-changed-paths --source=. --target-branch=master --diff-path=.
```

Only changes within `charts/`:

```bash
dagger -m ./modules/git call get-changed-paths --source=. --target-branch=master --diff-path=charts
```

List tags by pattern:

```bash
dagger -m ./modules/git call get-tags --source=. --pattern="mychart/1.2.3"
```

Fetch tags:

```bash
dagger -m ./modules/git call with-fetched-tags --source=. --remote=origin
```

Get tags pointing at HEAD:

```bash
dagger -m ./modules/git call get-tags-pointing-at --source=. --ref=HEAD
```

Get the merge base for two refs:

```bash
dagger -m ./modules/git call get-merge-base --source=. --base-ref=origin/main --head-ref=HEAD
```

## Tag Fetch And Push With Generic Git Hosts

The Git module does not read GitHub, GitLab, or Bitbucket environment variables directly. Pass explicit remotes, refs, tags, hosts, and credentials from the surrounding CI adapter or scenario.

Fetch tags from the configured remote before release checks:

```bash
dagger -m ./modules/git call with-fetched-tags --source=. --remote=origin get-tags
```

Create and push a release tag:

```bash
dagger -m ./modules/git call \
  create-tag --source=. --tag=v1.2.3 --message="Release v1.2.3" \
  push-tag --tag=v1.2.3 --remote=origin
```

### HTTPS Token Auth

Use `with_https_token_auth` for GitHub, GitLab, and Bitbucket HTTPS remotes. The token is passed as a `dagger.Secret`; the module configures Git credential prompting without writing the token to Git config or returned output.

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

Use the same shape for GitLab or Bitbucket by changing only `host` and `username`:

```python
gitlab_git = dag.git(source=repo).with_https_token_auth(
    host="gitlab.com",
    token=gitlab_token,
    username="oauth2",
)

bitbucket_git = dag.git(source=repo).with_https_token_auth(
    host="bitbucket.org",
    token=bitbucket_token,
    username="x-token-auth",
)
```

### SSH Key Auth

Use `with_ssh_key_auth` when the remote uses SSH URLs such as `git@github.com:org/repo.git`, `git@gitlab.com:org/repo.git`, or `git@bitbucket.org:workspace/repo.git`. Pass both the private key and `known_hosts` as `dagger.Secret` values.

Python SDK example:

```python
private_key = dag.set_secret("GIT_SSH_KEY", private_key_value)
known_hosts = dag.set_secret("GIT_KNOWN_HOSTS", known_hosts_value)
git = dag.git(source=repo).with_ssh_key_auth(
    private_key=private_key,
    known_hosts=known_hosts,
    host="git@github.com:org/repo.git",
)
await git.with_fetched_tags(remote="origin").create_tag(
    tag="v1.2.3",
    message="Release v1.2.3",
).push_tag(tag="v1.2.3")
```

## Component Discovery Examples

Use component discovery when CI should run checks only for affected repository parts.

### Monorepo Components

Discover components from explicit roots and glob-like root patterns:

```bash
dagger -m ./modules/git call get-components \
  --source=. \
  --component-roots=services/* \
  --component-roots=packages/*
```

For a repository with `services/api`, `services/web`, and `packages/shared`, the result is sorted:

```text
["packages/shared", "services/api", "services/web"]
```

Get only components changed between two refs:

```bash
dagger -m ./modules/git call get-changed-components \
  --source=. \
  --base-ref=origin/main \
  --head-ref=HEAD \
  --component-roots=services/* \
  --component-roots=packages/*
```

Add shared paths when changes outside component roots should affect every discovered component:

```bash
dagger -m ./modules/git call get-changed-components \
  --source=. \
  --base-ref=origin/main \
  --head-ref=HEAD \
  --component-roots=services/* \
  --component-roots=packages/* \
  --shared-paths=shared \
  --shared-paths=.github/workflows
```

### Single-Component Repositories

Use `single_component` when the repository should be treated as one deployable unit. The module returns `["."]` when files under the configured roots or shared paths changed, and `[]` when they did not.

```bash
dagger -m ./modules/git call get-changed-components \
  --source=. \
  --base-ref=origin/main \
  --head-ref=HEAD \
  --component-roots=. \
  --single-component=true
```

Scope the same single component to source files while still treating CI configuration as shared:

```bash
dagger -m ./modules/git call get-changed-components \
  --source=. \
  --base-ref=origin/main \
  --head-ref=HEAD \
  --component-roots=src \
  --shared-paths=.github/workflows \
  --single-component=true
```

## License
See the repository root LICENSE file.
