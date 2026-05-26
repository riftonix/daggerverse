## Why

The Daggerverse needs a reusable, Dagger-native foundation for CI pipelines that build and publish container images from a container-images monorepo. The implementation should keep Docker/OCI primitives reusable while providing a portable scenario that CI systems can call with explicit inputs.

## What Changes

- Add a reusable `modules/docker` Dagger module for container image build, registry auth, publish, platform-aware builds, build arguments, and optional smoke checks.
- Add a portable `scenarios/container-images` Dagger scenario that verifies and publishes one or more image contexts using explicit parameters.
- Extend repository CI and release workflows so scenarios are discovered, tested, and published similarly to modules.
- Update the root command interface to address modules and scenarios explicitly, such as `make tests module docker` and `make tests scenario container-images`, and remove legacy module-only shorthand commands.
- Move the shared Ruff configuration out of `modules/` so linting and formatting apply consistently to both `modules/` and `scenarios/`.
- Keep CI-provider policy outside the scenario: GitHub Actions, GitLab CI, or another runner decides when to run, which contexts changed, how tags map to image references, and which registry references to publish.
- Use OCI registry semantics for publication so `ghcr.io` works as a normal registry endpoint without GHCR-specific module behavior.
- Add Dagger-native tests and documentation for the new module and scenario.

## Capabilities

### New Capabilities
- `docker-module`: Reusable Docker/OCI image build, login, publish, and smoke-check primitives.
- `container-images-scenario`: Portable CI scenario for verifying and publishing container image contexts through explicit inputs.

### Modified Capabilities
- `daggerverse`: Document the new module and scenario layout in the repository-level docs.

## Impact

- Adds `modules/docker` with Python Dagger SDK implementation, README, and neighboring Dagger test module.
- Adds `scenarios/container-images` with Python Dagger SDK implementation and README.
- Updates repository documentation to describe the new module, scenario, and CI usage pattern.
- Updates the root command interface and GitHub workflows so scenarios can have Dagger-native tests and can be published on branch pushes or scenario release tags.
- Updates lint and format commands so no-argument runs cover both reusable modules and scenarios.
- Does not require new CI-provider-specific modules on the first stage.
- Does not require a GHCR-specific module because GHCR can be addressed as an ordinary OCI registry.
- Does not modify the existing Helm module.
