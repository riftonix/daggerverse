## Why

Runtime container image versions are currently declared inconsistently across Dagger modules, scenarios, and tests. Some images use module-level constants while others are inline default arguments, which makes Renovate updates fragile and makes it harder to keep module and scenario defaults in sync.

This change introduces a consistent, code-local convention for Renovate-managed image tags so the same image can be updated across modules, scenarios, and tests in one MR.

## What Changes

- Add a repository convention for declaring runtime images as `*_IMAGE_REGISTRY`, `*_IMAGE_REPOSITORY`, and `*_IMAGE_TAG` constants in existing and new modules, scenarios, and tests.
- Require a Renovate annotation comment immediately before every Renovate-managed `*_IMAGE_TAG` constant.
- Move inline runtime image defaults in modules and scenarios into constants.
- Move additional test-only runtime images into constants when they are currently inline function defaults.
- Update `renovate.json` with a Python regex custom manager that reads the annotation comment and updates the following `*_IMAGE_TAG` value.
- Keep related module, scenario, and test image updates in the same MR by using the same `datasource` and `depName` in their Renovate annotations.

## Capabilities

### New Capabilities

- `renovate-managed-runtime-images`: Runtime container image defaults in existing and new Dagger modules, scenarios, and tests are discoverable and updateable by Renovate from code-local annotations.

### Modified Capabilities

None.

## Impact

- Affects Python source files under `modules/*/src`, `modules/*/tests`, `scenarios/*/src`, and `scenarios/*/tests` that declare runtime image defaults.
- Affects future module and scenario authoring conventions for runtime image defaults.
- Affects `renovate.json` by adding a custom regex manager for annotated Python image tag constants.
- Does not change public runtime behavior or Dagger function signatures except replacing inline default literals with equivalent constants.
- Enables Renovate MRs for images such as `alpine/helm`, `alpine/git`, `helmunittest/helm-unittest`, `ghcr.io/riftonix/container-images/hugo-autoprefixer`, `ghcr.io/opentofu/opentofu`, `kroniak/ssh-client`, and `registry`.
