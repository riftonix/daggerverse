## 1. Hugo Module And Tests

- [x] 1.1 Update `modules/hugo` default image parameters to `ghcr.io/riftonix/container-images/hugo-autoprefixer:0.154.5-10.5.0`.
- [x] 1.2 Remove runtime `npm config set registry` and `npm install autoprefixer` from the normal Hugo build path and add a test that the Docsy fixture builds with the prepared image.
- [x] 1.3 Add strict Hugo validation behavior using Hugo build/config commands and warning/path check flags and add a test that the Docsy fixture passes validation.
- [x] 1.4 Keep build output as a `dagger.Directory` rendered with caller-provided `site_base_url` and add a test that rendered output exists.
- [x] 1.5 Add Hugo module preparation operations for initialization/dependency resolution without static-site publication and add tests for module preparation.
- [x] 1.6 Add tests or fixtures showing that content-only Hugo modules can stay path-neutral while an importing site chooses the content mount target.
- [x] 1.7 Add tests or fixtures showing that independent `docs` and `openspec` Hugo module roots can be prepared separately.
- [x] 1.8 Add `modules/hugo/tests/dagger.json` and Python test module structure consistent with existing component tests.
- [x] 1.9 Remove or demote the legacy shell smoke test if it becomes redundant.

## 2. Static Site Scenario And Tests

- [ ] 2.1 Create `scenarios/static-site` Dagger scenario structure with dependency on `modules/hugo`.
- [ ] 2.2 Implement provider-neutral engine selection with Hugo as the first supported engine, keep the scenario API limited to common render/verify operations, and add a test that unsupported engines fail clearly.
- [ ] 2.3 Implement a provider-neutral verification function that accepts a site directory, explicit `site_base_url`, and selected engine, then add a test that verifies the Docsy fixture.
- [ ] 2.4 Implement a provider-neutral render function that returns the rendered static-site directory for the selected engine, then add a test that rendered output exists.
- [ ] 2.5 Add Dagger automation/test fixtures for a main Hugo site that imports `daggerverse/docs` at `content/docs/components/daggerverse`, `container-images/docs` at `content/docs/components/container-images`, and both OpenSpec modules at `content/docs/specs` plus `content/docs/changes/archive`.
- [ ] 2.6 Add validation for duplicate virtual paths when multiple OpenSpec modules merge into shared specs or changes archive targets, with tests for unique and duplicate paths.
- [ ] 2.7 Add `scenarios/static-site/tests/dagger.json` and Python test module structure.

## 3. Documentation

- [ ] 3.1 Update `modules/hugo/README.md` to document the prepared image, strict validation, Hugo module preparation, content-only module path neutrality, and provider-neutral build usage.
- [ ] 3.2 Add `scenarios/static-site/README.md` documenting engine selection, Hugo usage, extension path for future engines, provider workflow boundaries, and the rule that engine-specific capabilities such as Hugo module preparation stay in engine modules.
- [ ] 3.3 Document the recommended `docs` Hugo module layout with `README.md`, `go.mod`, and Hugo content under `docs/content`.
- [ ] 3.4 Document the recommended `openspec` Hugo module layout with `go.mod`, OpenSpec-owned files unchanged, and optional sidecar `_index.md` files for Docsy navigation.
- [ ] 3.5 Document the main-site import and mount layout for multiple component `docs` and `openspec` modules, including example resulting URLs.
- [ ] 3.6 Document OpenSpec virtual path collision rules for shared `content/docs/specs` and `content/docs/changes/archive` targets.
- [ ] 3.7 Document that GitHub/GitLab event handling, Pages publication, preview cleanup, comments, tokens, and environments remain in CI workflows.

## 4. Verification

- [ ] 4.1 Run `make lint-check module hugo`, `make tests module hugo`, `make lint-check scenario static-site`, `make tests scenario static-site`, and `openspec validate add-static-site-scenario --strict`.
