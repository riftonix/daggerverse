# Docker Module Reference

The Docker module exposes reusable Docker and OCI image primitives for CI workflows. It uses Dagger-native container build and publish APIs, so callers do not need a Docker daemon and provider-specific CI policy stays outside the module.

## Module Path

```bash
dagger -m ./modules/docker call <function> --source=.
```

Defaults:

- `source`: current directory
- `context_path`: `.`
- `dockerfile_path`: `Dockerfile`
- `target`: empty
- `build_args`: none
- `platforms`: current/default platform
- `bake_path`: `docker-bake.json`
- `variable_overrides`: none

## Core Objects

- `Docker`
- `DockerBuild`
- `DockerImage`

`Docker.build(...)` returns a `DockerBuild`. `DockerBuild.publish(...)` returns a `DockerImage`.

## Build

- `build(source, context_path='.', dockerfile_path='Dockerfile', target=None, build_args=None, platforms=None, tags=None, labels=None) -> DockerBuild`
- `DockerBuild.container() -> dagger.Container`
- `DockerBuild.context_path() -> str`
- `DockerBuild.dockerfile_path() -> str`
- `DockerBuild.target() -> str`
- `DockerBuild.build_args() -> list[str]`

Build an image from a context:

```bash
dagger -m ./modules/docker call build \
  --source=. \
  --context-path=modules/docker/tests/fixtures/basic-image \
  container
```

Build with a Dockerfile path, target, and build argument:

```bash
dagger -m ./modules/docker call build \
  --source=. \
  --context-path=modules/docker/tests/fixtures/basic-image \
  --dockerfile-path=Dockerfile \
  --target=runtime \
  --build-args=MESSAGE=hello=dagger \
  build-args
```

Build arguments use `KEY=VALUE` strings. The key must be non-empty and the `=` separator is required. Values may contain additional `=` characters.

Python SDK example:

```python
build = dag.docker().build(
    source=repo,
    context_path="docker/app",
    dockerfile_path="Dockerfile",
    target="runtime",
    build_args=["VERSION=1.2.3", "MESSAGE=hello=dagger"],
)
container = build.container()
```

## Docker Buildx Bake

- `build_from_bake(source, target, bake_path='docker-bake.json', variable_overrides=None) -> DockerBuild`
- `DockerBuild.image_refs() -> list[str]`
- `DockerBuild.tags() -> list[str]`
- `DockerBuild.labels() -> list[str]`

`build_from_bake` loads a JSON Docker Buildx Bake manifest and translates one target into Dagger-native build calls. The target may be omitted when the manifest contains exactly one target. It does not invoke the Docker CLI or require a Docker socket.

Supported target fields:

- `context`
- `dockerfile`
- `target`
- `args`
- `tags`
- `labels`
- `platforms`

Each Bake target must define at least one non-empty tag. Unsupported target fields fail explicitly instead of being ignored.

Bake variables use JSON objects with `default` values:

```json
{
  "variable": {
    "REGISTRY": {
      "default": "ghcr.io/my-org"
    },
    "VERSION": {
      "default": "1.2.3"
    }
  },
  "target": {
    "app": {
      "context": "docker/app",
      "dockerfile": "Dockerfile",
      "args": {
        "VERSION": "${VERSION}"
      },
      "tags": [
        "${REGISTRY}/app:${VERSION}"
      ],
      "labels": {
        "org.opencontainers.image.version": "${VERSION}"
      },
      "platforms": [
        "linux/amd64",
        "linux/arm64"
      ]
    }
  }
}
```

Build from the manifest:

```bash
dagger -m ./modules/docker call build-from-bake \
  --source=. \
  --bake-path=docker/app/docker-bake.json \
  image-refs
```

Pass `--target=app` when the manifest contains multiple targets.

Override variables without editing the manifest:

```bash
dagger -m ./modules/docker call build-from-bake \
  --source=. \
  --bake-path=docker/app/docker-bake.json \
  --target=app \
  --variable-overrides=REGISTRY=registry.example.local/team \
  image-refs
```

Python SDK example:

```python
build = dag.docker().build_from_bake(
    source=repo,
    bake_path="docker/app/docker-bake.json",
    target="app",
    variable_overrides=["REGISTRY=registry.example.local/team"],
)
image_refs = await build.image_refs()
```

