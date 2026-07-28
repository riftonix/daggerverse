## Why

`riftonix/helm-shared` needs a reusable Helm CI workflow for pull request validation and default-branch chart publication. Daggerverse already has Helm, Git, and Helm CI building blocks, but it does not yet have a dedicated Helm unittest module or the single-call chart publication and Git tagging behavior needed by an external GitHub Actions workflow.

## What Changes

- Extend `scenarios/helm-ci` with provider-neutral changed-chart validation and default-branch release publication.
- Add a dedicated `modules/helm-unittest` module based on the public `helmunittest/helm-unittest` image for charts that contain test suites.
- Extend Helm CI to compose `modules/helm-unittest` while keeping charts without tests valid.
- Add baseline repository requirements for new image-backed module runtime defaults and `container_user_id` naming.
- Add structured chart publication results, including registry-visible OCI references without credentials.
- Publish a caller-selected release chart version and create its Git tag through the Git module in one `publish_chart` Dagger call.
- Support chart roots matching the `helm-shared` layout, including `charts/*` application charts and `libs/*` library charts.
- Support documentation validation as repository content validation only, without rendering or publishing the external main site.
- Keep GitHub Actions, GitLab CI, and other provider mechanics outside Dagger; provider workflows pass explicit refs, paths, run ids, registry destinations, and secrets.

## Capabilities

### New Capabilities

- `helm-unittest-module`: Define the reusable Helm unittest module contract based on the public `helmunittest/helm-unittest` image.

### Modified Capabilities

- `helm-ci-scenario`: Add requirements for composing the Helm unittest module, default-branch release publication, structured results, repository documentation validation, and the `helm-shared` integration contract.
- `daggerverse`: Add repository-wide requirements for new image-backed modules to expose split runtime image inputs, use `container_user_id`, define `DEFAULT_*` constants, use pinned public defaults, and test default plus override behavior.

## Impact

- Affected scenario: `scenarios/helm-ci`
- Affected modules: add `modules/helm-unittest`; `modules/helm` may need chart metadata helpers; `modules/git` should be reused without provider-specific behavior changes.
- Affected tests: add Dagger-native tests under `modules/helm-unittest/tests` and update tests under `scenarios/helm-ci/tests` and `modules/helm/tests` for new public behavior.
- Affected docs: update Helm CI scenario README and repository docs to describe the new provider-neutral workflow and the `helm-shared` GitHub Actions call pattern.
- External consumer: `riftonix/helm-shared` can use GitHub Actions to select charts under `charts/*` and `libs/*`, then call the released scenario once per chart with its repository source, chart source, OCI registry credentials, and Git credentials.
