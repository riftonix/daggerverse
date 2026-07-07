## Context

The repository already has an implicit runtime image pattern. `modules/git`, `modules/helm`, `modules/hugo`, `modules/kind`, and `modules/ssh` expose image selection as `image_registry`, `image_repository`, `image_tag`, and `user_id`. This lets callers pin the exact tool runtime without parsing or rewriting a combined image reference.

The pattern is not applied consistently. `modules/opentofu` accepts a combined `container_image`, while scenarios that compose image-backed modules often rely on the module defaults and do not expose runtime image inputs. That hides the actual image tag from CI workflows and makes Renovate coordination difficult. The static-site workflow issue is the concrete example: Hugo site configuration can be raised to a version that is newer than the hidden Hugo runtime image used by the scenario.

The previous source-input standardization established that `source` is the primary input tree and provider CI policy stays outside scenarios. This change extends the same public API discipline to runtime tool images.

## Goals / Non-Goals

**Goals:**

- Standardize image-backed module and scenario public APIs on `image_registry`, `image_repository`, `image_tag`, and `user_id`.
- Require scenarios to expose runtime image inputs for image-backed modules they compose.
- Use tool-specific prefixes when a scenario composes more than one image-backed tool.
- Update `scenarios/static-site` to expose Hugo runtime image inputs and pass them to `dag.hugo`.
- Update `scenarios/helm-ci` to expose Helm and Git runtime image inputs and pass them to `dag.helm` and `dag.git`.
- Update `modules/opentofu` to use standard split image inputs while preserving the `executor` input.
- Document the rule for future modules and scenarios so new code does not reintroduce combined or hidden image inputs.
- Document Renovate-based version synchronization for duplicated runtime image defaults and derived site configuration such as Hugo minimum version.
- Update tests and docs to enforce the public API shape.

**Non-Goals:**

- Introduce a shared Python base class or inheritance hierarchy for Dagger objects.
- Require constants for default image versions when a constructor literal is clearer and Renovate can track the literal directly.
- Rename Docker build metadata such as `image_ref`, `image_refs`, `tags`, `context_path`, `dockerfile_path`, or Bake variables.
- Move CI-provider event, checkout, preview, publication, cleanup, or comment policy into scenarios.
- Change the default image versions except where required by existing constants or tests.
- Make every scenario accept image inputs when it does not run a fixed runtime tool image.

## Decisions

1. Use split image inputs for runtime tool images.

   Public APIs that select the container used to run a tool should accept `image_registry`, `image_repository`, `image_tag`, and `user_id`. Splitting the image reference keeps registry moves, repository moves, and tag updates separately addressable by callers and Renovate. A combined `container_image` hides those fields and makes partial override awkward.

2. Prefix image inputs in multi-tool scenarios.

   A scenario that composes multiple image-backed modules should name each input set after the tool or engine it configures, for example `helm_image_tag`, `git_image_tag`, or `hugo_image_tag`. This avoids ambiguous scenario constructors such as one `image_tag` that might configure only one of several tools.

3. Keep generic names for single-tool modules.

   Reusable modules that directly wrap one tool keep generic names: `image_registry`, `image_repository`, `image_tag`, and `user_id`. This matches the existing Git, Helm, Hugo, Kind, and SSH modules.

4. Keep Docker build output references separate from runtime image inputs.

   Docker and container image APIs use `image_ref`, `image_refs`, `tags`, Bake `variable_overrides`, and registry auth for images being built or published. Those are output/build metadata, not the runtime container image used to execute a tool. They should not be renamed to the runtime image input convention.

5. Treat `modules/opentofu` as a breaking API migration.

   `container_image` should be replaced by `image_registry`, `image_repository`, and `image_tag`. `executor` remains separate because it chooses the command inside the selected image (`tofu` or compatible alternatives), not the image identity. Consumers that need the old combined input can stay on the old tag until they migrate.

6. Make scenario image pins visible to CI.

   Static-site CI should be able to pass `hugo_image_tag`, and Helm CI should be able to pass Helm/Git image tags. This lets downstream repositories synchronize configuration such as `hugo.yml` `module.hugoVersion.min` with the image that actually builds the site.

