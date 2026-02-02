# Pipelines Dagger Module

CI orchestration on top of local `helm` and `git` modules.

## Features
- Helm chart lint + template
- Helm chart publish to OCI
- Run checks only for changed directories (via git module)

## API

- helm_verify(source: Directory, values: File | None = None, release_name: str = 'ci-release') -> str
  - Runs lint + template and returns the combined output.

- helm_publish(source: Directory, oci_url: str, version: str, app_version: str | None = None, username: str | None = None, password: Secret | None = None, insecure: bool | None = False) -> str
  - Packages and pushes a chart. If username/password are provided, performs `helm registry login`.

- helm_verify_changed(source: Directory, target_branch: str = 'master', diff_path: str = '.', values: File | None = None, release_name: str = 'ci-release') -> list[str]
  - Computes changed paths via the git module and runs `helm_verify` for each.

## Usage (CLI)

Verify a single chart:

```bash
dagger -m ./pipelines call helm-verify --source=./helm/tests/charts/ns-configurator
```

Publish a chart:

```bash
REGISTRY_PASSWORD=secret \
dagger -m ./pipelines call helm-publish \
  --source=./helm/tests/charts/ns-configurator \
  --oci-url=registry.example.com/mycharts \
  --version=0.1.0 \
  --app-version=1.0.0 \
  --password=env://REGISTRY_PASSWORD \
  --username=myuser
```

Verify only changed directories:

```bash
dagger -m ./pipelines call helm-verify-changed \
  --source=. \
  --target-branch=master \
  --diff-path=helm/tests/charts
```

## License
See the repository root LICENSE file.
