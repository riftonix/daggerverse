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
- build one JSON Docker Buildx Bake target
- pass Dockerfile path, target, build args, and platforms
- configure registry authentication
- run smoke checks
- publish built images to OCI references

`scenarios/container-images` provides workflow functions:

- verify one explicit image context
- verify multiple explicit image contexts
- verify one JSON Docker Buildx Bake target
- configure one or more registry authentications for later publication
- publish one explicit context to one explicit image reference
- publish multiple explicit context/reference pairs
- publish one JSON Docker Buildx Bake target to its resolved image references

The scenario keeps CI-provider policy outside its implementation. Provider
workflows decide when to run, which contexts changed, how tags map to image
references, and whether publication should happen.

## Scenario Path

```bash
dagger -m ./scenarios/container-images call <function> --source=.
```

## Verify

Verify one explicit image context:

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

Verify multiple image contexts:

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

Verify one Bake target:

```bash
dagger -m ./scenarios/container-images call verify-bake-target \
  --source=. \
  --bake-path=images/api/docker-bake.json \
  --bake-target=api \
  --variable-overrides=REGISTRY_PREFIX=registry.example.local/team \
  --smoke-command=app \
  --smoke-command=--version
```

Verification builds the selected image without publishing it. See
[Parameters](#parameters) for the distinction between `--target` and
`--bake-target`.

## Publish

Configure registry credentials before a publication call. Repeat
`with-registry-auth` when publishing to multiple private registries. Passwords
remain Dagger secrets and are not exposed by scenario results.

Publish one explicit image:

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

Publish multiple images with explicit `context_path=image_ref` specs:

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

Publish one Bake target to the references resolved from its manifest:

```bash
dagger -m ./scenarios/container-images call \
  with-registry-auth \
    --address=ghcr.io \
    --username="$GITHUB_ACTOR" \
    --password=env:GITHUB_TOKEN \
  publish-bake-target \
    --source=. \
    --bake-path=images/api/docker-bake.json \
    --bake-target=api \
    --variable-overrides=REGISTRY_PREFIX=ghcr.io/example \
    --publish-dry-run=false
```

`publish-bake-target` accepts optional `--variable-overrides=KEY=VALUE` values.
Use them to override values such as the registry prefix without editing the
manifest. The function returns all image references published for the target.

Use `--publish-dry-run=true` in default tests or local wiring checks when no
registry reachable by the Dagger engine is available.

## Parameters

Common source parameter:

- `--source`: directory visible to the scenario. Paths passed to the same call are relative to this directory. Default: `.`.

Explicit image build parameters:

- `--context-path`: Docker build context relative to `--source`.
- `--dockerfile-path`: Dockerfile path relative to the context. Default: `Dockerfile`.
- `--target`: optional Dockerfile stage for a multi-stage explicit build.
- `--build-args=KEY=VALUE`: optional Docker build argument. Repeat for multiple arguments.
- `--platforms`: optional target platform such as `linux/amd64`. Repeat for multiple platforms.

Bake target parameters:

- `--bake-path`: JSON Docker Buildx Bake file relative to `--source`.
- `--bake-target`: required named target from the Bake manifest. This is not a Dockerfile stage.
- `--variable-overrides=KEY=VALUE`: optional Bake variable override. Repeat for multiple variables.

Verification parameter:

- `--smoke-command`: one command argument to execute in the built image. Repeat to construct the argument vector, for example `--smoke-command=app --smoke-command=--version`.

Publication parameters:

- `--image-ref`: full OCI destination reference for `publish-image`, for example `ghcr.io/example/api:v1.2.3`.
- `--publish-specs=CONTEXT_PATH=IMAGE_REF`: explicit context and destination pair for `publish-images`. Repeat for multiple images.
- `--publish-dry-run`: validate publication wiring and return refs without pushing. Default: `false`.

Registry authentication parameters for chainable `with-registry-auth`:

- `--address`: explicit registry authentication address passed to Dagger unchanged, for example `ghcr.io`, `registry.example.local:5000`, or `gitea.local/registry` when the registry requires a path prefix.
- `--username`: registry username.
- `--password`: registry password or token passed as a Dagger secret, for example `env:GITHUB_TOKEN`.

`publish-bake-target` does not accept `--image-ref`. It publishes every resolved
tag from the selected Bake target. Registry credentials are configured
separately with one or more `with-registry-auth` calls.

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

dagger -m ./scenarios/container-images call \
  with-registry-auth \
    --address=ghcr.io \
    --username="$GITHUB_ACTOR" \
    --password=env:GITHUB_TOKEN \
  publish-image \
    --source=. \
    --context-path="$context_path" \
    --image-ref="$image_ref" \
    --dockerfile-path=Dockerfile \
    --target=runtime \
    --build-args=APP_ENV=production \
    --platforms=linux/amd64 \
    --publish-dry-run=false
```

The `docker/` prefix, tag parsing, Bake target selection, and registry namespace
are workflow policy. They are not hardcoded in the scenario.
