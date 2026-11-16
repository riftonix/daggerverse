# Add Helm Chart Sync Proposal

## Why

### Initial Requirements and Drivers

The `helm-shared` repository forks Helm charts from the upstream registry `oci://registry.nixys.ru/nuc` and has to follow upstream releases. A draft updater already exists on `helm-shared` `master`: an Updatecli manifest, a Python adapter, and a workflow. The repository owner wants that draft moved into the Daggerverse `scenarios/helm-ci` scenario, using the same principles as the `add-skills-sync` change: Updatecli orchestration, a bundled helper, a dedicated runtime image, and the built-in CI token. This change has to be implemented before section 3 of `add-skills-sync`.

### Current Solution

- `helm-shared` keeps 25 independently versioned components under `charts/` and `libs/`. Each one is registered in `updatecli/values.yaml` and pinned to an upstream version and OCI digest in `updatecli/pins/<id>.json`.
- `updatecli/manifest.yaml` renders one pipeline per component. It uses a `helmchart` source to select the version and a shell target that runs `updatecli/sync_chart.py` from the `helm-shared` checkout.
- `sync_chart.py` pulls the pinned and the new upstream packages with Helm, checks the pinned digest, applies exclusions and rewrite rules, merges the result into the fork with `git merge-tree`, and writes only the component directory and its pin.
- The `Update charts` workflow (`.github/workflows/updatecli.yaml`) runs only manually. It installs Python, PyYAML, Updatecli, and Helm on the runner, and it requires a `UPDATECLI_GITHUB_TOKEN` repository secret (a PAT or GitHub App token). The secret is not configured, and the workflow has never run.
- `helm-shared` CI (`ci.yaml`) starts only on `pull_request` events and uses `scenarios/helm-ci` for chart validation and publication.

### Business Problems

- Forked charts do not follow upstream releases until someone provisions a token secret and runs the workflow by hand.
- The updater logic lives in `helm-shared`, separate from the reusable Helm CI scenario that the repository already uses. It has its own tests and its own toolchain installation steps.
- When the `helmchart` source fails, Updatecli skips the pipeline and exits successfully, so an unreachable registry or an empty version filter goes unnoticed.

## Stakeholders

- Repository owner of `helm-shared` and `daggerverse`: maintains the forked charts and reviews update pull requests.
- Consumers of the published `helm-shared` charts: users of `oci://ghcr.io/riftonix/helm-shared/charts/*` and `libs/*`.

## What Changes

### Goals

- Detect new upstream chart versions for every registered `helm-shared` component.
- Propose each update as an independent, reviewable pull request that changes only the component directory and its pin.
- Run with the built-in CI token of `helm-shared`, without secret provisioning.
- Fail visibly when an upstream version cannot be resolved, a package digest does not match, or an update cannot be merged.
- Keep the chart update logic in the reusable `scenarios/helm-ci` scenario and its tests.

### Scope

- `scenarios/helm-ci` gains chart sync functions for manifest rendering, local preview, local synchronization, and pull request proposal. It also gets a bundled `chart_sync.py` helper ported from `sync_chart.py`, prefixed Updatecli runtime image inputs, and a dependency on `modules/updatecli`.
- The helper resolves upstream versions itself through the OCI Distribution API, instead of using an Updatecli source.
- `scenarios/helm-ci` and its test module move from Dagger engine `v0.20.8` to `v0.21.10`.
- The `updatecli-python-nodejs` runtime image in `container-images` gets Helm and is released under a new tag.
- Repository documentation for the chart sync functions.
- Dependent work in `helm-shared` is tracked as external tasks: replace the draft workflow with a scenario call, dispatch CI on update branches, and remove the draft adapter files.

### Non-Goals

- Automatic merging of update pull requests or ordering of dependent component updates.
- Registries other than OCI registries, and registry credentials. Upstream registries are read anonymously.
- Prerelease upstream versions.
- Changes to the existing `verify_chart`, `publish_chart`, or other existing Helm CI functions.
- Changes to the `add-skills-sync` change or to the Daggerverse Renovate configuration.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `helm-ci-scenario`: adds chart sync configuration, version selection, package integrity, merge, preview, and pull request proposal requirements, and adds Updatecli runtime image inputs.

## Impact

### Users and Business Processes

- The `helm-shared` owner reviews and merges per-component update pull requests instead of running the updater by hand.
- Merge order between dependent components stays a manual decision.

### Systems and Components

- `daggerverse`: `scenarios/helm-ci` source, tests, README, and docs. The scenario gains a local dependency on `modules/updatecli`, which comes from `add-skills-sync`.
- `container-images`: a new `updatecli-python-nodejs` tag that includes Helm. `add-skills-sync` can consume the same tag.
- `helm-shared`: a new scenario-based updater workflow, a manual dispatch trigger in `ci.yaml`, and removal of `updatecli/manifest.yaml`, `updatecli/sync_chart.py`, `updatecli/requirements.txt`, and `updatecli/tests/`.

### Data and Integrations

- `updatecli/values.yaml` and `updatecli/pins/<id>.json` stay in `helm-shared` and keep their format. The `github` block in `values.yaml` becomes obsolete.
- The scenario reads tag lists and chart packages anonymously from `registry.nixys.ru`.
- Pull requests are created through the GitHub API with the `helm-shared` built-in `GITHUB_TOKEN`.

### Operational Impact

- Callers of the new `scenarios/helm-ci` release need Dagger `v0.21.10` or later.
- Pull request CI for update branches has to be started explicitly by the updater workflow, because GitHub does not start `pull_request` workflows for pull requests created by the built-in token.
- New releases of the scenario and the runtime image require Renovate-tracked tags in their consumers.
