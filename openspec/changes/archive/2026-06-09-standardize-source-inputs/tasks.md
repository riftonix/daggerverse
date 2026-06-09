## 1. API Audit

- [x] 1.1 Audit public Dagger module and scenario constructors/functions for `dagger.Directory` inputs that represent the primary input tree.
- [x] 1.2 Classify each directory input as either primary `source` or a secondary path/input that keeps a descriptive name.
- [x] 1.3 Record any modules or scenarios that require a breaking public API rename and identify the release tags that consumers will need to upgrade to.

## 2. Static Site Scenario

- [x] 2.1 Update `scenarios/static-site` to store `source: dagger.Directory` on the object through a constructor input named `source`.
- [x] 2.2 Remove function-level `site` directory inputs from `verify_site` and `render_site`.
- [x] 2.3 Update Hugo engine dispatch so verification and rendering use `self.source`.
- [x] 2.4 Expose `hugo_theme_url` as a required public input when `engine=hugo`.
- [x] 2.5 Ensure `validate_hugo_mounts` and `get_hugo_mount_collisions` keep their existing secondary inputs because they do not operate on the primary site source tree.

## 3. Other Modules And Scenarios

- [x] 3.1 Update any audited primary directory inputs outside `scenarios/static-site` that still use specialized names such as `site`, `chart`, or repository-source variants.
- [x] 3.2 Confirm `scenarios/helm-ci` continues to expose primary chart/repository directories as `source`.
- [x] 3.3 Confirm secondary Helm CI inputs such as `charts_path`, `libs_path`, `target_branch`, and `values` keep descriptive names.

## 4. Tests

- [x] 4.1 Update static-site scenario tests to construct the scenario with `source` and call `verify_site`/`render_site` without `site`.
- [x] 4.2 Add or update tests that verify `hugo_theme_url` is required for Hugo-backed operations and passed to the Hugo module.
- [x] 4.3 Add or update tests that exercise the documented public API shape for static-site CLI-equivalent calls.
- [x] 4.4 Adjust any tests affected by primary directory renames in other modules or scenarios.

## 5. Documentation

- [x] 5.1 Update `scenarios/static-site/README.md` with the constructor `source` call shape and migration from `--site` to `--source`.
- [x] 5.2 Update root README, docs how-to guides, and examples so primary input directories use `--source`.
- [x] 5.3 Document the repository-wide `source` convention for new and updated modules/scenarios, including exceptions for secondary paths.
- [x] 5.4 Document that provider-specific CI event, checkout, preview, publication, cleanup, and comment behavior remains outside scenarios.
- [x] 5.5 Document that this is a breaking change and changed scenarios/modules require new release tags.

## 6. Verification

- [x] 6.1 Run `make lint-check scenario static-site`.
- [x] 6.2 Run `make tests scenario static-site`.
- [x] 6.3 Run lint/test targets for any other module or scenario changed by the audit.
- [x] 6.4 Run `openspec validate standardize-source-inputs --strict`.
- [x] 6.5 After implementation and archive, update baseline specs under `openspec/specs/` through the OpenSpec archive workflow.
