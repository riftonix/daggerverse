# Pipelines Dagger Module

CI orchestration on top of local `helm` and `git` modules.

## Features
- Helm chart lint + template
- Helm chart publish to OCI
- Run checks only for changed directories (via git module)
- Verify/publish changed charts from charts/libs directories
- Optional feature version publishing (1.2.3+<commit>)
- Release publishing with git tag push

## API

- helm_verify(source: Directory, values: File | None = None, release_name: str = 'ci-release') -> str
  - Runs lint + template and returns the combined output.

- helm_publish(source: Directory, oci_url: str, version: str, app_version: str | None = None, username: str | None = None, password: Secret | None = None, insecure: bool | None = False) -> str
  - Packages and pushes a chart. If username/password are provided, performs `helm registry login`.

- helm_verify_changed(source: Directory, target_branch: str = 'master', diff_path: str = '.', values: File | None = None, release_name: str = 'ci-release') -> list[str]
  - Computes changed paths via the git module and runs `helm_verify` for each.

- helm_verify_changed_charts(source: Directory, target_branch: str = 'master', charts_path: str = 'charts', libs_path: str = 'libs', values: File | None = None, release_name: str = 'ci-release', feature_publish: bool = False, feature_oci_url: str | None = None, username: str | None = None, password: Secret | None = None, insecure: bool = False) -> list[str]
  - Verifies changed charts and libraries (Chart.yaml present). If `feature_publish` is true, publishes `version+<shortsha>` to `feature_oci_url` only when that version is missing in OCI.

- helm_publish_release_changed_charts(source: Directory, values: File | None = None, release_name: str = 'ci-release', release_oci_url: str, username: str | None = None, password: Secret | None = None, insecure: bool = False, tag_prefixes: list[str] | None = None) -> list[str]
  - Publishes release versions based on tags pointing at `HEAD`. Tags must look like `charts/<name>/<version>` or `libs/<name>/<version>`. If the version already exists in OCI, publish is skipped (idempotent).

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

Verify changed charts/libs and optionally publish feature builds:

```bash
REGISTRY_PASSWORD=secret \
dagger -m ./pipelines call helm-verify-changed-charts \
  --source=. \
  --target-branch=master \
  --charts-path=charts \
  --libs-path=libs \
  --feature-publish=true \
  --feature-oci-url=registry.example.com/mycharts \
  --password=env://REGISTRY_PASSWORD \
  --username=myuser
```

Publish release charts by tag:

```bash
REGISTRY_PASSWORD=secret \
dagger -m ./pipelines call helm-publish-release-changed-charts \
  --source=. \
  --release-oci-url=registry.example.com/mycharts \
  --password=env://REGISTRY_PASSWORD \
  --username=myuser
```

## Notes on version checks

Current implementation skips publish when a git tag `chartname/version` already exists. Alternative option is to query OCI registry for existing chart versions (e.g., `helm show chart oci://<registry>/<chart> --version <ver>` or registry API) and skip if found. This avoids reliance on git tags but requires registry credentials and network access in CI. Git tags are faster and deterministic for monorepos; OCI checks are useful if tags are not enforced or if multiple repos publish to the same registry.

## License
See the repository root LICENSE file.
