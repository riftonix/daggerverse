# Kind Dagger Module

Provision a container image with the `kind` Kubernetes-in-Docker CLI installed for use in Dagger pipelines.

## Features
- Minimal wrapper that produces a container with `kind` installed
- Pin to a specific base image and `kind` version for reproducibility

## Defaults
- image_registry: `docker.io`
- image_repository: `docker`
- image_tag: `28.5.0-rc.1-dind`
- Installs kind v0.30.0 for linux-amd64 to `/usr/local/bin/kind`

## API

- create(image_registry, image_repository, image_tag, user)
  - Returns a configured Kind module instance.

- container() -> dagger.Container
  - Returns a cached container based on `<registry>/<repository>:<tag>` with `kind` installed.

## Usage (Python SDK)

```python
import asyncio
import dagger
from dagger import dag
from kind import Kind

async def main():
    async with dagger.Connection(dag) as client:
        kind_mod = await Kind.create()
        ctr = kind_mod.container()
        out = await ctr.with_exec(["kind", "version"]).stdout()
        print(out)

asyncio.run(main())
```

## Usage (CLI)

Check installed kind version:

```bash
dagger -m ./kind call container \
  | with-exec --args=kind,version \
  | stdout
```

Notes:
- This module does not create a cluster by itself; it only provides the CLI. You can use `ctr.with_exec([...])` to run `kind create cluster` with appropriate Docker-in-Docker privileges when integrating into a larger pipeline.

## License
See the repository root LICENSE file.
