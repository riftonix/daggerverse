## Context

The repository already separates reusable Dagger modules under `modules/` from ready-to-run CI scenarios under `scenarios/`. The existing `git` module provides provider-neutral primitives for refs, tags, changed files, changed directories, and changed components, so container image CI should not duplicate Git policy or CI-provider event handling.

The new container image workflow should support a future `container-images` monorepo where image contexts may live under `docker/<image-name>`, but that path convention must be supplied by the caller rather than hardcoded into the scenario. CI systems remain responsible for deciding when to run, which contexts are in scope, and how repository tags map to destination image references.

## Goals / Non-Goals

**Goals:**
- Provide a reusable `modules/docker` module for Dagger-native image build, registry auth, publish, platform-aware builds, build arguments, and smoke checks.
- Use an object-oriented Docker module API where `Docker.build(...)` returns a build object and publishing returns an image object.
- Support explicit build arguments and target platforms in the Docker module API.
- Provide a portable `scenarios/container-images` entrypoint that accepts explicit image contexts and destination refs.
- Extend the existing repository command interface and GitHub workflows so scenarios have the same test and publish lifecycle as modules.
- Replace module-only Makefile shorthand with explicit component addressing for modules and scenarios.
- Move shared Ruff configuration to the repository root and make lint/format commands cover both `modules/` and `scenarios/`.
- Keep GHCR support generic by treating `ghcr.io` as a normal OCI registry.
- Keep changed-component detection and tag lookup in `modules/git`.
- Add focused tests and documentation for the new public APIs.

**Non-Goals:**
- Do not implement GitHub Actions, GitLab CI, or other provider-specific trigger policy inside the scenario.
- Do not parse release tags such as `docker/<image-name>/<version>` inside the scenario.
- Do not hardcode `docker/` as the image root in the scenario.
- Do not add a GHCR-specific module.
- Do not require a Docker daemon.
- Do not modify the existing Helm module or rename its registry-login API.

## Decisions

1. `modules/docker` will use Dagger-native container build and publish APIs.

   This keeps the module daemonless and compatible with Dagger execution environments. The alternative was shelling out to Docker CLI, but that would add daemon requirements and make tests less portable.

2. Smoke checks will be included as a cheap first-stage primitive.

   A smoke check will build the image and run a caller-provided command in the resulting container. The module will not invent image-specific checks. This is low-cost because it reuses the built container and only requires an optional command list from the caller.

3. `scenarios/container-images` will accept explicit `context_path` and `image_ref` values.

   CI-provider workflows can map tags, branches, or changed components to these values before calling Dagger. The scenario stays portable and can be reused by GitHub Actions, GitLab CI, local scripts, or another orchestrator.

4. Multi-image scenario functions will accept lists of image specs.

   This gives CI a stable batch interface after it has already selected the relevant image contexts. The scenario should aggregate results and fail if any image verification or publication fails.

5. Scenario tests and publication will be supported by the repository infrastructure.

   The existing CI discovers module tests under `modules/<name>/tests`, and publication discovers modules under `modules/<name>`. This change will add analogous scenario discovery for `scenarios/<name>/tests` and publication for `scenarios/<name>`. Branch pushes should publish all scenarios, while tags like `scenarios/container-images/v0.0.0` should publish only the named scenario. The alternative was to keep scenario CI manual for now, but that would make the first scenario a second-class repository artifact.

6. Makefile commands will use explicit component kind and name.

   Test commands should use `make tests module docker` and `make tests scenario container-images`. Lint and format commands should support `make lint`, `make lint module docker`, and `make lint scenario container-images`, with analogous `lint-check`, `format`, and `format-check` commands. Existing shorthand commands such as `make tests docker` will be removed during the CI command-interface update because they become ambiguous once modules and scenarios share the same top-level lifecycle.

7. Ruff configuration will move to the repository root.

   The current `modules/ruff.toml` placement implies module-only ownership. A root-level `ruff.toml` is a better fit once Python code exists under both `modules/` and `scenarios/`, and it lets `ruff` discover the shared configuration without per-tree duplication.

8. The Docker module will expose `Docker`, `DockerBuild`, and `DockerImage` objects.

   `Docker.build(...)` should return a `DockerBuild` object. `DockerBuild.publish(...)` should return a `DockerImage` object. This keeps the first-stage API small while leaving room for later image operations such as digest lookup, tarball export, copy, scan, SBOM, sign, or attest without changing the build entrypoint.

9. The Docker module will use `with_registry_auth`.

   Docker image publish and pull operations can use Dagger-native `Container.with_registry_auth`, so the Docker module should expose `with_registry_auth` rather than `with_registry_login`. The existing Helm module will not be changed in this proposal because Helm OCI pushes rely on Helm registry configuration and are not a direct equivalent.

10. The Docker module will publish through Dagger-native `Container.publish`.

   Publication should pass caller-provided OCI image references directly to Dagger. This keeps registries such as `ghcr.io` provider-neutral and avoids Docker CLI or daemon requirements.

   `Container.publish` is resolved by the Dagger engine rather than by a caller-managed container. Because of that, Dagger service bindings used by test containers do not make an ephemeral registry service reachable to the publish resolver. Default Docker module tests should cover publish validation and result wiring with a dry-run publish mode. Real publish integration tests, when needed, require a registry that is reachable by the Dagger engine itself, such as an engine-level `registry:5000` fixture configured in `engine.json`.

11. The Docker module will accept target platforms.

   The build API should accept `platforms: list[dagger.Platform] | None`. Empty or omitted platforms mean single-platform build for the default/current platform. Multiple platforms produce platform variants that publication can push as a multi-platform image.

12. Build arguments will use CLI-friendly `KEY=VALUE` strings.

   The public API should accept build arguments as strings because this is ergonomic for Dagger CLI and CI callers. Parsing must use `partition("=")` or equivalent validation so values containing `=` remain valid and malformed arguments fail clearly.

## Risks / Trade-offs

- Registry auth behavior varies between registries -> Keep the Docker module registry auth generic and test credential configuration without exposing the secret in default tests.
- Smoke commands can be too image-specific -> Require callers to pass the command explicitly and keep the default behavior to build-only verification.
- Passing structured image specs through Dagger CLI can be less ergonomic than provider-specific scripts -> Provide single-image functions and batch functions so CI can choose the simpler interface.
- OCI publication tests can be slow or flaky if they depend on external services -> Cover publish wiring in default Dagger-native tests with dry-run mode; run real publication only in an integration environment with an engine-reachable registry fixture.
- Scenario CI broadens the root command interface beyond modules -> Use explicit component kind and name in Makefile commands and update documentation at the same time.
- Removing module-only shorthand commands changes local developer muscle memory -> Make the new commands clear in help text and docs.

## Migration Plan

1. Add `modules/docker` and its tests.
2. Extend repository test, lint, format, and publish discovery to support scenarios with explicit component-kind commands.
3. Add `scenarios/container-images` depending on `modules/docker` with tests alongside each public function.
4. Update repository docs and examples.
5. In the future container-images monorepo, add thin CI workflow steps that compute `context_path` and `image_ref`, then call `scenarios/container-images`.
