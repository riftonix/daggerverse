# Helm Dagger Module

Containerized Helm tooling for Dagger pipelines. This module wraps the Helm CLI in a reproducible container, exposing common operations such as dependency update, lint, template, package, and push, with optional OCI registry authentication.

## Features
- Reproducible Helm environment based on `alpine/helm`
- Optional registry login for private OCI registries
- Dependency management (`helm dependency update`)
- Chart linting with strict and quiet modes
- Template rendering with optional values file
- Packaging to a versioned `.tgz`
- Publishing to OCI registries

## Defaults
- image_registry: `docker.io`
- image_repository: `alpine/helm`
- image_tag: `3.18.6`
- container_user: `65532`
- Working directory in container: `/tmp/helm/chart`
- Registry config path: `/tmp/helm/registry/config.json`

## API

All functions are exposed via the Dagger module and return either a configured container, a new module instance (to continue chaining), a string (command output), or a Dagger file artifact.

- create(source, image_registry, image_repository, image_tag, container_user)
  - Returns a configured Helm module instance. `source` must point to a Helm chart directory (must contain `Chart.yaml`).

- container() -> dagger.Container
  - Returns the cached base container with Helm installed and the chart mounted at `/tmp/helm/chart`.

- with_registry_login(username, password: Secret, address='docker.io') -> Self
  - Logs into an OCI registry using `helm registry login`.

- with_dependency_update() -> Self
  - Runs `helm dependency update .` in the chart directory.

- lint(strict: bool = False, errors_only: bool = False) -> str
  - Runs `helm lint .`. If `strict` is true, adds `--strict`. If `errors_only` is true, adds `--quiet`.

- template(values: File | None = None, release_name: str = 'ci-release') -> str
  - Lints (strict) first, then renders templates via `helm template <release_name> .`.
  - If `values` is provided, it is mounted as `values.yaml` and `-f values.yaml` is passed.
  - If the chart `type` is `library`, templating is skipped with a warning (Helm cannot template library charts).

- package(app_version: str = '', version: str = '') -> dagger.File
  - Packages the chart to a `.tgz` in `/tmp/helm/` and returns the file artifact.
  - Optional `--app-version` and `--version` flags are supported.

- push(oci_url: str, version: str = '', insecure: bool = False, app_version: str = '') -> str
  - Packages the chart and pushes it to `oci://<oci_url>` using `helm push`.
  - If `insecure` is true, `--plain-http` is used.

## Usage (Python SDK)

Example: lint, template, package and push a chart.

```python
import asyncio
import dagger
from dagger import dag
from helm import Helm

async def main():
    async with dagger.Connection(dag) as client:
        chart_dir = client.host().directory("./helm/tests/charts/ns-configurator")

        helm = await Helm.create(source=chart_dir)

        # Optional: authenticate to registry
        # secret = client.set_secret("REGISTRY_PASSWORD", "<password>")
        # helm = helm.with_registry_login(username="<user>", password=secret, address="registry.example.com")

        # Update dependencies
        helm = helm.with_dependency_update()

        # Lint
        lint_out = await helm.lint(strict=True)
        print(lint_out)

        # Template (optionally pass values file)
        rendered = await helm.template(release_name="ci-release")
        print(rendered)

        # Package and push
        artifact = await helm.package(app_version="1.0.0", version="0.1.0")
        # Optionally push to OCI
        # out = await helm.push(oci_url="registry.example.com/mycharts", version="0.1.0", app_version="1.0.0")
        # print(out)

asyncio.run(main())
```

## Usage (CLI)

Lint chart:

```bash
dagger -m ./helm call lint --source=./charts/mychart --strict=true
```

Render templates:

```bash
dagger -m ./helm call template --source=./charts/mychart --release-name=ci-release
```

Package chart:

```bash
dagger -m ./helm call package --source=./charts/mychart --version=0.1.0 --app-version=1.0.0
```

Push to OCI (with registry credentials):

```bash
REGISTRY_PASSWORD=secret \
dagger -m ./helm call push \
  --source=./charts/mychart \
  --oci-url=registry.example.com/mycharts \
  --version=0.1.0 \
  --app-version=1.0.0 \
  --insecure=false \
  --password=env://REGISTRY_PASSWORD \
  --username=myuser
```

Notes:
- The module sets and uses `HELM_CHART_PATH=/tmp/helm/chart` and `HELM_REGISTRY_CONFIG=/tmp/helm/registry/config.json` inside the container.
- When passing a values file to `template`, it is mounted as `values.yaml` and the command line includes `-f values.yaml`.
- Templating is skipped for charts with `type: library` in `Chart.yaml`.

## Development
- Requires Dagger engine/runtime available (Docker, etc.).
- Python SDK: `pip install dagger-io`

## License
See the repository root LICENSE file.
