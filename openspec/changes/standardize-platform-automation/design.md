## Context

Riftonix repositories are converging on Dagger scenarios for portable CI logic, but the surrounding automation is still copied per repository. `daggerverse`, `container-images`, and `riftonix.github.io` each pin the Dagger CLI in GitHub Actions, configure Renovate custom managers, and maintain workflow-specific glue. `container-images` and `daggerverse` still route important workflows through Makefile targets, while `riftonix.github.io` already demonstrates the preferred direction: GitHub Actions can run in GitHub and locally through `act`, and the workflow calls a Dagger scenario directly.

The goal is to present the Riftonix organization as a platform engineering demo. That means consumer repositories should expose intent and repository-specific policy, while shared platform repositories own common automation. Dagger remains the portable execution layer. GitHub Actions remains the event and permission layer. Renovate remains the dependency update policy engine.

The current repository is still the right place to plan this work because Daggerverse owns the reusable scenarios and the baseline OpenSpec expectations. The final reusable GitHub Actions and Renovate presets can live in a dedicated repository such as `riftonix/platform-automation`, or in the organization `.github` repository if that better fits GitHub discovery and repository presentation.

## Goals / Non-Goals

**Goals:**

- Provide composable Renovate presets for common Riftonix repository concerns.
- Provide reusable GitHub Actions workflows for common CI, publication, release, and preview flows.
- Provide composite actions only for repeated step-level behavior that is smaller than a workflow.
- Make local `act` execution a first-class supported path for workflows that can reasonably run locally.
- Keep Dagger modules and scenarios responsible for provider-neutral build, verify, render, and publish logic.
- Keep repository workflows responsible for events, branch filters, path filters, permissions, concurrency, and repository-specific inputs.
- Remove or demote Makefiles after equivalent workflow and `act` paths exist.
- Migrate repositories incrementally, starting with the repositories closest to the target pattern.

**Non-Goals:**

- Move Dagger module or scenario implementations out of `daggerverse`.
- Hide GitHub Pages, GitHub Packages, pull request comments, branch protection, or token permissions inside Dagger scenarios.
- Replace Renovate with a custom dependency update tool.
- Make one universal workflow that every repository must use.
- Require every workflow to support local `act` execution when provider-only features make local execution impractical.
- Preserve Makefile commands as a compatibility API after documented workflow alternatives exist.

## Decisions

1. Create a dedicated platform automation surface.

   Shared automation should live outside consumer repositories, either in `riftonix/platform-automation` or in `riftonix/.github`. A dedicated repository is clearer for a demo organization because it gives the paved road a visible home and can contain reusable workflows, composite actions, Renovate presets, documentation, and migration examples in one place. The organization `.github` repository remains a viable alternative if GitHub defaults and organization profile content become the primary concern.

   Alternative considered: keep shared workflows in `daggerverse`. This was rejected because GitHub reusable workflows and organization Renovate presets are not Dagger modules. Mixing them into Daggerverse would blur the repository's purpose and make it harder to explain the platform boundary.

2. Model Renovate as composable presets, not one global config.

   The shared Renovate config should provide small presets such as `base`, `github-actions`, `dagger`, `daggerverse`, `docker-bake`, `hugo`, `go`, `terraform`, and `helm`. Consumer repositories compose only the presets they need through `extends`.

   Alternative considered: one universal org config. This was rejected because repositories have different managers, labels, package grouping, automerge safety, and custom regex requirements. A universal config would either be too weak or would enable irrelevant managers and rules everywhere.

3. Use reusable workflows for job-level automation and composite actions for step-level helpers.

   Reusable workflows should own common job graphs such as static-site CI, static-site publish, container image verify/publish, Daggerverse component tests, Go service CI, Terraform module checks, and Helm chart checks. Composite actions should own repeated step sequences such as Dagger setup, `act` source detection, and required job result validation.

   Alternative considered: composite actions only. This was rejected because composite actions cannot define job matrices, permissions, triggers, dependencies, or reusable workflow outputs. The duplicated Riftonix behavior is mostly job graph behavior, not just repeated shell steps.

4. Keep repository workflow files intentionally thin.

   Consumer repositories should keep the root workflow files that define `on`, branch/path filters, permissions, concurrency, and calls to reusable workflows. This makes repository-specific policy visible and keeps branch protection checks stable. The called workflow receives explicit inputs for Dagger module refs, site URLs, image roots, registry behavior, or component selectors.

   Alternative considered: centralize workflow triggers completely. This was rejected because reusable workflows are called from jobs and do not own the caller's events. Repository owners also need local visibility into what events run automation.

