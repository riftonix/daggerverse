# Runtime Image Inputs

Runtime image inputs select the container image used to execute a tool inside a
Dagger module or scenario. They are separate from images that a workflow builds,
tags, publishes, or tests as output artifacts.

## Single-Tool Modules

Reusable modules that directly wrap one image-backed tool use these constructor
inputs:

- `image_registry`
- `image_repository`
- `image_tag`
- `container_user_id`

The module builds the runtime image reference internally from registry,
repository, and tag. Callers can override one field without parsing a combined
image string.

New image-backed modules define these defaults as module-level constants:

- `DEFAULT_IMAGE_REGISTRY`
- `DEFAULT_IMAGE_REPOSITORY`
- `DEFAULT_IMAGE_TAG`
- `DEFAULT_CONTAINER_USER_ID`

`DEFAULT_IMAGE_TAG` is Renovate-managed. Put the strict Renovate annotation on
the line immediately before the tag constant:

```python
DEFAULT_IMAGE_REGISTRY = "docker.io"
DEFAULT_IMAGE_REPOSITORY = "alpine/helm"
# renovate: datasource=docker depName=alpine/helm
DEFAULT_IMAGE_TAG = "3.18.6"
DEFAULT_CONTAINER_USER_ID = "65532"
```

Docker Hub images use the repository name as `depName`, for example
`alpine/helm`. Non-Docker Hub images include the registry in `depName`, for
example `ghcr.io/riftonix/container-images/hugo-autoprefixer`.

Default runtime images should be public and `DEFAULT_IMAGE_TAG` should be pinned
to a concrete tag instead of `latest`, unless a design explicitly documents a
different choice.

Example:

```bash
dagger -m ./modules/hugo call \
  --source=./site \
  --image-tag=0.154.5-10.5.0 \
  build \
  --hugo-theme-url=github.com/google/docsy@v0.13.0 \
  --site-base-url=https://example.com/
```

`modules/helm-unittest` follows the same split-input convention and defaults to
the public `helmunittest/helm-unittest` runtime. `modules/opentofu` also follows
the convention. Its `executor` input remains separate because it selects the
command to run inside the image, such as `tofu` or `terraform`, not the image
identity.

## Multi-Tool Scenarios

Scenarios that compose one image-backed module expose the composed tool's
runtime image fields with a purpose prefix. Scenarios that compose more than one
image-backed module expose one prefixed input set per tool.

Examples:

- `hugo_image_registry`, `hugo_image_repository`, `hugo_image_tag`, `hugo_container_user_id`
- `helm_image_registry`, `helm_image_repository`, `helm_image_tag`, `helm_container_user_id`
- `git_image_registry`, `git_image_repository`, `git_image_tag`, `git_container_user_id`

The container user field uses `container_user_id` because the user is a
container execution setting, not part of the image reference.

Scenario source uses the same constant convention with a tool prefix:

```python
DEFAULT_HELM_IMAGE_REGISTRY = "docker.io"
DEFAULT_HELM_IMAGE_REPOSITORY = "alpine/helm"
# renovate: datasource=docker depName=alpine/helm
DEFAULT_HELM_IMAGE_TAG = "3.18.6"
DEFAULT_HELM_CONTAINER_USER_ID = "65532"
```

Use the same `datasource` and `depName` anywhere the same runtime image appears
so Renovate updates module, scenario, and fixture uses in one MR.

Example static-site pin:

```bash
dagger -m ./scenarios/static-site call \
  --source=./site \
  --hugo-theme-url=github.com/google/docsy@v0.13.0 \
  --hugo-image-tag=0.154.5-10.5.0 \
  verify-site \
  --site-base-url=https://example.com/ \
  --engine=hugo
```

Example Helm CI pins:

```bash
dagger -m ./scenarios/helm-ci call \
  --helm-image-tag=3.18.6 \
  --git-image-tag=2.52.0 \
  helm-verify-changed-charts \
  --source=. \
  --target-branch=master \
  --charts-path=charts
```

Single-chart Helm operations do not use the Git module, but the Git runtime
image inputs remain on the scenario constructor for changed-chart operations.

## Docker Build Metadata Exceptions

Docker build and publication APIs keep build-specific names. Do not rename these
inputs to the runtime image convention:

- `image_ref`
- `image_refs`
- `tags`
- `context_path`
- `dockerfile_path`
- `bake_path`
- `variable_overrides`
- registry authentication fields such as usernames and passwords

Those inputs describe images being built, tagged, pushed, or authenticated. They
do not select the tool container that runs the Dagger operation.

## Renovate Synchronization

Default runtime image versions must not be constructor literals. Store each
runtime image as registry, repository, and tag constants, and annotate the tag
constant for Renovate.

When the same runtime image default appears in module code, scenario code, test
fixtures, documentation, or downstream workflow examples, use the same
`datasource` and `depName`. Renovate should update the full runtime image tag
atomically, including composite tags such as `0.154.5-10.5.0`.

Tests for a module or scenario should rely on the parent module or scenario
defaults by calling `dag.<module>(...)` or `dag.<scenario>(...)` without passing
duplicated image arguments. Add test-local image constants only when the test
needs a distinct fixture image, such as a Git container used to create a fixture
repository. Fixture image tags use the same Renovate annotation format as module
and scenario runtime image tags.

For Hugo builder-coupled site configuration, track `module.hugoVersion.min` from
the same Docker image stream used by the runtime builder. The current Hugo
runtime follows Docker tags from `hugomods/hugo` with this extraction rule:

```text
^exts-(?<version>.+)$
```

Do not track `module.hugoVersion.min` from `gohugoio/hugo` GitHub releases when
the minimum version is intended to describe the Hugo version available in the
runtime builder.

## Release Tags

Changing public runtime image inputs in a released module or scenario requires a
new release tag. Consumers should pin the old tag until they update their Dagger
calls.

Breaking migrations include removing a combined input such as `container_image`
and replacing it with `image_registry`, `image_repository`, and `image_tag`.
Source-compatible constructor additions should still be released under a new tag
when they change the public scenario or module API.
