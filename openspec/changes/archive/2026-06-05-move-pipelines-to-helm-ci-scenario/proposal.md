## Why

The current `modules/pipelines` component is a transitional Helm CI wrapper, but repository architecture now treats ready-to-run CI workflows as scenarios under `scenarios/`. The component has not been published or adopted externally, so this is the right time to move it before the old module path becomes a public contract.

## What Changes

- **BREAKING**: Remove the transitional `modules/pipelines` Dagger component and its `pipelines` module name.
- Add `scenarios/helm-ci` as the Helm CI scenario that composes the existing `modules/helm` and `modules/git` modules.
- Preserve the existing Helm workflow functions under the new scenario:
  - `helm-verify`
  - `helm-publish`
  - `helm-verify-changed-charts`
- Move the neighboring Dagger-native tests to `scenarios/helm-ci/tests` and update them to call the scenario through `dag.helm_ci()`.
- Update documentation and examples to use `dagger -m ./scenarios/helm-ci ...` and `make tests scenario helm-ci`.
- Remove transitional wording that presents `modules/pipelines` as the current Helm orchestration entrypoint.

## Capabilities

### New Capabilities
- `helm-ci-scenario`: Defines the portable Helm CI scenario, its public workflow functions, documentation, and Dagger-native tests.

### Modified Capabilities
- `daggerverse`: Update repository layout and documentation requirements so Helm CI orchestration is located under `scenarios/helm-ci` rather than the transitional `modules/pipelines` module.

## Impact

- Affected code: `modules/pipelines`, `scenarios/helm-ci`, scenario test metadata, Python package/module names, and local Dagger dependencies.
- Affected docs: root README, Helm tutorial/how-to pages, module/scenario reference pages, repository layout and architecture explanations.
- Affected commands: callers must use `dagger -m ./scenarios/helm-ci ...` and `make tests scenario helm-ci`; old `./modules/pipelines` commands will no longer work.
- CI impact: no expected workflow logic changes, because repository CI and publishing already discover scenarios under `scenarios/<name>`.
