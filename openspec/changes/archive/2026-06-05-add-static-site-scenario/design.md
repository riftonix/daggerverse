## Context

`modules/hugo` currently wraps a Hugo container, mounts a site directory, installs `autoprefixer` with npm during the build, updates a Hugo module, and returns the rendered `public` directory. This works as a smoke build, but it makes the build less reproducible than the prepared `ghcr.io/riftonix/container-images/hugo-autoprefixer:0.154.5-10.5.0` image and does not expose reusable validation or Hugo module management surfaces for CI.

The repository already separates low-level modules from higher-level scenarios. `scenarios/container-images` composes a module while leaving provider-specific trigger policy and publication details outside the scenario. The static-site workflow should follow the same boundary because GitHub Pages and GitLab Pages handle previews, publication, and cleanup differently.

Hugo is the first static-site engine for this scenario, but the scenario should not be named or modeled as Hugo-only. Jekyll can be added later with its own low-level module while keeping provider workflows and the static-site orchestration shape stable. Engine-specific features do not need to be shared across engines; Hugo module preparation remains a Hugo module concern and does not create a requirement for Jekyll.

The intended documentation architecture uses component `docs` and `openspec` repositories as separate Hugo modules imported by the main site. The main site owns the final URL placement through explicit mounts:

```yaml
module:
  imports:
    - path: github.com/riftonix/daggerverse/docs
      mounts:
        - source: content
          target: content/docs/components/daggerverse

    - path: github.com/riftonix/container-images/docs
      mounts:
        - source: content
          target: content/docs/components/container-images

    - path: github.com/riftonix/daggerverse/openspec
      mounts:
        - source: specs
          target: content/docs/specs
        - source: changes/archive
          target: content/docs/changes/archive

    - path: github.com/riftonix/container-images/openspec
      mounts:
        - source: specs
          target: content/docs/specs
        - source: changes/archive
          target: content/docs/changes/archive
```

This keeps component documentation under component-specific paths while merging OpenSpec specs and archived changes into shared namespaces. Example results:

```text
daggerverse/docs/content/how-to/foo.md
-> /docs/components/daggerverse/how-to/foo/

container-images/docs/content/how-to/foo.md
-> /docs/components/container-images/how-to/foo/

daggerverse/openspec/specs/git-module/spec.md
-> /docs/specs/git-module/spec/

container-images/openspec/specs/container-images-scenario/spec.md
-> /docs/specs/container-images-scenario/spec/
```

Because multiple `openspec` modules merge into the same virtual `content/docs/specs` and `content/docs/changes/archive` targets, Dagger automation must detect virtual path collisions before rendering or as part of validation. Hugo's union filesystem gives precedence to earlier mounts when files share the same path, which is useful for overrides but unsafe for shared spec namespaces unless collisions are intentional.

## Goals / Non-Goals

**Goals:**

- Make `modules/hugo` use the prepared Hugo Autoprefixer image by default.
- Remove runtime npm install behavior from the normal Hugo build path.
- Add strict Hugo validation and build functions that are useful in CI.
- Add Hugo module operations for creating or preparing reusable Hugo modules without requiring site publication.
- Add Dagger-native tests for the Hugo module, using the existing Docsy fixture site.
- Add `scenarios/static-site` as a provider-neutral orchestration layer for static-site verification and rendering, with Hugo as the first supported engine.
- Keep Hugo module preparation available through `modules/hugo`, not through the common static-site scenario API.
- Support Dagger automation that prepares separate `docs` and `openspec` Hugo modules and validates that the composed main-site mount layout can render.
- Validate that merged OpenSpec module mounts do not contain conflicting virtual paths unless the caller explicitly allows overrides.
- Keep workflow-specific GitHub and GitLab details in CI configuration.

**Non-Goals:**

- Add a full markdown, HTML, accessibility, or link linting module.
- Implement GitHub Pages or GitLab Pages publication APIs inside `modules/hugo`.
- Implement Jekyll support in this change.
- Implement a full OpenSpec renderer or transform arbitrary OpenSpec files into custom Docsy pages.
- Implement provider-specific preview cleanup, deployment comments, token handling, or environment lifecycle inside the scenario.
- Replace caller-owned decisions about which branches, merge requests, paths, or previews are in scope.

## Decisions

1. Use the prepared Hugo Autoprefixer image as the Hugo module default.

   The normal Hugo build path will rely on `ghcr.io/riftonix/container-images/hugo-autoprefixer:0.154.5-10.5.0`. This removes runtime npm installation and makes the build environment explicit. The alternative was to keep npm installation in the module for flexibility, but that repeats image-building concerns in every site build and makes CI depend on npm registry availability.

