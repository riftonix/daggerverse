# Run Helm Checks Through Helm CI

Use the `helm-ci` scenario when you want a CI-style wrapper around Helm chart
checks. The scenario composes `modules/helm` for Helm operations and
`modules/git` for changed-directory selection.

CI provider workflows own event triggers, branch selection, path selection, and
publish timing. Pass those decisions into the scenario as explicit inputs.

## Verify One Chart

```bash
dagger -m ./scenarios/helm-ci call \
  --helm-image-tag=3.18.6 \
  helm-verify \
  --source=./modules/helm/tests/charts/ns-configurator
```

The command runs Helm lint and template through the local Helm module dependency.

## Verify Changed Chart Components

Use `verify-charts` when the repository is a Git checkout and you want to check only changed chart components under caller-provided component roots:

```bash
dagger -m ./scenarios/helm-ci call \
  --helm-image-tag=3.18.6 \
  --git-image-tag=2.52.0 \
  verify-charts \
  --source=. \
  --base-ref=origin/master \
  --head-ref=HEAD \
  --charts-path='charts/*' \
  --charts-path='libs/*'
```

The command asks the Git module for changed components matching the chart roots, then verifies each returned chart directory. Caller-provided refs and path patterns keep provider event policy outside the scenario.

`helm-verify` and `helm-publish` use Helm runtime image inputs only. Changed-chart
operations also use Git runtime image inputs. Pin both tags in CI when the
workflow must be reproducible or must use mirrored images.

## Publish A Chart

```bash
REGISTRY_PASSWORD=secret \
dagger -m ./scenarios/helm-ci call \
  --helm-image-tag=3.18.6 \
  helm-publish \
  --source=./modules/helm/tests/charts/ns-configurator \
  --oci-url=registry.example.com/mycharts \
  --version=0.1.0 \
  --app-version=1.0.0 \
  --username=myuser \
  --password=env://REGISTRY_PASSWORD
```

Use real Dagger secrets in CI instead of printing credentials in logs.