7. Keep test module entrypoints predictable.

   Dagger test modules should expose `module()` and a no-argument aggregate `all()` by default, because repository CI can call the same aggregate function for every component. Tests should use `dag.current_module().source()` for fixtures and only accept a public `source` input when the test is explicitly intended to run against an external caller-provided tree. Helper service images exposed by tests should follow the same prefixed image input rule, for example `registry_image_tag` for a local registry service used by Helm tests.

8. Allow optional test runtime image overrides for offline runs.

   Test modules should be runnable in environments without direct internet access when required images are mirrored into a local registry. To support that, image-backed test modules may expose optional constructor-level runtime image inputs for the tested module and helper services, including container user fields when the underlying runtime supports them. Multi-tool scenarios use purpose-prefixed names such as `hugo_container_user_id`, `helm_container_user_id`, and `git_container_user_id` for these user fields. The aggregate `all()` remains no-argument; offline callers configure image overrides once on the test object before invoking `all()`.

9. Keep tested-component defaults as the synchronization source.

   Test module defaults should match the tested module or scenario defaults by importing shared constants or delegating through the tested component when practical. When a test must expose the same image inputs as the tested component, it should use the same default values so version drift is caught by Renovate and by the shared constant source.

10. Permit Renovate-synchronized duplicate defaults.

   Default image tags do not have to live in constants. Duplicated constructor defaults are acceptable when every occurrence is tracked by Renovate with the same dependency identity, datasource, versioning, and extraction rule. Renovate should update the full runtime image tag atomically, including composite tags such as `0.154.5-10.5.0`. Manual drift is caught by keeping test defaults synchronized with tested-component defaults through shared constants or Renovate-managed duplicate defaults.

11. Use the runtime image source for Hugo minimum-version updates.

   Hugo `module.hugoVersion.min` in downstream sites should follow the same source as the runtime image stream when it is intended to describe the Hugo version available in the builder. For the current Hugo runtime, that source is Docker tags from `hugomods/hugo` with `extractVersion=^exts-(?<version>.+)$`, matching `container-images`, not GitHub releases from `gohugoio/hugo`.

12. Pair implementation changes with tests.

   Each component API change should update the relevant tests in the same implementation step. Final lint, format, and test command execution is user-owned for this change, but the implementation must leave the commands and expected targets documented for the user to run.

## Risks / Trade-offs

- Breaking `modules/opentofu` callers -> Document migration from `container_image` to split inputs and require a new release tag.
- More scenario constructor inputs -> Use clear prefixes and defaults so basic calls remain ergonomic while CI can pin versions explicitly.
- Inconsistent docs during transition -> Update root docs, reference docs, component READMEs, and examples in the same change.
- Hidden image defaults may remain in tests or docs -> Grep/audit public signatures and keep test defaults synchronized with tested-component defaults through shared constants or Renovate-managed duplicate defaults before closing the change.
- Test module aggregates drift across components -> Document the default no-argument `all()` shape and keep exceptions explicit.
- Test runtime image defaults drift from tested components -> Ensure duplicated defaults are Renovate-managed with the same source and synchronized with tested-component defaults through shared constants.
- Hugo minimum version tracks a newer upstream release than the runtime image stream -> Configure Renovate to use the same Docker datasource/extractVersion as the runtime base image source.

## Migration Plan

1. Update `scenarios/static-site` constructor, offline test overrides, and docs together.
2. Update `scenarios/helm-ci` constructor/state, offline test overrides, and docs together.
3. Update `modules/opentofu` runtime image inputs and docs together; document the test module gap.
4. Update repository guidance, Renovate examples, and downstream workflow guidance for runtime image and Hugo minimum-version synchronization.
5. Hand off final lint, format, test, and OpenSpec validation commands for the user to run.
6. Release changed modules/scenarios under new tags. Consumers migrate by pinning the new tags and replacing any old `container_image` or hidden default assumptions with explicit image inputs.

Rollback is tag-based: consumers can stay on previous released tags until their workflows are updated.

## Open Questions

None.
