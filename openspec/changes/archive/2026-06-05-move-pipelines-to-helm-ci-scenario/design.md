## Context

`modules/pipelines` currently composes the local Helm and Git modules into Helm-oriented CI workflows. Repository architecture now separates reusable tool primitives under `modules/` from ready-to-run CI workflows under `scenarios/`, and existing documentation already marks `modules/pipelines` as transitional.

The component has not been published or adopted by external callers, so the migration can be a direct rename and move rather than a compatibility-preserving deprecation. The new scenario name is `helm-ci`.

## Goals / Non-Goals

**Goals:**
- Move the Helm CI orchestration entrypoint from `modules/pipelines` to `scenarios/helm-ci`.
- Rename Dagger and Python identifiers so callers use `dag.helm_ci()` and `dagger -m ./scenarios/helm-ci`.
- Keep the existing Helm CI workflow functions and their behavior intact.
- Keep tests as a neighboring Dagger test module under the scenario.
- Update docs and OpenSpec current-state expectations so `modules/pipelines` is no longer presented as an active component.

**Non-Goals:**
- Add CI-provider-specific event parsing or workflow policy.
- Expand the Helm workflow API beyond the existing verification, changed-chart verification, and publication functions.
- Preserve a compatibility alias for `modules/pipelines` or `dag.pipelines()`.
- Publish both old and new component names.

## Decisions

1. Move directly to `scenarios/helm-ci` without a compatibility shim.

   The old component is unpublished and unused, so keeping `modules/pipelines` around would preserve a boundary the repository has already decided is wrong. A direct move keeps the repository layout simple and prevents two public entrypoints from drifting.

   Alternative considered: keep `modules/pipelines` as a wrapper around the new scenario. This was rejected because modules must remain reusable tool boundaries, and a wrapper would continue advertising a ready-to-run CI workflow as a module.

2. Use `helm-ci` as the Dagger module name and `helm_ci` as the Python package/object accessor shape.

   Dagger module names commonly use kebab-case in `dagger.json`, while Python package names use underscores. The public Dagger call path becomes `dag.helm_ci()` in test code and generated clients.

   Alternative considered: `helm-shared`. This was rejected because `shared` sounds like a reusable module, while the component is a CI scenario.

3. Preserve current function names and behavior.

   Existing function names already describe Helm workflow actions clearly. The migration should change location and component identity, not the caller's function-level workflow model.

   Alternative considered: shorten function names by dropping the `helm_` prefix inside the `helm-ci` scenario. This was rejected for this change because it would add an unnecessary API rename on top of the component move.

4. Keep Git diff policy provider-neutral.

   `helm_verify_changed_charts` can continue to use the Git module for merge-base changed directories, but the scenario must not inspect GitHub Actions, GitLab CI, or other provider event variables. CI workflows remain responsible for passing explicit branch/path inputs.

## Risks / Trade-offs

- Breaking local command paths -> Update all repository docs and tests in the same implementation step.
- Generated Dagger SDK state may become stale after moving metadata -> Run the scenario tests through `make tests scenario helm-ci`, which forces Dagger to resolve the moved local dependencies.
- Documentation may retain references to `modules/pipelines` -> Search for `pipelines` and `modules/pipelines` after implementation and remove or rewrite active usage references.
- Scenario name could collide with future provider-specific Helm workflows -> Keep this scenario provider-neutral and reserve provider-specific wrappers for separate future scenarios or CI workflow files.

## Migration Plan

1. Move the component directory and rename Dagger/Python identifiers.
2. Update local dependency paths from the scenario location.
3. Move and update the Dagger test module.
4. Rewrite docs and examples to use `scenarios/helm-ci`.
5. Run focused lint and tests for `scenario helm-ci`, plus repository checks that validate Dagger metadata and OpenSpec artifacts.

Rollback is straightforward before publication: move the directory and identifiers back to `modules/pipelines`. After publication, rollback would require a deliberate decision about whether to retire or supersede the published scenario name.

## Open Questions

None.
