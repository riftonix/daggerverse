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

## pipelines

Orchestrates CI workflows using local module dependencies.

- Path: `modules/pipelines`
- Main source: `modules/pipelines/src/pipelines/main.py`
- Local dependencies: `../helm`, `../git`
- Typical command: `dagger -m ./modules/pipelines call helm-verify --source=./charts/mychart`

## ssh

Runs SSH client operations in a container.

- Path: `modules/ssh`
- Main source: `modules/ssh/src/ssh/main.py`
- Typical command: `dagger -m ./modules/ssh call exec --destination=example.com`
