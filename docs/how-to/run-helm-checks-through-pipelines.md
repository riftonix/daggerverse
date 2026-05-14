# Run Helm Checks Through Pipelines

Use the `pipelines` module when you want a CI-style wrapper around Helm checks.

## Verify One Chart

```bash
dagger -m ./modules/pipelines call helm-verify --source=./modules/helm/tests/charts/ns-configurator
```

The command runs Helm lint and template through the local Helm module dependency.

## Verify Changed Chart Directories

Use `helm-verify-changed` when the repository is a Git checkout and you want to check only changed directories under a path:

```bash
dagger -m ./modules/pipelines call helm-verify-changed \
  --source=. \
  --target-branch=master \
  --diff-path=modules/helm/tests/charts
```

The command asks the Git module for changed top-level paths inside `diff-path`, then verifies each returned chart directory.

## Publish A Chart

```bash
REGISTRY_PASSWORD=secret \
dagger -m ./modules/pipelines call helm-publish \
  --source=./modules/helm/tests/charts/ns-configurator \
  --oci-url=registry.example.com/mycharts \
  --version=0.1.0 \
  --app-version=1.0.0 \
  --username=myuser \
  --password=env://REGISTRY_PASSWORD
```

Use real Dagger secrets in CI instead of printing credentials in logs.
