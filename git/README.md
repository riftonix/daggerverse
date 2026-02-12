# Git Dagger Module

Module to get a list of changed paths/directories in a git repository. Uses a git container and includes untracked files.

## Features
- Containerized git
- Changed path detection vs a target branch
- Includes untracked files
- Scope diff to a subdirectory (`diff_path`)

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

- fetch_tags(remote: str = 'origin', prune: bool = False) -> str
  - Fetches tags from the remote repository.

- list_tags(pattern: str | None = None) -> list[str]
  - Lists tags, optionally filtered by a glob pattern (e.g. `chartname/1.2.3`).

- get_short_commit_sha(length: int = 7) -> str
  - Returns the short SHA of the current `HEAD` commit.

- create_and_push_tag(tag: str, message: str | None = None, remote: str = 'origin', user_name: str = 'dagger-ci', user_email: str = 'dagger-ci@example.local') -> str
  - Creates a lightweight tag (or annotated if `message` provided) and pushes it to the remote.

- get_tags_pointing_at_head() -> list[str]
  - Returns tags that point at `HEAD` (useful for tag-triggered pipelines).

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
dagger -m ./git call get-changed-paths --source=. --target-branch=master --diff-path=.
```

Only changes within `charts/`:

```bash
dagger -m ./git call get-changed-paths --source=. --target-branch=master --diff-path=charts
```

List tags by pattern:

```bash
dagger -m ./git call list-tags --source=. --pattern="mychart/1.2.3"
```

Create and push a release tag:

```bash
dagger -m ./git call create-and-push-tag --source=. --tag="mychart/1.2.3" --remote=origin
```

Get tags pointing at HEAD:

```bash
dagger -m ./git call get-tags-pointing-at-head --source=.
```

## License
See the repository root LICENSE file.
