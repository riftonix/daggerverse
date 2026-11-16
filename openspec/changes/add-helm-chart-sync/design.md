# Add Helm Chart Sync Design

## Glossary and References

### Glossary

- **Component**: one forked chart directory in `helm-shared` (`charts/<name>` or `libs/<name>`) with its own upstream chart, pin, pipeline, and pull request. The component ID is also the local chart name.
- **Chart sync configuration**: `updatecli/values.yaml` in `helm-shared`. It holds the upstream registry, version filter, exclusions, rewrite rules, `home`, and components. The file keeps its historical name, but the scenario reads it directly and does not pass it to Updatecli as values.
- **Pin**: `updatecli/pins/<id>.json`, the synchronized upstream `version` and OCI manifest `digest` of one component.
- **Base, incoming, ours**: the normalized pinned package, the normalized selected package, and the current fork directory, as merged by `git merge-tree`.

### References

- Draft updater: `riftonix/helm-shared` `master` at `9ec2b32`, files `updatecli/sync_chart.py`, `updatecli/manifest.yaml`, `updatecli/values.yaml`, `updatecli/README.md`, `updatecli/tests/test_sync_chart.py`, `.github/workflows/updatecli.yaml`.
- Principles and shared components: `openspec/changes/add-skills-sync/design.md` (`modules/updatecli`, runtime image, built-in token with CI dispatch).
- Updatecli v0.123.0 GitHub SCM: `pkg/plugins/scms/github/main.go` (`force`, `commitusingapi`, working branch `updatecli_<branch>_<pipelineid>`).
- OCI Distribution Specification: tag listing `GET /v2/<name>/tags/list`, with Docker registry token authentication.
- Specs: `specs/helm-ci-scenario/spec.md`.

## Context

### Problem Context

See `proposal.md`, section Why. The draft has these technical properties:

- `values.yaml` declares `upstream.registry: oci://registry.nixys.ru/nuc`, the default filter `>=1.0.0 <2.0.0`, shared exclusions, ordered rewrite rules, `home`, a `github` block for the SCM, and 25 components. Only `appchart` (`>=3.0.0 <4.0.0`) and `cert-manager` (`upstream: nuc-certificates`) override defaults.
- `sync_chart.py --component <id> --version <v>` does the following:
  1. it validates the component and the pin path;
  2. it returns silently when the version equals the pin;
  3. it pulls both packages with a private Helm and git environment;
  4. it normalizes the packages and merges them;
  5. it runs `git apply --check`;
  6. it prints one line and writes only when `DRY_RUN=false`.
- The draft selects versions with an Updatecli `helmchart` source. A failed source makes Updatecli v0.123.0 skip the pipeline and exit `0`.
- Harbor at `registry.nixys.ru` refuses anonymous `GET /v2/nuc/<name>/tags/list` with `401` and a `WWW-Authenticate: Bearer realm="https://registry.nixys.ru/service/token",service="harbor-registry",scope="repository:nuc/<name>:pull"` challenge. An anonymous token from that realm allows the listing. Tag lists include cosign signature tags such as `sha256-<hex>.sig`.

### Existing Technical Constraints

- Daggerverse conventions apply:
  - prefixed runtime image inputs;
  - Renovate-annotated `*_IMAGE_TAG` constants;
  - Dagger test modules with `all()`;
  - the repository-aligned engine version.
- All modules use engine `v0.21.10`. The scenarios and their tests used `v0.20.8` (`static-site` tests `v0.21.9`), because the Renovate `engineVersion` manager and `scripts/check_dagger_version.py` covered only `modules/**/dagger.json`. Dagger refuses to load a module whose `engineVersion` is newer than the running engine (`module requires dagger <version>, but you have <version>`).
- `scenarios/helm-ci` already depends on `pyyaml==6.0.3`.
- The published `updatecli-python-nodejs` tag `py3.14-node26-updatecli0.123.0-pyyaml6.0.3` has Updatecli, git 2.47.3 (with `merge-tree --write-tree`, available since git 2.38), and Python 3.14 with PyYAML, but no Helm. Its runtime user is `pn` (uid 1000).
- The `helm-shared` `master` branch has these protections and settings:
  - required check `CI Passed` with strict up-to-date branches;
  - push restrictions that allow only the Renovate app;
  - Actions `default_workflow_permissions: read` and `can_approve_pull_request_reviews: true`.
