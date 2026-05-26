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

- get_tags(pattern: str | None = None) -> list[str]
  - Lists tags, optionally filtered by a glob pattern (e.g. `chartname/1.2.3`).

- get_short_commit_sha(length: int = 8) -> str
  - Returns the short SHA of the current `HEAD` commit.

- get_tags_pointing_at(ref: str = 'HEAD', remote: str = 'origin') -> list[str]
  - Fetches tags and returns tags that point at `ref`.

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