2. Treat Hugo build flags as the built-in validation mechanism.

   Hugo does not expose a dedicated `hugo lint` command. The module will provide validation through Hugo commands and strict flags such as `--panicOnWarning`, `--printPathWarnings`, `--printI18nWarnings`, and `--printUnusedTemplates`. A separate future module can own markdown, HTML, link, and accessibility linting.

3. Keep provider mechanics out of Dagger modules and the static-site scenario.

   GitHub and GitLab differ in event variables, Pages publication, deployment lifecycle, and preview cleanup. The scenario will accept explicit values such as `site_base_url` and return rendered directories or verification output. GitHub Actions and GitLab CI will remain responsible for deriving preview URLs, publishing Pages artifacts, deleting previews, managing environments, and commenting on PRs or MRs.

4. Make `scenarios/static-site` compose `modules/hugo` rather than duplicate Hugo logic.

   The scenario should provide workflow-shaped functions like `verify_site` and `render_site`, while all Hugo-specific command construction remains in `modules/hugo`. This preserves module reuse and keeps scenario behavior small.

5. Model the scenario around a static-site engine selection.

   The first supported engine will be Hugo. The scenario should expose an engine parameter or similarly explicit dispatch point so Jekyll support can be added later through a separate module without changing the provider workflow boundary. The scenario contract is limited to common static-site operations such as verification and rendering. Engine-specific operations, including Hugo module preparation, stay in the relevant engine module. The alternative was to create a Hugo-specific scenario first and rename it later, but that would make CI users change commands when another engine appears.

6. Keep content-only Hugo modules neutral about their final site path.

   A reusable documentation module should not need to know that an importing site wants to render it under `docs/components/daggerverse`. The content module can expose standard Hugo component directories such as `content`, while the importing site chooses the mount target with its module import configuration. This keeps the documentation module portable across sites that may want different URL paths.

7. Support Hugo module preparation separately from site rendering.

   Hugo modules can be initialized and imported independently of publishing a rendered site. The Hugo module should expose operations for module preparation so callers can validate reusable Hugo modules without producing a public directory. These operations should not be surfaced as generic static-site scenario functions because future engines such as Jekyll do not have the same module model. The alternative was to treat modules only as an implementation detail of a site build, but that would not support reusable module repositories.

8. Add Dagger-native tests before relying on the module in CI.

   The current shell smoke test is not discovered by the repository test matrix. Adding `modules/hugo/tests/dagger.json` and Python test functions makes `make tests module hugo` and GitHub Actions run Hugo checks consistently with the Git, Helm, and Docker modules.

9. Prepare separate component documentation and OpenSpec Hugo modules before rendering the main site.

   Dagger automation should prepare each component `docs` and `openspec` module root independently, then render the main site that imports those modules with the explicit mount layout. This verifies reusable modules and the composed site without embedding GitHub or GitLab publication behavior in Dagger code.

10. Keep OpenSpec artifacts unchanged and add Hugo sidecars when navigation needs them.

   The `openspec` tree can expose current specs from `specs` and archived completed changes from `changes/archive`. OpenSpec-owned files such as `spec.md`, `proposal.md`, `design.md`, and `tasks.md` should remain valid OpenSpec markdown. Hugo-owned sidecar `_index.md` files can be added next to them for Docsy navigation where needed.

11. Validate merged OpenSpec virtual paths.

   When multiple component OpenSpec modules mount into shared site targets, Dagger automation should compute the virtual paths contributed by each module and fail on duplicate paths by default. This prevents Hugo's precedence rules from silently hiding one component's spec or archived change behind another.

## Risks / Trade-offs

- Base image drift or missing tools -> Pin the default image tag and add tests that verify Hugo can build the Docsy fixture without npm installation.
- Strict Hugo flags may fail existing sites with warnings -> Make strict validation explicit and document which function callers should use for CI.
- Provider-neutral scenario may feel thin -> Keep it thin intentionally; CI providers have different Pages primitives and the scenario should not hide provider-specific lifecycle decisions.
- Engine selection can become awkward as new generators appear -> Keep Hugo-specific behavior inside `modules/hugo` and add a narrow scenario dispatch point instead of baking Hugo method names into workflow-facing commands.
- Hugo module preparation could leak into the common scenario contract -> Keep the static-site scenario limited to common render/verify operations and document engine-specific module APIs separately.
- Hugo module updates can break consumers that relied on runtime npm install -> Document the new image expectation and leave any optional package-install extension outside the normal build path if needed later.
- Shared OpenSpec mounts can hide duplicate paths -> Add a collision check for merged virtual paths and require globally unique spec/change paths unless overrides are explicitly allowed.
