# Container Images Scenario

Portable container image verification and publication scenario for CI workflows. The scenario composes the reusable Docker module while keeping CI-provider trigger policy, changed path selection, tag parsing, and image reference mapping outside the scenario.

## Usage

The scenario expects callers to provide explicit image inputs. CI workflows,
local scripts, or higher-level scenarios decide which contexts are in scope and
which destination references should be used before calling this scenario.

### Verify One Image

Build one image context from a source directory:

```bash
dagger -m ./scenarios/container-images call verify-image \
  --source=. \
  --context-path=images/api
```

Pass Docker build options explicitly when the image needs them:

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
  --context-paths=images/worker
```

### Publish One Image

Publish a built image to the caller-provided OCI image reference:

```bash
dagger -m ./scenarios/container-images call publish-image \
  --source=. \
  --context-path=images/api \
  --image-ref=ghcr.io/example/api:v1.2.3
```

Use registry authentication when publication needs credentials:

```bash
dagger -m ./scenarios/container-images call publish-image \
  --source=. \
  --context-path=images/api \
  --image-ref=ghcr.io/example/api:v1.2.3 \
  --registry-address=ghcr.io \
  --registry-username="$GITHUB_ACTOR" \
  --registry-password=env:GITHUB_TOKEN
```

### Publish Multiple Images

Pass publish specs in `context_path=image_ref` form:

```bash
dagger -m ./scenarios/container-images call publish-images \
  --source=. \
  --publish-specs=images/api=ghcr.io/example/api:v1.2.3 \
  --publish-specs=images/worker=ghcr.io/example/worker:v1.2.3
```

For local or default tests, `--publish-dry-run=true` validates publish wiring
without pushing to a registry:

```bash
dagger -m ./scenarios/container-images call publish-image \
  --source=. \
  --context-path=images/api \
  --image-ref=registry.example.local/api:latest \
  --publish-dry-run=true
```

## CI Boundary

Provider workflows own event rules, changed path selection, tag parsing, and
tag-to-image-reference mapping. This scenario only verifies or publishes the
explicit `context_path` and `image_ref` values it receives.

## Local Paths

- Scenario source: `src/container_images/`
- Dagger test module: `tests/`
- Public facade: `src/container_images/main.py`

## License

See the repository root LICENSE file.
