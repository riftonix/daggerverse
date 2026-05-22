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

- fetch_tags(remote: str = 'origin', prune: bool = False) -> str
  - Fetches tags from the remote repository.

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
dagger -m ./modules/git call fetch-tags --source=. --remote=origin
```

Get tags pointing at HEAD:

```bash
dagger -m ./modules/git call get-tags-pointing-at --source=. --ref=HEAD
```

Get the merge base for two refs:

```bash
dagger -m ./modules/git call get-merge-base --source=. --base-ref=origin/main --head-ref=HEAD
```

## License
See the repository root LICENSE file.
