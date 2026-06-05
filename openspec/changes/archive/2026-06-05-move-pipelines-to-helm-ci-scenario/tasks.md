## 1. Move Component Structure

- [x] 1.1 Move `modules/pipelines` to `scenarios/helm-ci`.
- [x] 1.2 Update `scenarios/helm-ci/dagger.json` name to `helm-ci` and dependency paths to `../../modules/helm` and `../../modules/git`.
- [x] 1.3 Rename the Python package from `pipelines` to `helm_ci` and update `pyproject.toml` project metadata.
- [x] 1.4 Rename the public Dagger object from `Pipelines` to `HelmCi` so generated callers use `dag.helm_ci()`.
- [x] 1.5 Preserve existing public functions and behavior for `helm-verify`, `helm-publish`, and `helm-verify-changed-charts`.

## 2. Move And Update Tests

- [x] 2.1 Move the neighboring test module to `scenarios/helm-ci/tests`.
- [x] 2.2 Update test `dagger.json` to depend on `helm-ci` through the local parent scenario.
- [x] 2.3 Update test code and helper names from `pipelines` to `helm-ci` / `helm_ci`.
- [x] 2.4 Keep the changed-chart merge-base test covering feature-branch changes without base-branch drift.
- [x] 2.5 Remove or replace the legacy shell test script if it still references `modules/pipelines` or raw local Dagger calls.

## 3. Update Documentation

- [x] 3.1 Update the root README so `pipelines` is removed from modules and `helm-ci` is listed under scenarios.
- [x] 3.2 Rewrite the Helm CI how-to page to use `scenarios/helm-ci` and remove transitional module wording.
- [x] 3.3 Update Helm tutorial examples to call `dagger -m ./scenarios/helm-ci`.
- [x] 3.4 Update module and repository reference pages so Helm CI orchestration is documented as a scenario, not as `modules/pipelines`.
- [x] 3.5 Search repository docs and OpenSpec current specs for active `modules/pipelines` or `pipelines` references and rewrite or remove them where they describe current behavior.

## 4. Validate

- [x] 4.1 Run `make lint-check scenario helm-ci`.
- [x] 4.2 Run `make format-check scenario helm-ci`.
- [x] 4.3 Run `make tests scenario helm-ci`.
- [x] 4.4 Run `make check-dagger-version`.
- [x] 4.5 Run `openspec validate --all --strict`.