5. Treat Dagger as the portable execution layer.

   The reusable workflows should call Dagger scenarios or modules for domain work. They should not reimplement image build logic, Hugo rendering, Helm checks, Git changed component logic, or publication tagging in shell when an existing Dagger scenario can own it. Shell remains acceptable for provider glue, JSON output shaping, and small validation logic at the workflow boundary.

   Alternative considered: move all logic to GitHub Actions. This was rejected because it would lose the portability that Daggerverse already provides and would make local and future provider execution harder.

6. Replace Makefile command surfaces with workflow and `act` surfaces.

   Makefiles currently bundle validation, component selection, release tagging, and Dagger calls. The long-term interface should be `act` for local workflow execution and GitHub Actions for hosted execution. Repositories may keep a short transitional Makefile only while equivalent reusable workflows are being introduced.

   Alternative considered: keep a shared Makefile copied or included across repositories. This was rejected because it repeats the same distribution problem as Renovate and GitHub Actions, and it creates a second automation API beside the workflows that branch protection actually runs.

7. Version reusable automation separately from consumer repositories.

   Reusable workflows, composite actions, and Renovate presets should be referenced by stable tags or release branches after their initial adoption. Renovate should update those references where possible. Consumer repositories can pin major versions for stability and opt into breaking changes intentionally.

   Alternative considered: always reference `master`. This was rejected because CI behavior changes would land in every repository at once and make rollback harder.

8. Migrate in dependency order.

   `riftonix.github.io` should be the first consumer because it already removed the Makefile and has an `act`-aware workflow shape. `container-images` should follow because it exercises changed component matrices, Dagger scenarios, registry credentials, and tag publication. `daggerverse` should follow with its own component discovery, test, publish, and release workflows. Older repositories such as `terraform-shared`, `kelm`, `kafgres`, and `helm-shared` can migrate once the common patterns are stable.

## Risks / Trade-offs

- Reusable workflows become too generic -> Keep multiple focused workflows by repository archetype instead of one parameter-heavy workflow.
- Local `act` behavior diverges from GitHub-hosted behavior -> Document supported local paths, keep `.actrc` and event fixtures small, and avoid provider-only steps during local runs.
- Renovate presets accidentally enable unsafe automerge -> Split automerge policy into an explicit preset and keep risky managers opt-in by repository type.
- Workflow version pins can drift across repositories -> Add Renovate rules for reusable workflow references and document supported upgrade cadence.
- Required check names change during migration -> Preserve existing top-level workflow/job names where branch protection depends on them, or migrate branch protection in the same change.
- Makefile removal breaks contributor muscle memory -> Document the replacement `act` commands before removal and migrate one repository at a time.
- Central automation repository outage or bad release affects many consumers -> Pin stable automation versions and keep rollback as a one-line reference downgrade in consumer workflows.

## Migration Plan

1. Create the platform automation repository or choose the organization `.github` repository as the shared automation home.
2. Add Renovate presets for `base`, `github-actions`, `dagger`, `daggerverse`, `docker-bake`, `hugo`, `go`, `terraform`, and `helm`.
3. Add composite actions for Dagger setup, local `act` source detection, and required job result checks.
4. Add reusable workflows for static-site CI/publish, container image CI/publish, Daggerverse quality/test/publish/release, Go service CI/publish, Terraform module checks, and Helm chart checks.
5. Migrate `riftonix.github.io` to shared Renovate presets and reusable static-site workflows while preserving local `act` support.
6. Migrate `container-images` by replacing Makefile-backed workflow steps with reusable workflows that call the existing Dagger scenarios directly.
7. Migrate `daggerverse` after its workflows have reusable equivalents for quality checks, component test discovery, publication, and release tag publication.
8. Migrate older repositories in batches by repository archetype.
9. Remove transitional Makefiles only after the repository has documented `act` commands and hosted workflows that cover the same behavior.

Rollback is per repository: revert the consumer workflow `uses` reference, pin a previous platform automation release, or restore the previous repository-local workflow while keeping the shared automation repository intact. Renovate preset rollback is similarly a change to the consumer `extends` list or referenced preset version.

## Open Questions

- Should the shared automation home be `riftonix/platform-automation` for explicit demo clarity or `riftonix/.github` for organization-default behavior?
- Which workflows should guarantee local `act` support in their first release, and which should be documented as GitHub-only because they depend on provider features?
- Should automerge live in the default Renovate preset or remain an explicit opt-in preset per repository?
