# OpenTofu Dagger Module

Containerized OpenTofu/Terraform tooling for Dagger pipelines. This module wraps the OpenTofu (or Terraform-compatible) CLI to run fmt, init and validate checks.

## Features
- Reproducible OpenTofu container environment
- Linting through `fmt -recursive -check -diff`
- Initialization and validation steps combined into a single call
- Configurable executor binary (e.g., `tofu` or `terraform`)

## Defaults
- container_image: `ghcr.io/opentofu/opentofu:latest`
- executor: `tofu`
- Sets `TF_CLI_CONFIG_FILE=/src/.tf.rc` inside the container

## API

- create(container_image, executor)
  - Returns a configured Opentofu module instance.

- container() -> dagger.Container
  - Returns a cached container with the configured image and environment.

- lint(source: Directory) -> str
  - Mounts the IaC project directory at `/src` and executes:
    - `<executor> fmt -recursive -check -diff -no-color`
    - `<executor> init`
    - `<executor> validate -no-color`
  - Returns combined stdout from the sequence.

## Usage (Python SDK)

```python
import asyncio
import dagger
from dagger import dag
from opentofu import Opentofu

async def main():
    async with dagger.Connection(dag) as client:
        project = client.host().directory("./path/to/iac")
        tofu = await Opentofu.create()  # or set executor="terraform"
        out = await tofu.lint(source=project)
        print(out)

asyncio.run(main())
```

Notes:
- Ensure that your IaC directory contains the necessary provider and backend configuration for `init` to succeed.
- You can override `container_image` to a version-pinned image for reproducibility.

## License
See the repository root LICENSE file.
