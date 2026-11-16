# Tasks

Commands that run Dagger functions or containers (`make tests ...`, `dagger call ...`, `dagger develop`) need explicit approval from the repository owner before each run. `make lint-check`, `make format-check`, and `make openspec-validate` do not.

## 1. Configuration Format 2

- [ ] 1.1 Rewrite `load_config` in `scenarios/helm-ci/src/helm_ci/chart_sync.py` for format `2`:
  - the `version: 2` check, reported alone when it fails;
  - allowed keys per location, as in the design table;
  - `registries` with `url` and `plainhttp`, `defaults.registry`, and component `registry`;
  - `defaults` with `path` and `upstream` templates (`${id}` only), `versionfilter`, `exclude`, and `vendored`, and the component overrides;
  - the upstream chart name fallback to the component ID, and the required path and version filter;
  - component paths at any depth, with symbolic link, file prefix, and overlap checks;
  - the `pins` directory, defaulting to the configuration directory;
  - removal of `upstream`, `home`, and the `charts`/`libs` rule.

  Verify with `make lint-check scenario helm-ci`.
- [ ] 1.2 Replace `VENDORED` with the resolved vendored paths of each component, defaulting to `charts` and `Chart.lock`. Verify with `make lint-check scenario helm-ci`.
- [ ] 1.3 Migrate `scenarios/helm-ci/tests/fixtures/fork/updatecli/values.yaml` to format `2`, with explicit `scope: all` rules that keep the current rewrite expectations. Update the validation tests in `tests/src/tests/sync_charts.py` for:
  - the format `1` rejection;
  - unknown keys;
  - missing registry, path, and version filter;
  - invalid and undeclared registries;
  - unsafe and overlapping paths;
  - a pin without a directory;
  - nested paths and a custom pin directory;
  - custom and empty `vendored` lists.

  Verify with `make lint-check scenario helm-ci` and, with approval, `make tests scenario helm-ci`.

## 2. Rewrite Rules and Placeholders

- [ ] 2.1 Implement placeholder parsing and validation (`${id}`, `${upstream}`, `${path}`, `${registry}`, and `$${`), the `scope` key with `current` and `all`, and the expansion in `rules()` with field-specific escaping. Remove the built-in GitHub URL and chart name rules. Verify with `make lint-check scenario helm-ci`.
- [ ] 2.2 Add tests for:
  - no implicit rewrites;
  - `scope: all` and the default scope;
  - literal matching of placeholders in `regex` rules;
  - the `$${` escape;
  - unsupported placeholders.

  Add them to `all()`. Verify, with approval, with `make tests scenario helm-ci`.

## 3. Named Registries

- [ ] 3.1 Pass the component registry to `list_tags` and `pull`, including `plainhttp` per registry. Push fixture charts to two projects of the local `registry:3` service, declare them as two registry entries, and add a test that synchronizes components from both. Add it to `all()`. Verify with `make lint-check scenario helm-ci` and, with approval, `make tests scenario helm-ci`.

## 4. Initial Import

- [ ] 4.1 Mark components without a directory and a pin for import, and implement the import path of `synchronize`:
  - empty base and ours trees;
  - no version-collision check;
  - a failure on an empty result;
  - the `import` report line;
  - creation of the pin directory on apply.

  Verify with `make lint-check scenario helm-ci`.
- [ ] 4.2 Add tests for:
  - the import preview without writes;
  - a local import that writes only the component directory and the new pin;
  - an import into a missing pin directory;
  - a failed import that creates nothing;
  - the rendered manifest of an import component.

  Add them to `all()`. Verify, with approval, with `make tests scenario helm-ci`.

## 5. Documentation

- [ ] 5.1 Update the chart sync section of `scenarios/helm-ci/README.md` for format `2`:
  - every key and its default;
  - placeholders and rule scopes;
  - named registries;
  - vendored paths and the pin directory;
  - imports;
  - a format `1` to format `2` migration example.

  Verify that the README examples validate against the implemented helper in the tests, that the relative links resolve, and that there are no em or en dashes.

## 6. Integration Verification

- [ ] 6.1 Run `make lint-check scenario helm-ci`, `make format-check scenario helm-ci`, and `make openspec-validate`, and verify that they pass.
- [ ] 6.2 With approval, run `make tests scenario helm-ci` and verify that `Tests.all` passes.
- [ ] 6.3 With approval, run `sync-charts-diff` from the local scenario against a temporary copy of a `helm-shared` checkout with `updatecli/values.yaml` migrated to format `2`, and verify that the report matches the `scenarios/helm-ci/v1.4.0` report for the unmigrated checkout.

## Workflow follow-up

- Release a new version of `scenarios/helm-ci` with `make release scenarios/helm-ci/vX.Y.Z` from `master`.
- In the `helm-shared` integration, migrate `updatecli/values.yaml` to format `2` together with the scenario workflow, and verify the first import pull request, if any, before relying on imports.
- Archive the change after implementation and review, then update `docs/` per the archived change.
