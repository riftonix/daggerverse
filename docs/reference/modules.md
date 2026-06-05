# Module Reference

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

## hugo

Builds Hugo sites in a containerized environment.

- Path: `modules/hugo`
- Main source: `modules/hugo/src/hugo/main.py`
- Typical command: `dagger -m ./modules/hugo call build --source=./site`

## kind

Provides a container with the `kind` CLI installed.

- Path: `modules/kind`
- Main source: `modules/kind/src/kind/main.py`
- Typical command: `dagger -m ./modules/kind call container`

## opentofu

Runs OpenTofu or Terraform-compatible formatting, initialization, and validation.

- Path: `modules/opentofu`
- Main source: `modules/opentofu/src/opentofu/main.py`
- Typical command: `dagger -m ./modules/opentofu call lint --source=./iac`

## ssh

Runs SSH client operations in a container.

- Path: `modules/ssh`
- Main source: `modules/ssh/src/ssh/main.py`
- Typical command: `dagger -m ./modules/ssh call exec --destination=example.com`

## Scenario Note

Ready-to-run CI jobs are scenarios, not reusable modules.

## helm-ci scenario

Composes the reusable Helm and Git modules into portable Helm chart verification
and publication workflows.

- Path: `scenarios/helm-ci`
- Main source: `scenarios/helm-ci/src/helm_ci/main.py`
- How-to guide: [Run Helm checks through Helm CI](../how-to/run-helm-checks-through-helm-ci.md)
- Typical verify command: `dagger -m ./scenarios/helm-ci call helm-verify --source=./charts/mychart`
- Typical changed-chart command: `dagger -m ./scenarios/helm-ci call helm-verify-changed-charts --source=. --target-branch=master --charts-path=charts`
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
