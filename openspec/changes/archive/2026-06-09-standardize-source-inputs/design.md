## Context

The repository already uses constructor-style primary directory inputs in several reusable modules. `modules/helm` exposes `Helm.create(source: dagger.Directory, ...)`, and callers use `dagger -m ./modules/helm call --source=<chart-dir> lint`. The Git and Hugo modules also model their primary directory as `source`.

The static-site scenario currently differs from that pattern: `verify_site` and `render_site` accept a function-level `site` directory. That makes CI calls look different from Helm and other repository examples, for example `--site="$SITE_DIR"` instead of a common `--source="$SITE_DIR"` constructor argument. This is a small API difference, but it leaks into every provider workflow and README example.

The standardization should stay about naming the primary input tree. It must not pull provider-specific CI concerns into scenarios. A GitHub Actions or GitLab CI workflow still owns checkout depth, event selection, branch/ref policy, preview URL construction, Pages publication, deployment cleanup, and comments. `source` only tells the Dagger module or scenario which directory tree to operate on.

## Goals / Non-Goals

**Goals:**

- Establish `source` as the repository-wide public name for the primary input directory in new and updated modules and scenarios.
- Update `scenarios/static-site` to use a constructor `source` and remove function-level `site` directory parameters from `verify_site` and `render_site`.
- Keep the static-site CLI shape aligned with object construction, including `dagger -m <static-site> call --source=<dir> --hugo-theme-url=<module-ref> verify-site --site-base-url=... --engine=hugo`.
- Require Hugo callers to provide `hugo_theme_url` explicitly instead of relying on a hardcoded `DEFAULT_THEME_URL`.
- Audit existing modules and scenarios for primary directory inputs and update any outliers.
- Update documentation, examples, and tests so the public API shape is enforced.
- Document migration for breaking CLI callers and require new tags for changed released modules or scenarios.

**Non-Goals:**

- Preserve backward-compatible aliases such as `site`.
- Rename secondary paths or values that are not the primary input directory, such as `values`, `charts_path`, `libs_path`, `context_path`, `dockerfile_path`, registry URLs, output directories, target branches, or chart paths inside a repository.
- Change provider workflow policy or move GitHub/GitLab event handling into Dagger scenarios.
- Update baseline specs in this proposal-only change; baseline specs are updated after implementation and archive.

## Decisions

1. Use `source` only for the primary input tree.

   The convention applies when a directory represents the main project, chart, site, repository checkout, or module source being operated on. Secondary inputs keep descriptive names. This avoids overloading `source` for every path-like option and preserves clarity for cases such as Helm `values`, Docker `dockerfile_path`, or Helm CI `charts_path`.

2. Prefer constructor `source` for object APIs.

   Modules and scenarios that keep state around a primary directory should accept that directory in `create(source: dagger.Directory, ...)` and store it on the object. Functions then operate on `self.source`. This matches the Helm and Hugo modules and gives CLI users the stable shape `call --source=<dir> <function> ...`.

3. Make `scenarios/static-site` an object API.

   `StaticSite.create(source, hugo_theme_url=...)` should accept the source tree once and require the Hugo theme module reference when callers use `engine=hugo`. `verify_site` and `render_site` should keep only operation-specific inputs such as `site_base_url` and `engine`. Internally, Hugo dispatch uses `dag.hugo(source=self.source)` so the selected engine sees the same tree the scenario was constructed with.

4. Treat `hugo_theme_url` as required Hugo engine configuration, not a constant.

   A hardcoded `DEFAULT_THEME_URL` is too rigid for downstream sites and would become confusing when additional engines such as Jekyll or Zola are added. The constructor should expose a documented `hugo_theme_url` argument and Hugo-backed verification/rendering should reject empty or missing values when `engine=hugo`. Future engines can add their own clearly named configuration inputs without inheriting a Hugo-specific default.

5. Make the migration intentionally breaking.

   The repository is still standardizing public scenario contracts. Keeping aliases such as `site` would double the documented API and make examples less consistent. Consumers should migrate to the new tag and replace `--site=<dir>` with `--source=<dir>`.

