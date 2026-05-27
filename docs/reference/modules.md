# Module Reference

## git

Provides provider-neutral Git primitives for CI workflows, including refs, diffs, tags, components, repository metadata, authentication, and files-at-ref helpers.

- Path: `modules/git`
- Main source: `modules/git/src/git/main.py`
- Detailed reference: [Git module reference](git.md)
- Typical command: `dagger -m ./modules/git call get-changed-files --source=. --base-ref=origin/main --head-ref=HEAD`
- CI use cases: pull request diffs, changed-component matrices, release tags, repository metadata, and files-at-ref checks.

## docker

Provides Dagger-native Docker and OCI image primitives for CI workflows, including image build, build arguments, explicit platforms, smoke checks, registry auth, and publish wiring.

- Path: `modules/docker`
- Main source: `modules/docker/src/docker/main.py`
- Detailed reference: [Docker module reference](docker.md)
- Typical command: `dagger -m ./modules/docker call build --source=. --context-path=modules/docker/tests/fixtures/basic-image container`
- CI use cases: daemonless image builds, image smoke checks, registry-authenticated publish, and reusable primitives for higher-level container image scenarios.

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

Ready-to-run CI jobs are scenarios, not reusable modules. The current `modules/pipelines` implementation is transitional: it is a temporary Helm CI wrapper for a future scenario, with final naming and layout left to a separate proposal.
