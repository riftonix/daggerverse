# Run Helm Checks Through The Transitional Pipeline

Use the current `pipelines` module when you want a CI-style wrapper around Helm checks.

This module is transitional. Treat it as a temporary Helm CI wrapper for a future `scenarios/` entrypoint; final naming and layout should be defined in a separate proposal.

## Verify One Chart

```bash
dagger -m ./modules/pipelines call helm-verify --source=./modules/helm/tests/charts/ns-configurator
```

The command runs Helm lint and template through the local Helm module dependency.

## Verify Changed Chart Directories

Use `helm-verify-changed-charts` when the repository is a Git checkout and you want to check only changed chart directories under a path:

```bash
dagger -m ./modules/pipelines call helm-verify-changed-charts \
  --source=. \
  --target-branch=master \
  --charts-path=modules/helm/tests/charts
```

The command asks the Git module for changed chart directories, then verifies each returned chart directory. Pull request workflows should use merge-base diff behavior so base-branch drift does not trigger unrelated chart checks.

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
