## Why

Static documentation sites need a reusable CI path that can validate Hugo builds, publish merge-request previews, and publish the production site after merge. The current Hugo module only performs a build and installs npm dependencies at runtime, which does not match the prepared Hugo Autoprefixer image and does not provide a provider-neutral workflow surface.

## What Changes

- Update the Hugo module contract to use the prepared `ghcr.io/riftonix/container-images/hugo-autoprefixer:0.154.5-10.5.0` image by default.
- Remove runtime npm dependency installation from the normal Hugo build path.
- Add strict Hugo validation/build behavior suitable for CI quality gates, without introducing a full markdown or HTML linting module.
- Add Hugo module operations for creating or preparing reusable Hugo modules without publishing a static site.
- Add Dagger-native tests for the Hugo module so it participates in the existing component test matrix.
- Add a new `scenarios/static-site` scenario that composes a static-site engine for provider-neutral verification and render operations.
- Design `scenarios/static-site` so Hugo is the first engine, while future engines such as Jekyll can be added without replacing the scenario API.
- Keep engine-specific capabilities, such as Hugo module preparation, inside their engine modules instead of making them part of the static-site scenario contract.
- Support a documentation architecture where `docs` and `openspec` are separate Hugo modules imported by the main site with explicit mounts.
- Add Dagger automation so the `docs` and `openspec` modules can be prepared and validated before the main site publishes them.
- Keep GitHub- and GitLab-specific event handling, Pages deployment mechanics, cleanup, comments, tokens, and environment lifecycle in CI provider workflows.

## Capabilities

### New Capabilities

- `hugo-module`: Build and validate Hugo static sites using a prepared Hugo Autoprefixer image.
- `static-site-scenario`: Provide a reusable provider-neutral scenario for static-site verification and rendering.

### Modified Capabilities

None.

## Impact

- Affected code: `modules/hugo`, `modules/hugo/tests`, `scenarios/static-site`, and repository OpenSpec artifacts.
- API impact: the Hugo module defaults change to the prepared GHCR image; runtime npm install behavior is removed from the normal build path.
- CI impact: Hugo tests become eligible for the existing `make tests module hugo` and GitHub Actions component test matrix.
- Provider workflows remain responsible for GitHub Pages or GitLab Pages publication and preview cleanup.