- `helm-shared` `ci.yaml` reads `github.event.pull_request.base.sha` and `head.sha`, so it works only for `pull_request` events.

## Goals / Non-Goals

### Goals

- Keep the chart sync rules in one helper executed by Updatecli, so that preview, local synchronization, and pull request runs share one code path.
- Preserve the behavior of `sync_chart.py`, except for version selection and the obsolete `github` block.
- Keep `modules/updatecli` generic: no Helm-specific logic in the module.

### Non-Goals

- Updatecli autodiscovery, Updatecli Compose, or Updatecli SCM kinds other than `github`.
- Registry authentication, plain-HTTP registries other than local test fixtures, and non-OCI chart repositories.
- Verifying cosign signatures of upstream packages.

## Architecture and Component Boundaries

### Architecture Overview

```text
helm-shared workflow ──> scenarios/helm-ci sync_charts* ──> modules/updatecli ──> Updatecli in runtime image
                              │ validates config and pins,       │
                              │ renders one pipeline per         ├─ shell target: chart_sync.py sync
                              │ component, mounts chart_sync.py  │  (selects version, pulls, merges, writes)
                              │                                  └─ github/pullrequest action
helm-shared workflow ──> gh workflow run ci.yaml --ref <updatecli branch>
```

### Component Responsibilities

- **`scenarios/helm-ci` chart sync functions**:
  - read and validate the configuration and pins from `source`;
  - render the Updatecli manifest;
  - mount the helper;
  - select local or GitHub SCM mode.
- **`chart_sync.py`**: a stdlib-plus-PyYAML helper bundled in the scenario source. It does the following for one component:
  - lists upstream tags and selects the version;
  - pulls packages with Helm and checks digests;
  - normalizes the packages, merges them with git, and writes the component directory and pin;
  - prints the change report.
- **`modules/updatecli`** (from `add-skills-sync`): runs `updatecli pipeline diff`, `updatecli pipeline apply`, or `updatecli manifest show` with the mounted manifest, working tree, helper directory, and secrets, in its own or a caller-provided runtime container.
- **Runtime image `updatecli-python-nodejs`** (in `container-images`): provides Updatecli, Helm, git, and Python 3.14 with PyYAML.
- **`helm-shared` workflow**: grants token permissions, runs the update function, and dispatches CI on update branches.

### Component Boundaries

- The Updatecli module does not know about Helm, charts, or pins.
- The existing Helm CI functions and their Helm, Git, and Helm unittest module calls are unchanged. Chart sync does not use `modules/helm`; it runs Helm inside the Updatecli runtime image, because the Updatecli shell target needs Helm in its own container.
- The scenario does not schedule runs, trigger CI, enable auto-merge, or merge.
- Only the helper writes component directories and pins. Configuration data never supplies commands to execute.

### Dependencies and Data Flows

1. The scenario reads `config_path` and the pins from `source`, validates them, and applies the `components` selection.
2. The scenario renders one Updatecli pipeline per selected component. It then calls the Updatecli module with the runtime container (the module default with `source` at `/work`, or the caller replacement), the manifest, the helper directory, and, in update mode, the `UPDATECLI_GITHUB_TOKEN` secret.
3. Updatecli runs the shell target in the working tree: the local `source`, or the Updatecli clone of `branch`. The pipeline has no sources.
4. The helper selects the version, prepares the merged result, and checks the patch. Then it prints the report and writes the result, or prints nothing when the component is up to date.
5. In update mode, Updatecli commits the changed files through the GitHub API on the component working branch and creates or updates the pull request.

## Component Changes

### Helm CI Scenario

