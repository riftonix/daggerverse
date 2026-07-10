## Context

The repository contains Dagger modules and scenarios that run external container images. Current image defaults are not declared uniformly: some modules use `DEFAULT_IMAGE_*` constants, some scenarios use prefixed constants, and several modules or scenarios keep image values as inline default argument literals.

Renovate already manages some repository dependencies through `renovate.json`, but it does not currently discover Python runtime image defaults. The target implementation needs to cover modules, scenarios, and tests without adding a separate image manifest that would duplicate the Python source of truth.

## Goals / Non-Goals

**Goals:**

- Make runtime image tags discoverable by Renovate directly from Python source.
- Establish the same image declaration convention for new modules, scenarios, and tests.
- Keep image registry, repository, and tag visible near the code that uses each image.
- Allow the same image in modules, scenarios, and tests to be updated in one MR by using the same Renovate `depName`.
- Replace inline runtime image defaults with named constants so the convention is easy to scan and maintain.
- Keep Dagger API behavior unchanged by preserving the existing default values.

**Non-Goals:**

- Introduce a central image manifest or generated Python constants.
- Change image pinning strategy beyond making existing tags Renovate-managed.
- Refactor module behavior unrelated to runtime image defaults.
- Force all container images built by scenarios to be managed by Renovate. Only runtime images declared as defaults are in scope.

## Decisions

1. Use code-local Renovate annotations immediately before image tag constants.

   The annotation is placed before the `*_IMAGE_TAG` line:

   ```python
   DEFAULT_IMAGE_REGISTRY = "docker.io"
   DEFAULT_IMAGE_REPOSITORY = "alpine/helm"
   # renovate: datasource=docker depName=alpine/helm
   DEFAULT_IMAGE_TAG = "3.18.6"
   ```

   This keeps the Renovate source metadata near the version Renovate updates and avoids inferring dependency identity from neighboring constants. A structural regex-only approach was considered, but it would be more fragile because it must derive registry and repository from adjacent assignments.

2. Keep registry and repository as separate Python constants.

   The modules already accept `image_registry`, `image_repository`, and `image_tag` inputs separately. Keeping the constants split preserves the existing Dagger API shape and avoids parsing a single image reference at runtime.

3. Use matching `depName` values to coordinate module, scenario, and test updates.

   Renovate treats matching dependency records as the same update when `datasource`, `depName`, and versioning are compatible. Therefore `alpine/helm` must use the same annotation in the `helm` module, `helm-ci` scenario, and related tests. GHCR images include the registry in `depName`, for example `ghcr.io/riftonix/container-images/hugo-autoprefixer`.

4. Add one Python regex custom manager to `renovate.json`.

   The manager matches the strict annotation format `# renovate: datasource=<datasource> depName=<depName>` followed by a Python assignment whose name ends in `_IMAGE_TAG`. The annotation provides only `datasource` and `depName`, while the assignment provides `currentValue`.

5. Do not add a central image manifest.

   A manifest could make Renovate matching simpler, but it would create a second source of truth unless the Python code reads it dynamically or generated code is introduced. For this repository, direct Python constants are simpler and more reliable.

6. Apply the convention to future modules and scenarios.

   New Python modules, scenarios, and tests that introduce runtime image defaults must start with the same constants and annotation pattern. This prevents new code from reintroducing inline image defaults after the existing codebase is migrated.

## Risks / Trade-offs

- Annotation drift between `*_IMAGE_REPOSITORY` and `depName` can cause Renovate to update a tag for the wrong dependency. Mitigation: implementation tasks require matching each annotation to the adjacent registry and repository constants.
- Renovate regex custom managers are sensitive to formatting. Mitigation: standardize on one-line annotation comments immediately followed by a single assignment line.
- Docker Hub and GHCR use different `depName` conventions. Mitigation: use Docker Hub repository names without `docker.io/` and GHCR names with the `ghcr.io/` prefix.
- Tags such as `latest` may not produce useful update MRs. Mitigation: keep existing values unchanged in this change and let future module-specific proposals decide whether to pin or change tag strategy.

## Migration Plan

1. Add the Renovate Python image tag custom manager to `renovate.json`.
2. Convert runtime image defaults to constants where they are currently inline.
3. Add Renovate annotations to all runtime image tag constants in modules, scenarios, and tests.
4. Keep existing default values unchanged.
5. Validate Renovate config syntax and use a dry-run or hosted Renovate result to confirm extraction.
6. When the change is archived, update `docs/` with the convention for new modules and scenarios.
