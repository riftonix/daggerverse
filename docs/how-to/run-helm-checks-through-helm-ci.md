# Run Helm Checks Through Helm CI

Use the `helm-ci` scenario when you want a CI-style wrapper around Helm chart
checks. The scenario composes `modules/helm` for Helm operations and
`modules/git` for changed-directory selection.

CI provider workflows own event triggers, branch selection, path selection, and
publish timing. Pass those decisions into the scenario as explicit inputs.

## Verify One Chart

```bash
dagger -m ./scenarios/helm-ci call helm-verify \
  --source=./modules/helm/tests/charts/ns-configurator
```

The command runs Helm lint and template through the local Helm module dependency.

## Verify Changed Chart Directories

Use `helm-verify-changed-charts` when the repository is a Git checkout and you want to check only changed chart directories under a path:

```bash
dagger -m ./scenarios/helm-ci call helm-verify-changed-charts \
  --source=. \
  --target-branch=master \
  --charts-path=modules/helm/tests/charts
```

The command asks the Git module for changed chart directories, then verifies each returned chart directory. Pull request workflows should use merge-base diff behavior so base-branch drift does not trigger unrelated chart checks.

## Publish A Chart

```bash
REGISTRY_PASSWORD=secret \
dagger -m ./scenarios/helm-ci call helm-publish \
  --source=./modules/helm/tests/charts/ns-configurator \
  --oci-url=registry.example.com/mycharts \
  --version=0.1.0 \
  --app-version=1.0.0 \
  --username=myuser \
  --password=env://REGISTRY_PASSWORD
```

Use real Dagger secrets in CI instead of printing credentials in logs.
