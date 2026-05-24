# Pipelines Dagger Module

CI orchestration on top of local `helm` and `git` modules.

This module is transitional. Treat it as a temporary Helm CI wrapper for a future `scenarios/` entrypoint; final naming and layout should be defined in a separate proposal.

For full repository documentation, see [../../docs/README.md](../../docs/README.md). For pipeline tasks, see [../../docs/how-to/run-helm-checks-through-pipelines.md](../../docs/how-to/run-helm-checks-through-pipelines.md).

## Features
- Helm chart lint + template
- Helm chart publish to OCI
- Run checks only for changed directories (via git module)
- Verify changed charts from charts/libs directories

## API

- helm_verify(source: Directory, values: File | None = None, release_name: str = 'ci-release') -> str
  - Runs lint + template and returns the combined output.

- helm_publish(source: Directory, oci_url: str, version: str, app_version: str | None = None, username: str | None = None, password: Secret | None = None, insecure: bool | None = False) -> str
  - Packages and pushes a chart. If username/password are provided, performs `helm registry login`.

- helm_verify_changed_charts(source: Directory, target_branch: str = 'master', charts_path: str | None = None, libs_path: str | None = None, values: File | None = None, release_name: str = 'ci-release') -> list[str]
  - Computes changed chart directories under `charts_path` and/or `libs_path` since the merge base with `target_branch`, then runs `helm_verify` for each changed chart.

## Usage (CLI)

Verify a single chart:

```bash
dagger -m ./modules/pipelines call helm-verify --source=./modules/helm/tests/charts/ns-configurator
```

Publish a chart:

```bash
REGISTRY_PASSWORD=secret \
dagger -m ./modules/pipelines call helm-publish \
  --source=./modules/helm/tests/charts/ns-configurator \
  --oci-url=registry.example.com/mycharts \
  --version=0.1.0 \
  --app-version=1.0.0 \
  --password=env://REGISTRY_PASSWORD \
  --username=myuser
```

Verify changed chart directories:

```bash
dagger -m ./modules/pipelines call helm-verify-changed-charts \
  --source=. \
  --target-branch=master \
  --charts-path=modules/helm/tests/charts
```

## License
See the repository root LICENSE file.
