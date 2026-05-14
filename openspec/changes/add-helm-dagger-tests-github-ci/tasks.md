# Tasks

## 1. Helm Test Module

- [x] 1.1. Create a Dagger test module under `modules/helm/tests`.
- [x] 1.2. Install the parent Helm module as a local dependency of the test module.
- [x] 1.3. Add a test function that runs Helm lint against the existing fixture chart.
- [x] 1.4. Add a test function that runs Helm template against the existing fixture chart.
- [x] 1.5. Add a test function that packages the existing fixture chart.
- [x] 1.6. Add a test function that pushes the existing fixture chart to a local OCI registry service.
- [x] 1.7. Add a test function that checks the pushed fixture chart version with `is_already_published`.
- [x] 1.8. Add an aggregate test function for CI, for example `all`.

## 2. Dagger Version Alignment

- [x] 2.1. Update affected Dagger module metadata from engine version `v0.19.10` to `v0.20.6`.
- [x] 2.2. Regenerate affected SDK artifacts and lockfiles for Dagger `0.20.6`.
- [x] 2.3. Validate the Helm module still works with Dagger `0.20.6`.

## 3. GitHub Pull Request CI

- [ ] 3.1. Add a GitHub Actions workflow for pull requests targeting the repository default branch.
- [ ] 3.2. Use `dagger/dagger-for-github` with Dagger CLI version `0.20.6`.
- [ ] 3.3. Run the Helm test module aggregate function from CI through `make tests helm`.
- [ ] 3.4. Ensure modules without Dagger test modules are skipped rather than failed.

## 4. Legacy Test Cleanup

- [ ] 4.1. Keep `modules/helm/tests/test.sh` until the Dagger-native tests and CI are implemented and validated.
- [ ] 4.2. Remove `modules/helm/tests/test.sh` after the Dagger-native Helm test module is the canonical test path.

## 5. Documentation And Specs

- [ ] 5.1. Update repository documentation for CI usage, module test conventions, and the root `Makefile` command interface.
- [ ] 5.2. Keep this OpenSpec change aligned with the implementation.
- [ ] 5.3. After implementation, sync accepted behavior, including the root `Makefile` command interface, into `openspec/specs/daggerverse/spec.md`.
- [ ] 5.4. Validate OpenSpec artifacts before archiving the change.
