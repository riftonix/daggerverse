## 1. Shared Automation Home

- [ ] 1.1 Decide whether the shared automation home is `riftonix/platform-automation` or `riftonix/.github` and document the rationale.
- [ ] 1.2 Create the shared automation repository structure for Renovate presets, reusable workflows, composite actions, examples, and documentation.
- [ ] 1.3 Add repository overview documentation explaining the boundary between Renovate presets, GitHub Actions workflows, composite actions, and Dagger scenarios.
- [ ] 1.4 Add release/versioning documentation for shared workflow, composite action, and Renovate preset references.

## 2. Renovate Presets

- [ ] 2.1 Add a `base` Renovate preset with shared defaults, labels, rate limits, ignored dependency paths, and safe global policy.
- [ ] 2.2 Add a `github-actions` preset for built-in GitHub Actions dependency updates and grouping.
- [ ] 2.3 Add a `dagger` preset for Dagger CLI pins in GitHub Actions workflows.
- [ ] 2.4 Add a `daggerverse` preset for released Daggerverse module and scenario references.
- [ ] 2.5 Add a `docker-bake` preset for annotated Docker Bake variables and image dependency labels.
- [ ] 2.6 Add `hugo`, `go`, `terraform`, and `helm` presets for repository archetype-specific dependency update policy.
- [ ] 2.7 Add documentation with example `renovate.json` files for static-site, container-images, daggerverse, Go service, Terraform module, and Helm chart repositories.
- [ ] 2.8 Validate the presets with Renovate config validation or a documented dry-run procedure.

## 3. Composite Actions

- [ ] 3.1 Add a composite action for Dagger setup that accepts the Dagger version as an explicit input.
- [ ] 3.2 Add a composite action or documented reusable step sequence for detecting the local source directory during `act` runs.
- [ ] 3.3 Add a composite action for required job result checks used by aggregate `ci-passed` jobs.
- [ ] 3.4 Add README documentation and minimal example usage for each composite action.

## 4. Reusable Workflows

- [ ] 4.1 Add reusable static-site CI workflow for verify and pull request preview behavior backed by the Dagger static-site scenario.
- [ ] 4.2 Add reusable static-site publish workflow for production rendering and GitHub Pages publication.
- [ ] 4.3 Add reusable container image CI workflow for changed Bake target discovery and verification backed by the Dagger container-images scenario.
- [ ] 4.4 Add reusable container image publish workflow for changed Bake target publication, registry authentication, and release tag publication.
- [ ] 4.5 Add reusable Daggerverse quality workflow for Ruff, OpenSpec validation, and Dagger version alignment checks.
- [ ] 4.6 Add reusable Daggerverse component test workflow for discovering module and scenario test modules and running their aggregate tests.
- [ ] 4.7 Add reusable Daggerverse publication workflow for publishing all modules and scenarios on default branch pushes.
- [ ] 4.8 Add reusable Daggerverse release workflow for publishing one module or scenario from release tags.
- [ ] 4.9 Add reusable Go service workflow covering tests and optional `ko` image publication.
- [ ] 4.10 Add reusable Terraform module workflow covering formatting and generated documentation checks.
- [ ] 4.11 Add reusable Helm chart workflow covering lint, template, package, and optional OCI publication.
- [ ] 4.12 Document which reusable workflows support local `act` execution and which are GitHub-only.

## 5. Consumer Repository Migration

- [ ] 5.1 Migrate `riftonix.github.io` to shared Renovate presets and reusable static-site workflows while preserving `.actrc` and local event fixture behavior.
- [ ] 5.2 Migrate `container-images` to shared Renovate presets and reusable container image workflows.
- [ ] 5.3 Replace `container-images` Makefile-backed workflow steps with direct Dagger calls or shared workflow behavior.
- [ ] 5.4 Migrate `daggerverse` to shared Renovate presets and reusable Daggerverse quality, test, publish, and release workflows.
- [ ] 5.5 Replace `daggerverse` Makefile-backed workflow steps with workflow-native commands or shared workflow behavior.
- [ ] 5.6 Migrate `terraform-shared` to shared Renovate presets and reusable Terraform module workflow.
- [ ] 5.7 Migrate `kelm` and `kafgres` to shared Renovate presets and reusable Go service workflows.
- [ ] 5.8 Migrate `helm-shared` to shared Renovate presets and reusable Helm chart workflows.

## 6. Makefile Retirement

- [ ] 6.1 For each migrated repository, map every existing Makefile target to a hosted workflow path, local `act` command, or explicit non-CI replacement command.
- [ ] 6.2 Update repository documentation to show the replacement commands before removing any Makefile target.
- [ ] 6.3 Remove or demote transitional Makefiles only after hosted CI and documented local paths cover the same behavior.
- [ ] 6.4 Update Daggerverse OpenSpec baseline after Makefile-based repository command interface behavior has been replaced.

## 7. Verification

- [ ] 7.1 Run OpenSpec validation for `standardize-platform-automation`.
- [ ] 7.2 Run focused workflow validation for each reusable workflow using `act` where supported.
- [ ] 7.3 Run GitHub Actions checks for migrated repositories and confirm required check names remain valid or branch protection is updated deliberately.
- [ ] 7.4 Run Renovate validation or dry runs for migrated repositories and confirm expected dependency files are detected.
- [ ] 7.5 Confirm each migrated repository has no copied Renovate or GitHub Actions logic that should now come from shared automation.
