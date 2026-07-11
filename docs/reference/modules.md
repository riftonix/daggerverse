# Module Reference

## Source Input Convention

New and updated modules and scenarios use `source` for the primary caller
provided directory: a repository checkout, chart, site, image build tree, IaC
project, or other main input tree. Secondary inputs keep descriptive names, for
example `values`, `charts_path`, `base_ref`, `head_ref`, `context_path`,
`dockerfile_path`, `bake_path`, and registry or output arguments.

The `source` convention does not move CI provider behavior into modules or
scenarios. GitHub Actions, GitLab CI, and other workflow adapters continue to
own event selection, checkout strategy, preview URL derivation, publication,
cleanup, and pull request or merge request comments. They should translate that
provider state into explicit refs, paths, URLs, secrets, and booleans before
calling Dagger.

Renaming a public primary directory input to `source` is a breaking API change.
Any changed released module or scenario needs a new release tag so downstream
workflows can opt into the new command shape. Consumers that cannot migrate yet
should stay on the previous tag until their Dagger calls are updated.

## Runtime Image Input Convention

Image-backed modules expose the tool runtime image as `image_registry`,
`image_repository`, `image_tag`, and `container_user_id`. Scenarios that compose
image-backed modules use tool-prefixed inputs such as `hugo_image_tag`,
`helm_image_tag`, and `git_image_tag`, with container user fields such as
`hugo_container_user_id`.

Docker build and publish metadata keeps build-specific names such as
`image_ref`, `image_refs`, `tags`, `context_path`, `dockerfile_path`,
`bake_path`, and `variable_overrides`.

For Renovate synchronization, duplicate runtime image defaults are allowed when
all occurrences are tracked from the same dependency source and Renovate updates
the full tag. See [Runtime image input conventions](runtime-images.md).

## git

Provides provider-neutral Git primitives for CI workflows, including refs, diffs, tags, components, repository metadata, authentication, and files-at-ref helpers.

- Path: `modules/git`
- Main source: `modules/git/src/git/main.py`
- Detailed reference: [Git module reference](git.md)
- Typical command: `dagger -m ./modules/git call get-changed-files --source=. --base-ref=origin/main --head-ref=HEAD`
- CI use cases: pull request diffs, changed-component matrices, release tags, repository metadata, and files-at-ref checks.

## docker

Provides Dagger-native Docker and OCI image primitives for CI workflows, including explicit context builds, JSON Docker Buildx Bake targets, build arguments, labels, image references, explicit platforms, smoke checks, registry auth, and publish wiring.

- Path: `modules/docker`
- Main source: `modules/docker/src/docker/main.py`
- Detailed reference: [Docker module reference](docker.md)
- Typical command: `dagger -m ./modules/docker call build --source=. --context-path=modules/docker/tests/fixtures/basic-image container`
- CI use cases: daemonless explicit or Bake-driven image builds, image smoke checks, registry-authenticated publish, and reusable primitives for higher-level container image scenarios.

## helm

Runs Helm operations in a containerized environment.

- Path: `modules/helm`
- Main source: `modules/helm/src/helm/main.py`
- Typical command: `dagger -m ./modules/helm call lint --source=./charts/mychart`

## helm-unittest

Runs Helm chart unit tests in the public `helmunittest/helm-unittest` runtime.

- Path: `modules/helm-unittest`
- Main source: `modules/helm-unittest/src/helm_unittest/main.py`
- Detailed reference: [Helm unittest module reference](helm-unittest.md)
- Typical command: `dagger -m ./modules/helm-unittest call test --source=./charts/mychart`
- CI use cases: direct chart unit test execution and reusable composition from Helm chart validation workflows.

## hugo

Builds, validates, and prepares Hugo sites or Hugo modules in a containerized environment.

- Path: `modules/hugo`
- Main source: `modules/hugo/src/hugo/main.py`
- Detailed reference: [Hugo module reference](hugo.md)
- Typical command: `dagger -m ./modules/hugo call --source=./site build --hugo-theme-url=github.com/google/docsy@v0.13.0 --site-base-url=https://example.com/`
- Reproducible command: `dagger -m ./modules/hugo call --source=./site --image-tag=0.154.5-10.5.0 build --hugo-theme-url=github.com/google/docsy@v0.13.0 --site-base-url=https://example.com/`