- **Dependency:** a new local dependency `updatecli` on `../../modules/updatecli`.
- **Engine:** `v0.21.10`, from the engine alignment below. The generated SDK of the scenario and its tests is refreshed together with the new dependency.
- **Constructor:** new inputs `updatecli_image_registry`, `updatecli_image_repository`, `updatecli_image_tag`, and `updatecli_container_user_id`. The defaults come from new `DEFAULT_UPDATECLI_IMAGE_*` constants:
  - registry `ghcr.io`;
  - repository `riftonix/container-images/updatecli-python-nodejs`;
  - the new Helm-enabled tag, with a Renovate annotation;
  - container user `65532`, as in `add-skills-sync`.
- **New files:** `src/helm_ci/chart_sync.py` (the helper) and the manifest renderer. The scenario mounts the helper at `/opt/chart-sync`.
- **Runtime container:** a new optional field `updatecli_container_`. `updatecli_container()` returns it, or `dag.updatecli(source=source, <updatecli_* inputs>).container()` when it is unset. `with_updatecli_container(container)` sets it. Every chart sync function passes the result to the Updatecli module through `with_container`, then adds the helper, the token, and the manifest. This is the `container()` and `with_container()` pattern of `modules/helm`.
- **Existing functions:** unchanged.

### Updatecli Module

- **New function:** `with_container(container: Container) -> Self` replaces the cached runtime container, as in `modules/helm`. Later `with_*` additions and commands use it.
- **Tests:** a check that runs a manifest in a container with an added environment variable and asserts that the variable value appears in the output.
- **README:** documents the function.

### Engine Version Alignment

- `engineVersion` is `v0.21.10` in `dagger.json` of `scenarios/container-images`, `scenarios/helm-ci`, `scenarios/static-site`, and their `tests` modules.
- The Renovate `engineVersion` regex manager matches `/^(modules|scenarios)/.*/dagger\.json$/`.
- `scripts/check_dagger_version.py` checks `modules/**/dagger.json` and `scenarios/**/dagger.json` against the workflow `DAGGER_VERSION`.

### Chart Sync Helper

The helper is a port of `sync_chart.py` with these differences:

