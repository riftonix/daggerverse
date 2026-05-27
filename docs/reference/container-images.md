# Container Images Scenario Reference

The `container-images` scenario is the ready-to-run container image CI layer.
It composes `modules/docker` internally and exposes scenario-level functions for
verification and publication.

Use `modules/docker` when you need reusable Docker and OCI primitives in your
own scenario. Use `scenarios/container-images` when you want a portable CI entry
point that accepts selected image contexts and destination image references.

## Layering

`modules/docker` provides low-level primitives:

- build one image context
- pass Dockerfile path, target, build args, and platforms
- configure registry authentication
- run smoke checks
- publish built images to OCI references

`scenarios/container-images` provides workflow functions:

- verify one explicit image context
- verify multiple explicit image contexts
- publish one explicit context to one explicit image reference
- publish multiple explicit context/reference pairs

The scenario keeps CI-provider policy outside its implementation. Provider
workflows decide when to run, which contexts changed, how tags map to image
references, and whether publication should happen.

## Scenario Path

```bash
dagger -m ./scenarios/container-images call <function> --source=.
```

## Verify

Verify one image context:

```bash
dagger -m ./scenarios/container-images call verify-image \
  --source=. \
  --context-path=images/api
```

Verify multiple image contexts:

```bash
dagger -m ./scenarios/container-images call verify-images \
  --source=. \
  --context-paths=images/api \
  --context-paths=images/worker
```

## Publish

Publish one image:

```bash
dagger -m ./scenarios/container-images call publish-image \
  --source=. \
  --context-path=images/api \
  --image-ref=ghcr.io/example/api:v1.2.3
```

Publish multiple images with explicit `context_path=image_ref` specs:

```bash
dagger -m ./scenarios/container-images call publish-images \
  --source=. \
  --publish-specs=images/api=ghcr.io/example/api:v1.2.3 \
  --publish-specs=images/worker=ghcr.io/example/worker:v1.2.3
```

Use `--publish-dry-run=true` in default tests or local wiring checks when no
registry reachable by the Dagger engine is available.

## CI Mapping Example

Provider workflows own repository tag policy. For example, a workflow may accept
tags shaped as `docker/<image-name>/<version>` and map them before calling this
scenario:

```sh
tag="${GITHUB_REF_NAME}"

case "$tag" in
  docker/*/*)
    image_name="$(printf '%s\n' "$tag" | cut -d/ -f2)"
    version="$(printf '%s\n' "$tag" | cut -d/ -f3)"
    context_path="docker/${image_name}"
    image_ref="ghcr.io/example/${image_name}:${version}"
    ;;
  *)
    printf 'Unsupported image tag: %s\n' "$tag" >&2
    exit 2
    ;;
esac

dagger -m ./scenarios/container-images call publish-image \
  --source=. \
  --context-path="$context_path" \
  --image-ref="$image_ref" \
  --registry-address=ghcr.io \
  --registry-username="$GITHUB_ACTOR" \
  --registry-password=env:GITHUB_TOKEN
```

The `docker/` prefix, tag parsing, and registry namespace are workflow policy.
They are not hardcoded in the scenario.
