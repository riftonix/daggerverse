## 1. Docker Module With Incremental Tests

- [ ] 1.1 Create `modules/docker` Dagger module structure with metadata, Python package files, source package, README, neighboring `modules/docker/tests`, a minimal fixture image context, and an `all` test stub.
- [ ] 1.2 Update the root command interface so `make tests docker` runs the Docker test module as soon as the stub exists.
- [ ] 1.3 Implement Docker module construction around a repository source directory and optional container state, then add or update Docker module tests for construction and aggregate test wiring.
- [ ] 1.4 Implement image build using Dagger-native container build behavior with context path, Dockerfile path, target, and build arguments, then add or update Docker module tests for successful build and build options.
- [ ] 1.5 Implement optional smoke checks that build an image and run a caller-provided command in the resulting container, then add or update Docker module tests for smoke success and failure behavior.
- [ ] 1.6 Implement chainable `with_registry_login` for generic OCI registry authentication using username and password secret, then add or update Docker module tests for credential configuration without exposing the secret.
- [ ] 1.7 Implement image publish that builds and publishes to a caller-provided OCI image reference, then add or update Docker module tests for publication to a local OCI registry service without external registry credentials.

## 2. Repository CI And Scenario Lifecycle

- [ ] 2.1 Replace module-only Makefile argument parsing with explicit component addressing: `make tests module docker` and `make tests scenario container-images`.
- [ ] 2.2 Remove legacy shorthand commands such as `make tests docker` and make them fail with usage guidance for the explicit command form.
- [ ] 2.3 Move shared Ruff configuration from `modules/ruff.toml` to repository-level `ruff.toml`.
- [ ] 2.4 Update `make lint`, `make lint-check`, `make format`, and `make format-check` so no-argument runs cover all existing Python component roots under `modules/` and `scenarios/`.
- [ ] 2.5 Update lint and format selectors so `make lint module docker`, `make lint scenario container-images`, and analogous check/format commands target one component.
- [ ] 2.6 Extend pull request CI discovery to produce module and scenario test matrix entries with explicit `kind` and `name` fields.
- [ ] 2.7 Extend pull request CI test execution to call `make tests <kind> <name>` for each discovered module or scenario test module.
- [ ] 2.8 Extend branch-push publication so all Dagger scenarios under `scenarios/<scenario-name>` are published analogously to modules.
- [ ] 2.9 Extend release-tag publication so tags matching `scenarios/<scenario-name>/vX.Y.Z` publish only the named scenario and fail clearly for unknown scenarios.
- [ ] 2.10 Update release command validation so scenario release tags can be created consistently with module release tags.

## 3. Container Images Scenario With Incremental Tests

- [ ] 3.1 Create `scenarios/container-images` Dagger module structure with metadata, Python package files, source package, README, neighboring test module, local dependency on `modules/docker`, fixture image contexts, and an `all` test stub.
- [ ] 3.2 Implement single-image verification with explicit source, context path, Dockerfile path, optional target, optional build args, and optional smoke command, then add or update scenario tests for build-only and smoke verification.
- [ ] 3.3 Implement multi-image verification over caller-provided image specs, then add or update scenario tests for successful multi-image verification and failure propagation.
- [ ] 3.4 Implement single-image publication with explicit source, context path, destination image reference, and optional registry credentials, then add or update scenario tests using a local OCI registry service.
- [ ] 3.5 Implement multi-image publication over caller-provided publish specs, then add or update scenario tests for publishing multiple refs and failure propagation.
- [ ] 3.6 Ensure the scenario implementation and tests keep GitHub Actions, GitLab CI, tag parsing, changed-directory detection, and hardcoded `docker/` path policy outside the scenario.

## 4. Documentation

- [ ] 4.1 Document `modules/docker` public API and examples for build, login, publish, and smoke checks by following the style of `modules/git/README.md`.
- [ ] 4.2 Document `scenarios/container-images` examples using explicit `context_path` and `image_ref` inputs.
- [ ] 4.3 Update repository docs to describe the Docker module and container-images scenario as separate layers.
- [ ] 4.4 Include an example CI mapping where a provider workflow parses `docker/<image-name>/<version>` into `context_path` and `image_ref` before calling the scenario.
- [ ] 4.5 Document the explicit Makefile command form for modules and scenarios, including tests, lint, and format.