- The command is `sync --config <path> --component <id>`, without `--version`. The helper selects the version itself (see [External Integrations](#external-integrations)).
- It proposes nothing when the selected version is not greater than the pinned version. The draft returned only on equality, and it would downgrade a pin that is higher than the filter range.
- It validates the version filter syntax: space-separated `=`, `>`, `>=`, `<`, `<=` comparisons with `MAJOR.MINOR.PATCH` versions.
- It reads `upstream.plainhttp` (default `false`) and passes `--plain-http` to Helm and `http` to tag listing. The setting exists for the local test registry.
- It ignores configuration keys it does not read, including the obsolete `github` block. A newer scenario therefore accepts the current `values.yaml` until the `helm-shared` follow-up removes the block.
- It exits `1` on any component failure, with diagnostics on stderr. The draft exited `2`.

The rest is kept from the draft:

- the private `HOME`, `DOCKER_CONFIG`, Helm, and git environment;
- the identity and digest checks;
- copying without symbolic links or `.git` metadata;
- exact-path exclusions;
- the ordered rewrite rules;
- the three-way merge with `git merge-tree --write-tree`, and `git apply --check` before writing;
- the version-collision check;
- writing only when `DRY_RUN=false`.

### External Components

- `container-images`: `docker/updatecli-python-nodejs` gets the following changes:
  - a new bake variable `HELM_VERSION`, default `4.3.2` (the `alpine/helm` tag that Daggerverse already pins in `modules/helm` and `scenarios/helm-ci`), with the description `renovate: datasource=docker depName=alpine/helm`;
  - a Dockerfile stage `FROM docker.io/alpine/helm:${HELM_VERSION}`, from which the image copies the `helm` binary (at `/usr/bin/helm`) into `/usr/local/bin/helm`;
  - a `helm version` build check;
  - the tag `py<python>-node<node>-updatecli<updatecli>-pyyaml<pyyaml>-helm<helm>`, for example `py3.14-node26-updatecli0.123.0-pyyaml6.0.3-helm4.3.2`, with updated labels and `docs/reference/updatecli-python-nodejs.md`.

  The previous tag stays published.
- `helm-shared`: see [Migration Plan](#migration-plan).

## Data Model

### Entities and Relationships

The configuration format is unchanged from the draft. The new optional key `upstream.plainhttp` is used only by test fixtures:

```yaml
upstream:
  registry: oci://registry.nixys.ru/nuc
  versionfilter: '>=1.0.0 <2.0.0'
  exclude: [.github/, docs/AGENTS.md, CHANGELOG.md, charts/, Chart.lock, LICENSE]
home: https://github.com/riftonix/helm-shared
rewrite:
- {from: oci://registry.nixys.ru/nuc, to: oci://ghcr.io/riftonix/helm-shared/libs}
- {file: Chart.yaml, regex: '...', to: ''}
components:
  appchart: {path: charts/appchart, upstream: nxs-universal-chart, versionfilter: '>=3.0.0 <4.0.0', rewrite: [...]}
  common: {}
```

A pin:

```json
{
  "version": "1.0.5",
  "digest": "sha256:8eb6082623fc13f0e09a02f9e7941728f42e461bbb5d0483cb934c9986cf5264"
}
```

### Persistence Model

- The helper writes a pin as JSON with 2-space indentation and a trailing newline, keys `version` and `digest`.
- Component directory changes are applied as a binary git patch with rename detection relative to the component directory.

### Ownership and Lifecycle

- `helm-shared` owns the configuration and the fork-only content of each component.
- Upstream owns the content that the merge brings in from the selected package.
- The helper writes the pin and the merged component directory. Registering a component, including the first pin, stays a manual `helm-shared` change.

### Indexes and Constraints

- Component IDs are unique map keys that match `[a-z0-9][a-z0-9-]*`.
- A component path has exactly two segments, the first one `charts` or `libs`, and resolves inside the repository.
- A pin file is a regular file inside the repository.

## Technical Contracts

### External Integrations

- **Tag listing:**
  - **Request:** for `oci://<host>/<project>` and upstream chart `<name>`, the helper sends `GET https://<host>/v2/<project>/<name>/tags/list` with `urllib`.
  - **Authentication:** on `401` with a `Bearer` challenge, it requests an anonymous token from the challenge `realm` with the challenge `service` and `scope`, then retries once with `Authorization: Bearer <token>`. It accepts the `token` or `access_token` response field.
  - **Pagination:** it follows `Link: <...>; rel="next"` headers.
  - **Selection:** it ignores tags that are not `MAJOR.MINOR.PATCH`, applies the filter, and selects the maximum.
- **Helm:** `helm pull <registry>/<name> --version <v> --untar --destination <dir> --registry-config <private file>`, plus `--plain-http` when configured. The digest is parsed from the `Digest: sha256:<hex>` line of the Helm output.
- **git:** a private bare repository holds the trees of base, ours, and incoming. The helper does the following:
  1. it runs `git merge-tree --write-tree` on commits created with fixed author and committer data;
  2. it checks out the result;
  3. it runs `git diff --binary --full-index --find-renames`;
  4. it runs `git apply --check --directory <path>`, then `git apply` on the working tree.
- **GitHub:**
  - Updatecli `github` SCM with `owner`, `repository`, `branch`, `commitusingapi: true`, and `submodules: false`;
  - the token comes from the `UPDATECLI_GITHUB_TOKEN` secret environment variable;
  - the `github/pullrequest` action uses merge strategy `manual`.

### Internal Contracts

Updatecli pipeline per component (local mode omits `scms`, `scmid`, and `actions`):

```yaml
name: Update common from upstream OCI
pipelineid: upstream-common
scms:
  fork:
    kind: github
    spec: {owner: riftonix, repository: helm-shared, branch: master, commitusingapi: true, submodules: false}
targets:
  component:
    name: Merge only libs/common and its source pin
    kind: shell
    scmid: fork
    disablesourceinput: true
    spec:
      command: python3 -I /opt/chart-sync/chart_sync.py sync --config updatecli/values.yaml --component common
      changedif: {kind: console/output}
      environments: [{name: PATH}, {name: HOME}]
actions:
  pullrequest:
    kind: github/pullrequest
    scmid: fork
    title: "chore(deps): update common from upstream"
    spec:
      merge: {strategy: manual}
      description: |
        Updates only `libs/common` and `updatecli/pins/common.json`.
        Components are independent. Merge and publish missing dependencies first,
        then rerun this pipeline. Updatecli does not order or merge dependency PRs.
```

- **`pipelineid`:** `upstream-<id>`, as in the draft. Updatecli derives the working branch `updatecli_<branch>_upstream-<id>`.
- **Helper `sync` contract:**
  - **Input:** `--config`, `--component`, and `DRY_RUN` set to `true` or `false`. The working directory is the repository root.
  - **Changes:** the helper prints `Preview <id>: <pinned> -> <selected>` or `Apply <id>: <pinned> -> <selected>` only when it changed or would change files. An up-to-date component prints nothing, because any target stdout marks the pipeline as changed.
  - **Dry run:** with `DRY_RUN` other than `false`, it writes nothing. Tag listing and package pulls still run, because they only read upstream.
  - **Exit codes:** `0` on success, `1` on any failure. Diagnostics go to stderr, truncated to the last 6000 characters of tool output.

## Interfaces

### Command-Line Interface

```sh
# Preview, local sync, manifest, pull requests
dagger -m github.com/riftonix/daggerverse/scenarios/helm-ci@<tag> call --source=. sync-charts-diff --components=traefik
dagger -m github.com/riftonix/daggerverse/scenarios/helm-ci@<tag> call --source=. sync-charts export --path=.
dagger -m github.com/riftonix/daggerverse/scenarios/helm-ci@<tag> call --source=. \
  sync-charts-manifest --repository=riftonix/helm-shared --branch=master
dagger -m github.com/riftonix/daggerverse/scenarios/helm-ci@<tag> call --source=. \
  sync-charts-update --github-token=env:GITHUB_TOKEN --repository=riftonix/helm-shared --branch=master
```

### Internal Interfaces

**Helm CI scenario additions:**
- **Constructor:** the existing inputs, plus `updatecli_image_registry`, `updatecli_image_repository`, `updatecli_image_tag`, and `updatecli_container_user_id`.
- **Functions:** all of them accept `config_path: str = "updatecli/values.yaml"` and `components: list[str] | None = None`:
  - `sync_charts_manifest(config_path, components, repository: str | None, branch: str | None) -> str`;
  - `sync_charts_diff(config_path, components) -> str`;
  - `sync_charts(config_path, components) -> Directory`;
  - `sync_charts_update(github_token: Secret, repository: str, branch: str, config_path, components) -> str`.
- **Runtime container functions:** `updatecli_container() -> Container` and `with_updatecli_container(container: Container) -> HelmCi`.

**Updatecli module addition:** `with_container(container: Container) -> Updatecli`.

**Test fixture flow:**

```python
ci = dag.helm_ci(source=fixture_repository)
ci = ci.with_updatecli_container(
    ci.updatecli_container()
    .with_service_binding("registry", registry_service)
    .with_env_variable("NO_PROXY", "registry,registry:5000")
)
report = await ci.sync_charts_diff()
```

The fixture configuration uses `upstream.registry: oci://registry:5000/<project>` and `upstream.plainhttp: true`.

**`helm-shared` workflow sketch** (external task):

```yaml
on:
  workflow_dispatch:
    inputs:
      component: {description: Component ID; empty runs all components, required: false, type: string}
permissions: {contents: write, pull-requests: write, actions: write}
concurrency: {group: updatecli-charts, cancel-in-progress: false}
steps:
  - uses: actions/checkout@v7
  - uses: dagger/dagger-for-github@v8.4.1
  - run: |
      args=()
      [[ -n "$COMPONENT" ]] && args+=(--components="$COMPONENT")
      dagger -m "$HELM_CI_SCENARIO" call --source=. sync-charts-update \
        --github-token=env:GITHUB_TOKEN --repository="$GITHUB_REPOSITORY" --branch=master "${args[@]}"
    env: {GITHUB_TOKEN: "${{ github.token }}", COMPONENT: "${{ inputs.component }}"}
  - run: |
      gh pr list --state open --json headRefName --jq '.[].headRefName | select(startswith("updatecli_master_upstream-"))' |
        while read -r ref; do gh workflow run ci.yaml --ref "$ref"; done
    env: {GH_TOKEN: "${{ github.token }}"}
```

## Error Handling

### Error Categories

- **Configuration errors:** missing keys, unsafe components, missing or invalid pins, an unsupported filter, or an unknown selected component. They fail before any pipeline runs.
- **Resolution errors:** the registry is unreachable, token exchange fails, the tag listing is invalid, or no tag matches. They fail the component target.
- **Package errors:** a Helm pull failure, a missing or mismatched digest, a chart identity mismatch, symbolic links, or `.git` metadata. They fail the component target.
- **Merge errors:** a `merge-tree` conflict, a version collision, or a failed `git apply --check`. They fail the component target without writes.
- **SCM and action errors:** GitHub API or permission failures. They fail the component.

### Error Propagation and Mapping

- Updatecli runs pipelines independently and exits `1` if any of them failed. The module surfaces this as a failed Dagger call that includes the Updatecli output.
- The pipelines have no sources or conditions, so every component error is a target failure and fails the run. It is never a skipped pipeline.
- Configuration errors are raised by the scenario as one error that lists every invalid item.

### Retry and Recovery

- There are no in-run retries. The next run retries every selected component.
- After a merge conflict or version collision, the owner resolves the component manually in a regular pull request, including its pin, and the next run continues from the new pin.

### Logging and Diagnostics

- The helper report and stderr diagnostics appear in the Updatecli output returned by the scenario functions and in the caller job logs.
- The pull request description is the static per-component text above, plus the standard Updatecli report. The selected version is visible in the pin diff.
- `sync_charts_manifest` returns the rendered manifest for inspection. Dagger scrubs secret values from outputs.

## Decisions

### Decision: Select versions inside the shell target

The helper lists OCI tags and selects the version in the same target run that synchronizes the component. With the draft `helmchart` source, an unreachable registry or an empty filter result would skip the pipeline, and the run would exit `0`. A failed target fails the run.

The selected version is not available as a source value, so the pull request title cannot contain it. Reviewers see the version in the pin diff and in the job log.

Alternatives considered:
- keeping the `helmchart` source, rejected because of silent skips;
- a shell source that runs a `resolve` helper command, rejected for the same reason;
- `helm show chart` without `--version`, rejected because it returns only the latest version and ignores the filter.

### Decision: Keep the configuration in `helm-shared`, move the code to the scenario

The component registry, rewrite rules, and pins describe the fork, so they stay with the charts. The adapter, the manifest, and their tests are generic for OCI-forked chart repositories, so they move to `scenarios/helm-ci`. The scenario renders the manifest in Python, as in `add-skills-sync`, so that validation and pipeline rendering are tested without Go templates.

### Decision: Force-pushed working branches

The scenario keeps the Updatecli default `force: true` instead of the draft `force: false`. With force enabled, Updatecli recreates a working branch that diverged from `branch`, so an outdated pull request is rebased on the next run. This matches the strict up-to-date protection of `master` and the `add-skills-sync` behavior.

The trade-off is that manual commits on an update branch are discarded by the next run that changes the component. Manual resolution therefore happens in a separate pull request (see [Retry and Recovery](#retry-and-recovery)).

### Decision: Built-in token with explicit CI dispatch

The `helm-shared` `GITHUB_TOKEN` with `contents`, `pull-requests`, and `actions` write permissions pushes branches and opens pull requests. Those pull requests do not start `pull_request` workflows, so the workflow dispatches `ci.yaml` on each open `updatecli_master_upstream-*` branch, and that run reports `CI Passed` on the head commit.

For dispatched runs, `ci.yaml` gains `workflow_dispatch`. It uses the merge base of `origin/master` and `github.sha` as the base, and `github.sha` as the head.

Alternative considered: a PAT or GitHub App token, as in the draft. Rejected because it requires secret provisioning.

### Decision: Replaceable runtime container for test services

The chart sync tests need a local OCI registry reachable from the Updatecli shell target. The scenario creates the Updatecli container, so the test module cannot bind a service to it directly. The scenario therefore exposes `updatecli_container()` and `with_updatecli_container()`, and `modules/updatecli` gains `with_container()`, following `modules/helm`, whose tests bind the registry the same way. A service binding is part of the container definition, so the alias resolves when the scenario and the Updatecli module run the container.

Alternatives considered:
- an optional `upstream_registry_service` input on the four chart sync functions, rejected because it adds a test-only parameter to every public function;
- addressing the service by its own hostname without a binding, rejected because Dagger resolves service hostnames through the search domains of the calling module only;
- testing the helper outside the scenario, rejected because it would not cover the scenario and Updatecli end to end.

### Decision: Helm in the shared runtime image

The shell target runs inside the Updatecli container, so Helm has to be in that image. Adding it to `updatecli-python-nodejs` and releasing a new tag keeps one runtime image for both Daggerverse Updatecli scenarios. Copying the static binary from `alpine/helm` reuses the tag that Renovate already tracks in Daggerverse.

Alternatives considered:
- downloading Helm in the target at run time, rejected because it adds an unpinned network dependency to every pipeline;
- a separate Helm-specific image, rejected because it duplicates image maintenance.

## Risks / Trade-offs

- [Merged upstream content is published after merge] → No auto-merge. Every update is reviewed in a pull request, and the scenario never merges.
- [Harbor changes its anonymous token flow or tag listing] → The component fails visibly with the HTTP status in the diagnostics, and the next run retries.
- [The caller checkout differs from the remote `branch`] → Validation reads the caller `source`, while update mode reads the Updatecli clone of `branch`. The workflow checks out the same branch that it passes as `branch`.
- [Competing delta for `helm-ci-scenario` in the open `add-helm-shared-ci-workflow` change] → Requirement names do not overlap. Whichever change is archived second may need its delta rebased on the main spec.
- [Engine `v0.21.10` breaks callers on older Dagger] → Callers of the next scenario releases need Dagger `v0.21.10` or later. `helm-shared` must run Dagger `v0.21.10` or later before it consumes the new release. Its `DAGGER_VERSION` is `0.21.9` on `master`.
- [Renovate versioning of the composite image tag] → The Renovate annotation needs a versioning that understands the composite tag. This is shared with `add-skills-sync` and verified when the annotation is added.
- [Static pull request titles] → Accepted: the version is in the pin diff and the job log.
- [The `updatecli-module` capability is introduced by the open `add-skills-sync` change] → This change adds a requirement with a distinct name, so either change can be archived first.
- [A replaced runtime container bypasses the `updatecli_*` image inputs] → Accepted, as in `modules/helm`: the caller owns the container it passes.

## Migration Plan

### Rollout

1. Release the Helm-enabled `updatecli-python-nodejs` tag in `container-images`.
2. Implement the chart sync functions and release a new minor version of `scenarios/helm-ci`.
3. In `helm-shared`, do the following:
   - set `DAGGER_VERSION` to `0.21.10` or later;
   - add `workflow_dispatch` to `ci.yaml`;
   - replace `.github/workflows/updatecli.yaml` with the scenario-based workflow, with a Renovate annotation on the scenario tag;
   - remove `updatecli/manifest.yaml`, `updatecli/sync_chart.py`, `updatecli/requirements.txt`, and `updatecli/tests/`;
   - remove the `github` block from `values.yaml`;
   - update `updatecli/README.md` and the root README.
4. Run `sync-charts-diff` locally, then dispatch the workflow for one component. Review the first pull requests.

### Backward Compatibility

- Existing Helm CI functions and inputs keep their behavior. The only caller-visible change for them is the minimum Dagger version.
- The current `values.yaml` and pins are accepted without changes.

### Rollback

- Restore or delete the `helm-shared` updater workflow, and close open update pull requests.
- Merged updates are reverted with git, including the pin.
- The scenario and image releases can remain published without effect.