## opentofu

Runs OpenTofu or Terraform-compatible formatting, initialization, and validation.

- Path: `modules/opentofu`
- Main source: `modules/opentofu/src/opentofu/main.py`
- Typical command: `dagger -m ./modules/opentofu call lint --source=./iac`
- Reproducible command: `dagger -m ./modules/opentofu call --image-tag=latest lint --source=./iac`

## ssh

Runs SSH client operations in a container.

- Path: `modules/ssh`
- Main source: `modules/ssh/src/ssh/main.py`
- Typical command: `dagger -m ./modules/ssh call exec --destination=example.com`

## Kubernetes Cluster Lifecycle

The previous Kind wrapper module has been removed. Future Kubernetes cluster
lifecycle work should be introduced as a new module, for example a
Talos-oriented module, with its own public contract.

## Scenario Note

Ready-to-run CI jobs are scenarios, not reusable modules.

## helm-ci scenario

Composes the reusable Helm and Git modules into portable Helm chart verification
and publication workflows.

- Path: `scenarios/helm-ci`
- Main source: `scenarios/helm-ci/src/helm_ci/main.py`
- How-to guide: [Run Helm checks through Helm CI](../how-to/run-helm-checks-through-helm-ci.md)
- Typical verify command: `dagger -m ./scenarios/helm-ci call helm-verify --source=./charts/mychart`
- Typical changed-chart command: `dagger -m ./scenarios/helm-ci call verify-charts --source=. --base-ref=origin/master --head-ref=HEAD --charts-path='charts/*'`
- Reproducible changed-chart command: `dagger -m ./scenarios/helm-ci call --helm-image-tag=3.18.6 --git-image-tag=2.52.0 verify-charts --source=. --base-ref=origin/master --head-ref=HEAD --charts-path='charts/*'`
- CI use cases: verify one chart, verify changed chart directories through provider-neutral Git inputs, and publish caller-selected chart versions to OCI registries.

## container-images scenario

Composes the reusable Docker module into a portable image verification and publication workflow.

- Path: `scenarios/container-images`
- Main source: `scenarios/container-images/src/container_images/main.py`
- Detailed reference: [Container images scenario reference](container-images.md)
- Typical verify command: `dagger -m ./scenarios/container-images call verify-image --source=. --context-path=images/api`
- Typical publish command: `dagger -m ./scenarios/container-images call publish-image --source=. --context-path=images/api --image-ref=ghcr.io/example/api:v1.2.3`
- CI use cases: verify selected image contexts, publish caller-provided OCI image references, and keep provider-specific tag/path policy in the workflow layer.

The Docker module and container-images scenario are separate layers. `modules/docker` exposes reusable Docker and OCI primitives for other scenarios. `scenarios/container-images` uses those primitives internally and exposes stable scenario-level inputs and outputs.

## static-site scenario

Composes static-site engine modules into provider-neutral verification and
rendering workflows.

- Path: `scenarios/static-site`
- Main source: `scenarios/static-site/src/static_site/main.py`
- Detailed reference: [Static site scenario reference](static-site.md)
- Typical verify command: `dagger -m ./scenarios/static-site call --source=./site --hugo-theme-url=github.com/google/docsy@v0.13.0 verify-site --site-base-url=https://example.com/ --engine=hugo`
- Typical render command: `dagger -m ./scenarios/static-site call --source=./site --hugo-theme-url=github.com/google/docsy@v0.13.0 render-site --site-base-url=https://example.com/ --engine=hugo --output=./public`
- Reproducible verify command: `dagger -m ./scenarios/static-site call --source=./site --hugo-theme-url=github.com/google/docsy@v0.13.0 --hugo-image-tag=0.154.5-10.5.0 verify-site --site-base-url=https://example.com/ --engine=hugo`
- CI use cases: verify and render caller-selected static sites, validate Hugo mount collisions, and keep provider-specific Pages lifecycle in workflow YAML.
