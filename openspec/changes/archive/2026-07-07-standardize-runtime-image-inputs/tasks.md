## 1. Runtime Image API Audit

- [x] 1.1 Audit all public module and scenario constructors/functions for runtime tool image inputs.
- [x] 1.2 Classify each image-related input as runtime image selection, build/publish image metadata, registry authentication, or unrelated version input.
- [x] 1.3 Audit Dagger test module public entrypoints and helper service image inputs for convention drift.
- [x] 1.4 Record released modules/scenarios that require breaking public API changes and the tags consumers must upgrade from.

## 2. Static Site Scenario And Tests

- [x] 2.1 Add `hugo_image_registry`, `hugo_image_repository`, `hugo_image_tag`, and `hugo_container_user_id` constructor inputs to `scenarios/static-site`, store them on the object, and pass them to the Hugo module for `verify_site` and `render_site`.
- [x] 2.2 Update static-site scenario tests in the same change so Hugo runtime image overrides are accepted through the aggregate `all()` path.
- [x] 2.3 Add optional constructor-level Hugo runtime image overrides to `scenarios/static-site/tests` for offline or mirrored-registry runs.
- [x] 2.4 Keep `hugo_theme_url` as Hugo theme configuration and keep `source` as the primary site tree.
- [x] 2.5 Keep direct Hugo module integration tests in `modules/hugo/tests` so static-site tests do not bypass scenario runtime image overrides.

## 3. Helm CI Scenario And Tests

- [x] 3.1 Add Helm runtime image inputs with `helm_` prefixes and Git runtime image inputs with `git_` prefixes to `scenarios/helm-ci`.
- [x] 3.2 Store or otherwise carry Helm and Git runtime image inputs through scenario calls, pass Helm inputs to chart verify/publish operations, and pass Git inputs to changed-chart operations.
- [x] 3.3 Update Helm CI scenario tests in the same change so Helm and Git runtime image overrides are accepted through the aggregate `all()` path.
- [x] 3.4 Add optional constructor-level Helm/Git runtime image overrides to `scenarios/helm-ci/tests` for offline or mirrored-registry runs.
- [x] 3.5 Confirm single-chart verify/publish operations do not invoke the Git module.

## 4. OpenTofu Module And Tests

- [x] 4.1 Replace `container_image` with `image_registry`, `image_repository`, `image_tag`, and `user_id` in `modules/opentofu`, and build the image reference internally from split image inputs.
- [x] 4.2 Preserve `executor` as a separate IaC command input.
- [x] 4.3 Add OpenTofu module tests verifying the executor input selects the IaC command without changing image identity, using the default runtime image so the test runs against a pullable image.
- [x] 4.4 Update OpenTofu README and examples to document the breaking migration from `container_image`.

## 5. Documentation, Renovate, And Examples

- [x] 5.1 Document the runtime image input convention in repository reference docs.
- [x] 5.2 Document the multi-tool scenario prefix rule and Docker build metadata exceptions.
- [x] 5.3 Document that default image versions may remain as constructor literals when Renovate can track every duplicate occurrence.
- [x] 5.4 Document Renovate synchronization for duplicated runtime image defaults using the same dependency identity, datasource, versioning, and full-tag update behavior.
- [x] 5.5 Document that Hugo `module.hugoVersion.min` should use the same Docker datasource and `extractVersion` rule as `container-images` (`hugomods/hugo:exts-*`) when it is coupled to the runtime builder.
- [x] 5.6 Update module and scenario READMEs for static-site, helm-ci, hugo, and opentofu.
- [x] 5.7 Update CLI examples to show explicit image pins where reproducibility matters.
- [x] 5.8 Document that changed released modules/scenarios require new release tags.

## 6. Test Module Convention

- [x] 6.1 Normalize test module aggregate entrypoints to `all()` without public inputs unless an exception is documented; for `modules/git/tests`, replace `all(source)` with a no-argument aggregate and use a synthetic Git repository fixture for metadata SHA checks.
- [x] 6.2 Confirm test helper service image inputs use purpose-prefixed names such as `registry_image_*`.
- [x] 6.3 Ensure test module runtime image defaults stay synchronized with tested module or scenario defaults through Renovate-managed duplicates, shared constants, pass-through construction, or explicit assertions.
- [x] 6.4 Add constructor-level Hugo runtime image overrides to `modules/hugo/tests` and use them for direct Hugo module calls.

## 7. User-Run Verification

- [x] 7.1 Hand off `make format-check` for the user to run.
- [x] 7.2 Hand off `make lint-check scenario static-site`, `make lint-check scenario helm-ci`, and `make lint-check module opentofu` for the user to run.
- [x] 7.3 Hand off `make tests scenario static-site` and `make tests scenario helm-ci` for the user to run.
- [x] 7.4 Hand off OpenTofu module tests for the user to run if a test module exists, or document the gap if it does not.
- [x] 7.5 Hand off `openspec validate standardize-runtime-image-inputs --strict` for the user to run.

## 8. Archive

- [x] 8.1 After implementation, archive the change and update baseline specs under `openspec/specs/`.
