# Container Images Scenario

Portable container image verification and publication scenario for CI workflows. The scenario composes the reusable Docker module while keeping CI-provider trigger policy, changed path selection, tag parsing, and image reference mapping outside the scenario.

## Usage

The scenario expects callers to select explicit image contexts or Bake targets.
CI workflows, local scripts, or higher-level scenarios decide which inputs are
in scope and which registry overrides should be used before calling this
scenario.

### Verify One Image

Build one explicit image context:

```bash
dagger -m ./scenarios/container-images call verify-image \
  --source=. \
  --context-path=images/api \
  --dockerfile-path=Dockerfile \
  --target=runtime \
  --build-args=APP_ENV=ci \
  --platforms=linux/amd64 \
  --smoke-command=app \
  --smoke-command=--version
```

### Verify Multiple Images

Pass each selected context path explicitly:

```bash
dagger -m ./scenarios/container-images call verify-images \
  --source=. \
  --context-paths=images/api \
  --context-paths=images/worker \
  --dockerfile-path=Dockerfile \
  --target=runtime \
  --build-args=APP_ENV=ci \
  --platforms=linux/amd64 \
  --smoke-command=app \
  --smoke-command=--version
```

### Verify One Bake Target

Build a target from a JSON Docker Buildx Bake manifest without publishing:

```bash
dagger -m ./scenarios/container-images call verify-bake-target \
  --source=. \
  --bake-path=images/api/docker-bake.json \
  --variable-overrides=REGISTRY_PREFIX=registry.example.local/team \
  --smoke-command=app \
  --smoke-command=--version
```

Pass `--bake-target=api` when the manifest contains multiple targets.

### Publish One Image

Publish a built image to the caller-provided OCI image reference:

```bash
dagger -m ./scenarios/container-images call \
  with-registry-auth \
    --address=ghcr.io \
    --username="$GITHUB_ACTOR" \
    --password=env:GITHUB_TOKEN \
  publish-image \
    --source=. \
    --context-path=images/api \
    --image-ref=ghcr.io/example/api:v1.2.3 \
    --dockerfile-path=Dockerfile \
    --target=runtime \
    --build-args=APP_ENV=production \
    --platforms=linux/amd64 \
    --publish-dry-run=false
```

Repeat `with-registry-auth` before publication when multiple private registries
require credentials.

### Publish Multiple Images

Pass publish specs in `context_path=image_ref` form:

```bash
dagger -m ./scenarios/container-images call \
  with-registry-auth \
    --address=ghcr.io \
    --username="$GITHUB_ACTOR" \
    --password=env:GITHUB_TOKEN \
  publish-images \
    --source=. \
    --publish-specs=images/api=ghcr.io/example/api:v1.2.3 \
    --publish-specs=images/worker=ghcr.io/example/worker:v1.2.3 \
    --dockerfile-path=Dockerfile \
    --target=runtime \
    --build-args=APP_ENV=production \
    --platforms=linux/amd64 \
    --publish-dry-run=false
```

### Publish One Bake Target

Publish the image references resolved from a JSON Docker Buildx Bake manifest:

```bash
dagger -m ./scenarios/container-images call \
  with-registry-auth \
    --address=ghcr.io \
    --username="$GITHUB_ACTOR" \
    --password=env:GITHUB_TOKEN \
  publish-bake-target \
    --source=. \
    --bake-path=images/api/docker-bake.json \
    --variable-overrides=REGISTRY_PREFIX=ghcr.io/example \
    --publish-dry-run=false
```

Pass `--bake-target=api` when the manifest contains multiple targets.

For local or default tests, change `--publish-dry-run=false` to `true` to
validate publish wiring without pushing to a registry.

See [Container images scenario reference](../../docs/reference/container-images.md#parameters)
for the meaning of every parameter.

## CI Boundary

Provider workflows own event rules, changed path selection, tag parsing, and
target selection. This scenario verifies or publishes the explicit contexts or
Bake targets it receives.

## Local Paths

- Scenario source: `src/container_images/`
- Dagger test module: `tests/`
- Public facade: `src/container_images/main.py`

## License

See the repository root LICENSE file.