6. Verify the API through tests and documentation examples.

   Dagger-native scenario tests should call the public API in the new form. Documentation should show realistic local and remote module calls, including the static-site example with `--source="$PWD"` and provider-computed `--site-base-url`.

## API Audit Results

Audited public Dagger module and scenario constructors/functions with `dagger.Directory` inputs:

| Component | Public input | Classification | Follow-up |
| --- | --- | --- | --- |
| `modules/git` | constructor `source` | Primary repository source tree | Already follows convention. |
| `modules/helm` | constructor `source` | Primary Helm chart source tree | Already follows convention. |
| `modules/hugo` | constructor `source` | Primary Hugo site source tree | Already follows convention. |
| `modules/docker` | `build`, `build_from_bake`, and `resolve_bake_target` `source` | Primary build context / Bake source tree | Already follows convention; `context_path`, `dockerfile_path`, `bake_path`, and `variable_overrides` remain secondary descriptive inputs. |
| `modules/opentofu` | `lint` `source` | Primary IaC project source tree | Already follows convention. |
| `scenarios/container-images` | verify/publish functions `source` | Primary repository or image build source tree | Already follows convention; context, Dockerfile, Bake, target, registry, and publish spec inputs remain secondary descriptive inputs. |
| `scenarios/helm-ci` | `helm_verify`, `helm_publish`, and `helm_verify_changed_charts` `source` | Primary chart directory or repository checkout | Already follows convention; `values`, `charts_path`, `libs_path`, `target_branch`, release, version, and registry inputs remain secondary descriptive inputs. |
| `scenarios/static-site` | `verify_site` and `render_site` `site` | Primary static site source tree | Breaking rename required: move to constructor `source` and remove function-level `site`. |
| `scenarios/static-site` | `validate_hugo_mounts` and `get_hugo_mount_collisions` `modules` | Secondary imported Hugo module roots used with a config file | Keep descriptive name; not the scenario primary site source tree. |

Breaking public API impact:

- `scenarios/static-site` currently has release tag `scenarios/static-site/v0.1.0`. Consumers upgrading to the next static-site scenario tag must replace function-level `--site=<dir>` calls with constructor `--source=<dir>` calls.
- No other audited released module requires a primary `dagger.Directory` rename for this change. Existing released tags observed during the audit were `modules/docker/v0.1.0`, `modules/docker/v0.1.1`, `modules/docker/v0.1.2`, `modules/git/v1.0.0`, `modules/git/v1.0.1`, `modules/helm/v1.3.1`, and `modules/hugo/v0.2.0`; their public primary directory inputs already use `source`.

## Risks / Trade-offs

- Existing CI callers break when upgrading to the new static-site scenario tag -> Document the exact `--site` to `--source` migration and require a new scenario tag for the breaking release.
- Constructor parameters can make function examples look different from old commands -> Use one consistent example shape across READMEs and docs so users learn it once.
- Over-standardizing could make secondary paths less clear -> Limit `source` to the primary input tree and explicitly document exceptions for additional inputs.
- Static-site theme configuration could become Hugo-specific leakage -> Keep it as a clearly named Hugo-specific required input for Hugo operations while the common operations remain engine-neutral.
- Provider responsibilities could be misunderstood as part of `source` -> Repeat in scenario docs that `source` is an input tree only, not checkout or event policy.

## Migration Plan

1. Implement the static-site constructor and remove `site` parameters from `verify_site` and `render_site`.
2. Replace internal static-site Hugo calls with `self.source` and required constructor-configured `hugo_theme_url` for Hugo operations.
3. Audit modules and scenarios for any other public primary directory inputs that do not use `source`; rename only true primary input trees.
4. Update tests to call public APIs with constructor `source` and to cover required `hugo_theme_url` behavior for Hugo operations.
5. Update READMEs, how-to guides, root examples, and CI snippets from specialized primary directory names to `--source`.
6. Run component lint/tests and `openspec validate standardize-source-inputs --strict`.
7. Release changed modules or scenarios with new tags. Consumers migrate by updating the tag and changing CLI calls such as `--site="$SITE_DIR"` to `--source="$SITE_DIR"`.

Rollback is tag-based: consumers that cannot migrate stay on the previous static-site scenario tag until their workflows are updated.

## Open Questions

None.
