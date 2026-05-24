# Module Reference

## git

Detects changed paths and exposes common Git metadata operations.

- Path: `modules/git`
- Main source: `modules/git/src/git/main.py`
- Typical command: `dagger -m ./modules/git call get-changed-paths --source=.`

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
