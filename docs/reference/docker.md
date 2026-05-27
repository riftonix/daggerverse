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

## Core Objects

- `Docker`
- `DockerBuild`
- `DockerImage`

`Docker.build(...)` returns a `DockerBuild`. `DockerBuild.publish(...)` returns a `DockerImage`.

## Build

- `build(source, context_path='.', dockerfile_path='Dockerfile', target=None, build_args=None, platforms=None) -> DockerBuild`
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

Configure registry credentials before build or publish operations that need authenticated registry access. The password is a `dagger.Secret` and is not exposed through returned values.

```python
docker = dag.docker().with_registry_auth(
    address="ghcr.io",
    username="my-org",
    password=dag.set_secret("GHCR_TOKEN", token),
)
```

`registry_auth_addresses()` returns only configured registry addresses, which lets tests verify configuration without exposing secret values.

## Publish

- `DockerBuild.publish(image_refs) -> DockerImage`
- `DockerBuild.with_publish_dry_run() -> DockerBuild`
- `DockerImage.image_ref() -> str`
- `DockerImage.image_refs() -> list[str]`

Publish sends the built image to one or more caller-provided OCI image references through Dagger-native `Container.publish`:

```python
image = dag.docker().with_registry_auth(
    address="ghcr.io",
    username="my-org",
    password=dag.set_secret("GHCR_TOKEN", token),
).build(
    source=repo,
    context_path="docker/app",
    platforms=[dagger.Platform("linux/amd64"), dagger.Platform("linux/arm64")],
).publish([
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
).with_publish_dry_run().publish([
    "registry.example.local/app:latest",
])
```

Use dry-run mode for default unit-style Dagger tests. Real publication requires a registry reachable by the Dagger engine itself. A Dagger service binding inside a test container is not enough for `Container.publish`, because publish is resolved by the engine.

## Test Model

The Docker module has a neighboring Dagger test module under `modules/docker/tests`.

```bash
make tests module docker
```

The default tests cover build construction, build options, build argument validation, explicit platforms, smoke checks, registry auth configuration, dry-run publish wiring, and image result accessors. They intentionally avoid requiring external registry credentials or an ephemeral in-Dagger registry for real `Container.publish` calls.
