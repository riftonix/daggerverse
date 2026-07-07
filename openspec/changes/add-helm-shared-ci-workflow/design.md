## Context

`scenarios/helm-ci` currently composes `modules/helm` and `modules/git` for provider-neutral Helm chart checks. It can verify one chart, publish one chart, and verify changed chart directories using merge-base diff behavior. This is enough for basic pull request checks, but not enough for an external chart repository that needs a complete lifecycle from pull request validation to default-branch publication.

Helm unittest is a separate tool from Helm itself. It should be represented as its own reusable module based on the public `helmunittest/helm-unittest` image instead of being added to `modules/helm`.

`riftonix/helm-shared` is the first planned consumer. Its default branch is `master`; `main` exists but does not contain the full chart tree. The `master` branch contains `.github/workflows/ci.yaml`, `charts/appchart`, and `libs/common`. `charts/appchart` is an application chart with generated or source documentation content under the chart tree, and `libs/common` is a library chart. The Dagger scenario must support both chart roots without assuming a specific provider event model.

The archived static-site design established that component documentation is intended to be imported and published by the main site. That boundary applies here too: `helm-shared` CI should validate documentation content that lives in the chart repository when needed, but it should not render, publish, deploy, or manage the external main site.

## Goals / Non-Goals

**Goals:**

- Extend Helm CI so one released scenario can validate `helm-shared` pull requests and publish changed charts after merges.
- Keep provider mechanics outside Dagger. GitHub Actions, GitLab CI, or another adapter decides when to call each scenario function.
- Support `charts/*` and `libs/*` chart roots, including application and library chart differences.
- Run Helm dependency update, lint, template, and optional unittest checks through public runtime images.
- Add a dedicated Helm unittest module that can be reused outside the Helm CI scenario.
- Publish changed dev charts with caller-provided build metadata and changed release charts with the version from `Chart.yaml`.
- Return structured results that provider adapters can turn into summaries, comments, or logs without parsing free-form shell output.
- Validate repository documentation content only when requested, without invoking the static-site scenario or publishing a site.
- Add tests and docs so the workflow can be safely consumed by `riftonix/helm-shared`.

**Non-Goals:**

- Add GitHub Actions YAML to `riftonix/helm-shared` in this daggerverse change.
- Implement GitHub Releases, GitHub Pages, GitLab Pages, environments, deployment comments, or PR comment lifecycle inside Dagger.
- Render the external main documentation site from the chart repository.
- Introduce private runtime image defaults.
- Replace caller-owned branching, tagging, versioning, or registry repository policy.
- Implement a general markdown, link, or accessibility linter unless it is needed as a small documentation validation helper for this workflow.

## Decisions

1. Extend `scenarios/helm-ci` instead of creating a new scenario.

   The existing scenario already owns provider-neutral Helm chart orchestration and composes the correct low-level modules. Adding changed dev publish, release publish, unittest validation, and structured results there preserves a single workflow-facing module for chart repositories. A new `helm-shared-ci` scenario would overfit one downstream repository and duplicate most of the existing Helm CI surface.

2. Keep GitHub Actions as an adapter, not part of the Dagger contract.

   `helm-shared` will likely call this scenario from GitHub Actions, but the scenario will accept explicit refs, chart roots, run id or version suffix, registry destination, and credentials. It will not inspect `GITHUB_*`, `CI_*`, or provider event variables. This matches the existing static-site and Helm CI provider boundary.

3. Model chart selection as chart roots plus explicit diff mode.

   Pull request validation should use merge-base diff behavior against a caller-provided base ref. Release publication should compare a caller-provided previous ref against a caller-provided head ref. This avoids encoding `master`, `main`, `HEAD^`, or provider checkout assumptions in Dagger while still supporting the `helm-shared` default branch.

4. Treat application and library charts differently during verification.

   `helm lint` and dependency update apply to both chart types. `helm template` should run for application charts and be skipped for `type: library`, as the existing Helm module already does. This preserves current behavior and lets `libs/common` pass validation as a library chart.

5. Add Helm unittest as a separate module and compose it from Helm CI.

   `modules/helm-unittest` should wrap the public `helmunittest/helm-unittest` image and expose a small public API for running chart unit tests. `scenarios/helm-ci` should compose that module when unittest validation is enabled. A chart that contains a `tests` directory should run Helm unittest. A chart without `tests` should be marked as skipped for unittest and still pass the rest of verification. This keeps `modules/helm` focused on Helm CLI primitives and keeps unittest reusable for callers that do not need the full CI scenario.

6. Add multi-chart publication at the scenario layer.

   The Helm module should continue to own one-chart package and push primitives. The Helm unittest module should own one-chart unittest execution. The scenario should own selecting changed charts, computing dev versions, checking idempotency, and aggregating validation and publication results across charts. This keeps reusable tool modules small while giving CI one stable workflow function.

7. Return structured result objects or JSON-compatible records.

   Current changed verification returns a list of strings. New functions should return typed Dagger objects or JSON-compatible values containing chart path, chart name, chart version, action, status, message, package name, and OCI reference where applicable. Provider adapters can render summaries from these values without parsing command output.

8. Validate docs as repository content only.

   The `helm-shared` chart tree includes documentation content, but publication belongs to the main site that imports external component docs. Helm CI can validate that required documentation files exist, are non-empty when required, or are generated consistently if the repository defines such a check. It must not call `scenarios/static-site` for site rendering unless a future change explicitly adds a docs site to `helm-shared`.

9. Use public runtime defaults with mirror overrides.

   Helm and Git already default to public images. The Helm unittest module should default to the public `helmunittest/helm-unittest` image. Any documentation validation runtime must also default to a public image and expose prefixed runtime inputs so consumers can use mirrors without changing scenario behavior.

## Risks / Trade-offs

- Changed-chart detection may select directories that are not chart roots -> Validate `Chart.yaml` before running Helm and report skipped paths clearly.
- Release publication could republish existing chart versions -> Provide an idempotent mode that checks `is_already_published` before pushing and reports skipped existing versions.
- Helm unittest image tags can lag Helm tags -> Keep Helm and Helm unittest runtime inputs separate and test the default combination.
- Structured result objects can be awkward in Dagger CLI output -> Prefer simple JSON-compatible records or scenario-owned object types with stable primitive fields.
- Documentation validation requirements may be too weak at first -> Keep validation minimal and explicit, then add stronger doc checks in a future capability if `helm-shared` defines a concrete doc generation contract.
- GitHub default branch confusion between `main` and `master` can cause wrong diffs -> Require provider adapters to pass explicit refs and document `helm-shared` as using `master` for the current full chart tree.

## Migration Plan

1. Add the `modules/helm-unittest` module and tests.
2. Extend the Helm CI scenario API and tests in daggerverse.
3. Release or pin the updated modules and scenario version for downstream consumers.
4. Update `helm-shared` GitHub Actions to call the scenario with explicit `master` refs, chart roots `charts/*` and `libs/*`, and registry credentials.
5. Keep existing one-chart verification and publication functions available so existing callers are not forced to migrate immediately.

## Open Questions

- Which OCI registry and repository should `helm-shared` use for dev and release chart publication?
- Should dev publication be idempotent or always push a unique build-metadata version?
- Which documentation files are required for `helm-shared` charts, and should validation only check presence or also generated consistency?
- Should chart-testing be added in this change, or should Helm lint, template, dependency update, and unittest be the initial public workflow?
