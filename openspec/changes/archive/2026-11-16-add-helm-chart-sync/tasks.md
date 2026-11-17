# Tasks

Commands that run Dagger functions, containers, image builds, or network calls (`make tests ...`, `dagger call ...`, `dagger develop`, `docker buildx bake ...`) need explicit approval from the repository owner before each run.

## 1. Runtime Image (container-images repository)

- [x] 1.1 Extend `docker/updatecli-python-nodejs` in `container-images`:
  - add the bake variable `HELM_VERSION` (default `4.3.2`, description `renovate: datasource=docker depName=alpine/helm`) and pass it as a build argument;
  - add a `FROM docker.io/alpine/helm:${HELM_VERSION} AS helm` stage, verify the binary path in that image, and copy `helm` to `/usr/local/bin/helm`;
  - add `helm version` to the build checks;
  - change the tag to `py<python>-node<node>-updatecli<updatecli>-pyyaml<pyyaml>-helm<helm>` and update the image labels.

  Verify with the repository CI build for both platforms.

  Verified: the binary is at `/usr/bin/helm` in `alpine/helm:4.3.2` (image history). The build check compares `helm version --template '{{.Version}}'` with `v${HELM_VERSION}`. CI of [container-images#122](https://github.com/riftonix/container-images/pull/122) ([run 43837457309](https://github.com/riftonix/container-images/actions/runs/43837457309/job/133198066308)) built `linux/amd64` and `linux/arm64` with that check and passed.
- [x] 1.2 Update `docs/reference/updatecli-python-nodejs.md` and its catalog entries with Helm and the new tag. Verify that all relative links in the affected pages resolve.

  Verified: `docs/reference/updatecli-python-nodejs.md` and the `docs/README.md` catalog entry describe Helm, `HELM_VERSION`, and the new tag; all relative links in `docs/README.md`, `docs/reference/README.md`, and the reference page resolve.
- [x] 1.3 Publish the new tag and verify that it resolves for `linux/amd64` and `linux/arm64`, with user `pn`. Record the index digest.

  Verified: [container-images#122](https://github.com/riftonix/container-images/pull/122) merged as `52ab26b`; [Publish run 43838164488](https://github.com/riftonix/container-images/actions/runs/43838164488) succeeded. `ghcr.io/riftonix/container-images/updatecli-python-nodejs:py3.14-node26-updatecli0.123.0-pyyaml6.0.3-helm4.3.2` resolves to index `sha256:ffb645269975e3dd1dc4e7ad73689cd6830a906cf58aa2ccfe71803d850c2957` with `linux/amd64` (`sha256:2b836ef2d40083fff4e70d29a889d4cd6cc46a5eb2c0f689c41ec81a4d2bc4f9`) and `linux/arm64` (`sha256:85736cffb4c73ab9b78626d0b25305f380963da4b143abf027674ab474825715`); both configs have user `pn` and label `io.riftonix.container-images.helm.version=4.3.2`.

## 2. Helm CI Scenario Chart Sync

- [x] 2.1 Add the `updatecli` dependency on `../../modules/updatecli` to `scenarios/helm-ci/dagger.json` and refresh the generated SDK of the scenario and its tests with approval. Verify with `make lint-check scenario helm-ci`.

  Already done in `6a452bb`: engine `v0.21.10` in all scenario and scenario test `dagger.json` files, the Renovate `engineVersion` manager pattern, and `scripts/check_dagger_version.py` coverage of `scenarios/**/dagger.json` (`python3 scripts/check_dagger_version.py` reports aligned `0.21.10`).

  Verified: `make lint-check scenario helm-ci` passes; `make tests scenario helm-ci` regenerated the scenario and test SDKs with the `Updatecli` binding.
- [x] 2.2 Add `with_container(container) -> Self` to `modules/updatecli`, as in `modules/helm`, with a test in `modules/updatecli/tests` that runs a manifest in a container with an added environment variable, included in `all()`, and a README entry. Verify with `make lint-check module updatecli` and, with approval, `make tests module updatecli`.

  Verified: `make lint-check module updatecli` passes, and `make tests module updatecli` passes.
- [x] 2.3 Add the `DEFAULT_UPDATECLI_IMAGE_*` constants (tag from 1.3, Renovate-annotated, with a versioning that matches the composite tag) and the `updatecli_*` constructor inputs. Verify with `make lint-check scenario helm-ci`.

  Verified: `make lint-check scenario helm-ci` passes; the Renovate `versioning` regex matches the current tag (compatibility `3.14-node26`, Updatecli as major, minor, and patch, Helm major and minor as build and revision) and rejects tags without Helm and `latest`.
- [x] 2.4 Implement configuration loading and validation:
  - component defaults and overrides;
  - the `components` selection;
  - unsafe IDs and paths;
  - missing, symlinked, or invalid pins;
  - unsupported filters;
  - all errors in one message.

  Verify with the validation tests in 2.8.

  Verified: `sync-charts reports-all-configuration-errors`, `reports-missing-configuration`, and `rejects-unknown-component` pass in `make tests scenario helm-ci`.
- [x] 2.5 Port `sync_chart.py` to `src/helm_ci/chart_sync.py` with the `sync --config --component` command:
  - tag listing with the anonymous Bearer token flow and pagination;
  - stable semver selection with the filter, and no proposal unless the selected version is greater than the pin;
  - the `upstream.plainhttp` option;
  - pulls, digest and identity checks, exclusions, rewrites, merge, collision check, and `git apply --check`;
  - writes only when `DRY_RUN=false`, stdout only on change, exit code `1` on failure.

  Verify with the tests in 2.8.

  Verified: the version selection and merge tests and the no match, unreachable registry, digest, conflict, collision, and unsafe content cases of `reports-component-failures` pass in `make tests scenario helm-ci`.
- [x] 2.6 Implement manifest rendering for local mode and GitHub mode:
  - SCM with `commitusingapi` and `submodules: false`;
  - no sources;
  - a shell target with `disablesourceinput`, `console/output`, and `PATH` and `HOME` environments;
  - a `github/pullrequest` action with merge strategy `manual`;
  - `pipelineid` `upstream-<id>`.

  Verify with the manifest rendering tests in 2.8.

  Verified: `sync-charts selects-components` and `renders-local-and-pull-request-manifests` pass in `make tests scenario helm-ci`.
- [x] 2.7 Implement `updatecli_container`, `with_updatecli_container`, `sync_charts_manifest`, `sync_charts_diff`, `sync_charts`, and `sync_charts_update` over the Updatecli module, with the runtime container passed through `with_container`, the helper mounted at `/opt/chart-sync`, and the token passed as the `UPDATECLI_GITHUB_TOKEN` secret variable. Verify with `make lint-check scenario helm-ci` and the tests in 2.8.

  Verified: `make lint-check scenario helm-ci` passes and the runtime container and chart sync tests pass in `make tests scenario helm-ci`. `sync_charts` evaluates the Updatecli result before returning it, so failures keep the Updatecli output.
- [x] 2.8 Extend `scenarios/helm-ci/tests` so that `all()` covers every chart sync spec scenario that runs on local fixtures. The fixtures are a `registry:3` Dagger service (the tag pinned in `modules/helm/tests`) with pushed fixture chart versions, bound to the runtime container through `with_updatecli_container`, `upstream.plainhttp: true`, pins computed from the pushed digests, and a temporary fork repository. The checks cover:
  - configuration validation;
  - version selection with signature and prerelease tags, up-to-date and higher pins, and no matching tag;
  - digest mismatch;
  - additions, deletions, renames, and local-only files;
  - conflict and version collision without writes;
  - exclusions, rewrites, and binary files;
  - preview without writes, and local synchronization that changes only one component directory and its pin;
  - an independent failing component;
  - the default and replaced runtime container;
  - the rendered GitHub manifest without token values.

  Verify with `make tests scenario helm-ci`.

  Verified: `make tests scenario helm-ci` passes (`Tests.all` in 7m7s). `Tests.all()` runs the 14 chart sync tests of `SyncChartsTests` (`dagger call sync-charts <test>`), which read fork, upstream, and registry fixtures from `tests/fixtures/`.
- [x] 2.9 Update `scenarios/helm-ci/README.md` with the chart sync configuration, functions, inputs, and the scheduled or dispatched workflow with the built-in token and CI dispatch. The `docs/` reference and how-to pages are updated after the change is archived. Verify that all relative links resolve and that the documented commands match the scenario functions.

  Verified: the README documents `sync-charts-diff`, `sync-charts`, `sync-charts-manifest`, `sync-charts-update`, `updatecli-container`, and `with-updatecli-container`, matching the scenario functions; its relative links are unchanged and resolve.
## 3. Integration Verification

- [x] 3.1 With explicit approval, run `dagger -m ./scenarios/helm-ci call --source=<helm-shared checkout> sync-charts-diff --components=common` and verify that it either reports the expected upstream version or prints no change, with the pinned digest accepted.

  Verified on `helm-shared` `master` at `37c5706` with the scenario at `7be2309`: `common` is pinned to `1.0.5`, the highest matching upstream tag, so the run reports `NOTHING CHANGED` (`Changed: 0`, `Failed: 0`). An up-to-date component is not pulled, so the pinned digest check is covered by 3.2.
- [x] 3.2 With explicit approval, run `sync-charts` for one component with a known newer upstream version against a temporary copy of a `helm-shared` checkout, and verify that only the component directory and its pin change.

  Verified with `sync-charts --components=traefik` exported into a clone of `helm-shared` at `37c5706`: the pinned `1.0.5` package passed the digest check, and the run synchronized `traefik` to `1.0.6`. `git status` shows only `libs/traefik/Chart.yaml` (`version` `1.0.5` to `1.0.6`) and `updatecli/pins/traefik.json` (`1.0.6`, `sha256:c7a24c5b13fa453be3403eb639558c277470b46dd6bde32a0b005627316d728a`).
- [x] 3.3 Run `make openspec-validate` and verify that the change validates.

  Verified: `openspec validate add-helm-chart-sync --strict` reports the change as valid, and `make openspec-validate` passes.

## Workflow follow-up

- In `helm-shared`:
  - set `DAGGER_VERSION` to `0.21.10` or later;
  - add `workflow_dispatch` to `ci.yaml`, with the merge base of `origin/master` as the base and `github.sha` as the head;
  - replace `updatecli.yaml` with the scenario call (`contents`, `pull-requests`, and `actions` write permissions, built-in token, optional `component` input) and the CI dispatch for open `updatecli_master_upstream-*` branches;
  - add a Renovate annotation for the scenario tag;
  - remove `updatecli/manifest.yaml`, `updatecli/sync_chart.py`, `updatecli/requirements.txt`, `updatecli/tests/`, and the `github` block in `values.yaml`;
  - update `updatecli/README.md` and the root README.
- Dispatch the first run for one component and review the resulting pull request before running all components.
- Archive the change after implementation and review, then update `docs/` per the archived change.