Interpolation supports `${VAR}` placeholders in `context`, `dockerfile`, `target`, `args`, `tags`, `labels`, and `platforms`. Other interpolation forms and unresolved placeholders fail with a clear error.

Explicit `build(...)` calls return empty lists from `image_refs()` and `tags()`. Bake-derived builds return their resolved Bake tags from both accessors.

Bake resolution fails explicitly when:

- the Bake file does not exist
- the requested target does not exist
- the target has no non-empty tags
- the target uses unsupported fields
- a supported field contains unsupported or unresolved interpolation

## Platforms

- `DockerBuild.platforms() -> list[dagger.Platform]`
- `DockerBuild.platform_variants() -> list[dagger.Container]`

Pass target platforms when the caller needs explicit architecture variants:

```python
build = dag.docker().build(
    source=repo,
    context_path="docker/app",
    platforms=[
        dagger.Platform("linux/amd64"),
        dagger.Platform("linux/arm64"),
    ],
)
```

The build result retains platform variants so `publish` can push them as a platform-aware image.

## Smoke Checks

- `DockerBuild.with_smoke_check(command) -> DockerBuild`

Smoke checks run a caller-provided command in the built image. A failing command fails the Dagger call.

```python
build = dag.docker().build(
    source=repo,
    context_path="docker/app",
).with_smoke_check(["/bin/sh", "-c", "my-app --version"])
```

For platform builds, the smoke command runs against the retained platform variants.

## Registry Auth

- `Docker.with_registry_auth(address, username, password) -> Docker`
- `Docker.registry_auth_addresses() -> list[str]`

Configure registry credentials before build or publish operations that need authenticated registry access. Address and username must be non-empty. The password is a `dagger.Secret` and is not exposed through returned values.

```python
docker = dag.docker().with_registry_auth(
    address="ghcr.io",
    username="my-org",
    password=dag.set_secret("GHCR_TOKEN", token),
)
```

`registry_auth_addresses()` returns only configured registry addresses, which lets tests verify configuration without exposing secret values.

## Publish

- `DockerBuild.publish(image_refs=None) -> DockerImage`
- `DockerBuild.with_publish_dry_run() -> DockerBuild`
- `DockerImage.image_ref() -> str`
- `DockerImage.image_refs() -> list[str]`

Publish sends the built image to one or more OCI image references through Dagger-native `Container.publish`. Explicit builds pass references with `image_refs`. Bake-derived builds can omit the argument and publish their resolved Bake tags:

```python
image = dag.docker().with_registry_auth(
    address="ghcr.io",
    username="my-org",
    password=dag.set_secret("GHCR_TOKEN", token),
).build(
    source=repo,
    context_path="docker/app",
    platforms=[dagger.Platform("linux/amd64"), dagger.Platform("linux/arm64")],
).publish(image_refs=[
    "ghcr.io/my-org/app:1.2.3",
    "ghcr.io/my-org/app:latest",
])

published_ref = await image.image_ref()
all_refs = await image.image_refs()
```

Dry-run publish validates input and returns the same `DockerImage` shape without calling `Container.publish`:

```python
image = dag.docker().build(
    source=repo,
    context_path="docker/app",
).with_publish_dry_run().publish(image_refs=[
    "registry.example.local/app:latest",
])
```

Bake dry-run publish:

```python
image = dag.docker().build_from_bake(
    source=repo,
    bake_path="docker/app/docker-bake.json",
    target="app",
).with_publish_dry_run().publish()
```

Use dry-run mode for default unit-style Dagger tests. Real publication requires a registry reachable by the Dagger engine itself. A Dagger service binding inside a test container is not enough for `Container.publish`, because publish is resolved by the engine.

## Test Model

The Docker module has a neighboring Dagger test module under `modules/docker/tests`.

```bash
make tests module docker
```

The default tests cover explicit builds, Bake target loading and interpolation, Bake validation failures, image reference accessors, registry auth validation, explicit platforms, smoke checks, and dry-run publish wiring. They intentionally avoid requiring external registry credentials or an ephemeral in-Dagger registry for real `Container.publish` calls.
