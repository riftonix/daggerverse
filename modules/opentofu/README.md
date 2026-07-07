# OpenTofu Dagger Module

Containerized OpenTofu/Terraform tooling for Dagger pipelines. This module wraps the OpenTofu (or Terraform-compatible) CLI to run fmt, init and validate checks.

For full repository documentation, see [../../docs/README.md](../../docs/README.md). For module overview and paths, see [../../docs/reference/modules.md](../../docs/reference/modules.md).

## Features
- Reproducible OpenTofu container environment
- Linting through `fmt -recursive -check -diff`
- Initialization and validation steps combined into a single call
- Configurable executor binary (e.g., `tofu` or `terraform`)
- Split runtime image inputs (`image_registry`, `image_repository`, `image_tag`, `user_id`) so callers can pin or mirror the runtime image

## Defaults
- image_registry: `ghcr.io`
- image_repository: `opentofu/opentofu`
- image_tag: `latest`
- user_id: `65532`
- executor: `tofu`
- Sets `TF_CLI_CONFIG_FILE=/src/.tf.rc` inside the container

## API

- create(image_registry, image_repository, image_tag, user_id, executor)
  - Returns a configured Opentofu module instance. The runtime image is built from `image_registry`, `image_repository`, and `image_tag`; `executor` selects the IaC command run inside that image and does not change image identity.

- container() -> dagger.Container
  - Returns a cached container with the configured image and environment.

- lint(source: Directory) -> str
  - Mounts the IaC project directory at `/src` and executes:
    - `<executor> fmt -recursive -check -diff -no-color`
    - `<executor> init`
    - `<executor> validate -no-color`
  - Returns combined stdout from the sequence.

## Migration from `container_image`

Previous versions accepted a combined `container_image` input (default `ghcr.io/opentofu/opentofu:latest`). That input has been removed. Replace it with the split runtime image inputs:

- `container_image="ghcr.io/opentofu/opentofu:latest"` becomes `image_registry="ghcr.io"`, `image_repository="opentofu/opentofu"`, `image_tag="latest"`.
- `executor` is unchanged and still selects the IaC command (`tofu`, `terraform`, or compatible alternatives).

This is a breaking API change. Pin the new module tag when upgrading and update any callers that passed `container_image`. Consumers that cannot migrate immediately should remain on the previous tag.

## Usage (Python SDK)

```python
import asyncio
import dagger
from dagger import dag

async def main():
    async with dagger.Connection(dag) as client:
        project = client.host().directory("./path/to/iac")
        tofu = await dag.opentofu(image_tag="latest")  # pin image_tag and set executor="terraform" when needed
        out = await tofu.lint(source=project)
        print(out)

asyncio.run(main())
```

## Usage (CLI)

Run fmt/init/validate with defaults:

```bash
dagger -m ./modules/opentofu call lint --source=./path/to/iac
```

Pin the runtime image tag for reproducibility:

```bash
dagger -m ./modules/opentofu call \
  --image-tag=1.6.0 \
  lint --source=./path/to/iac
```

Notes:
- Ensure that your IaC directory contains the necessary provider and backend configuration for `init` to succeed.
- You can override `image_tag` (or any other runtime image input) to a version-pinned or mirrored image for reproducibility or offline runs.

## License
See the repository root LICENSE file.
