## 1. Renovate Configuration

- [x] 1.1 Add a Python regex custom manager to `renovate.json` that matches a strict `# renovate: datasource=<datasource> depName=<depName>` annotation followed by a `*_IMAGE_TAG = "..."` assignment and extracts only `datasource`, `depName`, and `currentValue`.
- [x] 1.2 Ensure the Python image tag manager scans module, scenario, and test Python files without matching unrelated non-image constants.
- [x] 1.3 Keep existing Renovate managers for Dagger engine and GitHub Actions Dagger CLI versions unchanged.

## 2. Module Runtime Images

- [x] 2.1 In `modules/helm/src/helm/main.py`, add a Renovate annotation before `DEFAULT_IMAGE_TAG` with `datasource=docker depName=alpine/helm`.
- [x] 2.2 In `modules/helm/tests/src/tests/main.py`, replace inline `registry_image_registry`, `registry_image_repository`, and `registry_image_tag` default literals with `DEFAULT_REGISTRY_IMAGE_REGISTRY`, `DEFAULT_REGISTRY_IMAGE_REPOSITORY`, and annotated `DEFAULT_REGISTRY_IMAGE_TAG` constants using `datasource=docker depName=registry`.
- [x] 2.3 In `modules/helm-unittest/src/helm_unittest/main.py`, add a Renovate annotation before `DEFAULT_IMAGE_TAG` with `datasource=docker depName=helmunittest/helm-unittest`.
- [x] 2.4 In `modules/hugo/src/hugo/main.py`, add `DEFAULT_IMAGE_REGISTRY`, `DEFAULT_IMAGE_REPOSITORY`, annotated `DEFAULT_IMAGE_TAG`, and `DEFAULT_CONTAINER_USER_ID` constants for `ghcr.io/riftonix/container-images/hugo-autoprefixer:0.154.5-10.5.0`; replace inline defaults and fallback literals with the constants.
- [x] 2.5 In `modules/hugo/tests/src/tests/main.py`, remove duplicated `DEFAULT_HUGO_IMAGE_*` constants and stop passing Hugo image defaults explicitly; rely on the Hugo module defaults from `modules/hugo/src/hugo/main.py`.
- [x] 2.6 In `modules/git/src/git/main.py`, add `DEFAULT_IMAGE_REGISTRY`, `DEFAULT_IMAGE_REPOSITORY`, annotated `DEFAULT_IMAGE_TAG`, and `DEFAULT_CONTAINER_USER_ID` constants for `docker.io/alpine/git:2.52.0`; replace inline defaults with the constants.
- [x] 2.7 In `modules/opentofu/src/opentofu/main.py`, add a Renovate annotation before `DEFAULT_IMAGE_TAG` with `datasource=docker depName=ghcr.io/opentofu/opentofu` while keeping the current `latest` value unchanged.
- [x] 2.8 In `modules/opentofu/tests/src/tests/main.py`, remove duplicated `DEFAULT_IMAGE_*` and `DEFAULT_USER_ID` constants and stop passing OpenTofu image defaults explicitly; rely on the OpenTofu module defaults from `modules/opentofu/src/opentofu/main.py`.
- [x] 2.9 In `modules/ssh/src/ssh/main.py`, add `DEFAULT_IMAGE_REGISTRY`, `DEFAULT_IMAGE_REPOSITORY`, annotated `DEFAULT_IMAGE_TAG`, and `DEFAULT_CONTAINER_USER_ID` constants for `docker.io/kroniak/ssh-client:3.21`; replace inline defaults with the constants.
- [x] 2.10 Confirm `modules/docker/src/docker/main.py` has no runtime image defaults to annotate and leave it unchanged unless a managed runtime image default is found during implementation.

## 3. Scenario Runtime Images

- [x] 3.1 In `scenarios/helm-ci/src/helm_ci/main.py`, add a Renovate annotation before `DEFAULT_HELM_IMAGE_TAG` with `datasource=docker depName=alpine/helm`.
- [x] 3.2 In `scenarios/helm-ci/src/helm_ci/main.py`, add a Renovate annotation before `DEFAULT_GIT_IMAGE_TAG` with `datasource=docker depName=alpine/git`.
- [x] 3.3 In `scenarios/helm-ci/tests/src/tests/main.py`, remove duplicated `DEFAULT_HELM_IMAGE_*` and `DEFAULT_GIT_IMAGE_*` constants and stop passing Helm CI scenario image defaults explicitly; keep `FIXTURE_GIT_IMAGE_*` for fixture repository creation and add a Renovate annotation before `FIXTURE_GIT_IMAGE_TAG` with `datasource=docker depName=alpine/git`.
- [x] 3.4 In `scenarios/static-site/src/static_site/main.py`, add `DEFAULT_HUGO_IMAGE_REGISTRY`, `DEFAULT_HUGO_IMAGE_REPOSITORY`, annotated `DEFAULT_HUGO_IMAGE_TAG`, and `DEFAULT_HUGO_CONTAINER_USER_ID` constants for `ghcr.io/riftonix/container-images/hugo-autoprefixer:0.154.5-10.5.0`; replace inline defaults and fallback literals with the constants.
- [x] 3.5 In `scenarios/static-site/tests/src/tests/main.py`, remove duplicated `DEFAULT_HUGO_IMAGE_*` constants and stop passing Static Site scenario image defaults explicitly; rely on the Static Site scenario defaults from `scenarios/static-site/src/static_site/main.py`.
- [x] 3.6 Confirm `scenarios/container-images/src/container_images/main.py` has no runtime image defaults to annotate and leave it unchanged unless a managed runtime image default is found during implementation.

## 4. Consistency Checks

- [x] 4.1 Verify every managed `*_IMAGE_TAG` constant has the Renovate annotation on the immediately preceding line.
- [x] 4.2 Verify every annotation `depName` matches the adjacent image registry and repository convention: Docker Hub images use repository names such as `alpine/helm`, and GHCR images include `ghcr.io/`.
- [x] 4.3 Verify matching images use identical `datasource` and `depName` across modules, scenarios, and tests so Renovate can update them in one MR.
- [x] 4.4 Verify no runtime image defaults remain as inline string literals in function signatures or constructor fallbacks for the covered modules and scenarios.
- [x] 4.5 Update the relevant `docs/` page during archive to document the image constants and Renovate annotation convention for new modules, scenarios, and tests.

## 5. Validation

- [x] 5.1 Run a JSON/schema validation for `renovate.json`.
- [x] 5.2 Run Python linting or formatting checks required by the repository for changed Python files.
- [x] 5.3 Run the relevant OpenSpec validation command for `annotate-image-tags-for-renovate`.
- [x] 5.4 Do not run heavy Dagger integration tests locally; provide the exact command for the user to run if full Dagger verification is needed.
