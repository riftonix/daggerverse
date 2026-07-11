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
- Publish changed dev charts from pull request workflows with caller-provided build metadata and changed release charts with the version from `Chart.yaml`.
- Support cleanup of pull-request development chart versions through OCI registry APIs when provider workflows request cleanup.
- Create release Git tags through the Git module after successful release publication when a chart version is raised by a default-branch merge.
- Return structured results that provider adapters can turn into summaries, comments, or logs without parsing free-form shell output.
- Validate repository documentation content only when requested, without invoking the static-site scenario or publishing a site.
- Add tests and docs so the workflow can be safely consumed by `riftonix/helm-shared`.

**Non-Goals:**

- Add GitHub Actions YAML to `riftonix/helm-shared` in this daggerverse change.
- Implement GitHub Releases, GitHub Pages, GitLab Pages, environments, deployment comments, or PR comment lifecycle inside Dagger.
- Implement cleanup through the GitHub Packages API or other provider-specific package APIs.
- Render the external main documentation site from the chart repository.
- Introduce private runtime image defaults.
- Replace caller-owned branching, tagging, versioning, or registry repository policy.
- Implement a general markdown, link, or accessibility linter unless it is needed as a small documentation validation helper for this workflow.

## Decisions

1. Extend `scenarios/helm-ci` instead of creating a new scenario.

   The existing scenario already owns provider-neutral Helm chart orchestration and composes the correct low-level modules. Adding changed dev publish, release publish, unittest validation, and structured results there preserves a single workflow-facing module for chart repositories. A new `helm-shared-ci` scenario would overfit one downstream repository and duplicate most of the existing Helm CI surface.

2. Keep GitHub Actions as an adapter, not part of the Dagger contract.

   `helm-shared` will likely call this scenario from GitHub Actions, but the scenario will accept explicit refs, chart roots, run id or version suffix, registry destination, and credentials. It will not inspect `GITHUB_*`, `CI_*`, or provider event variables. This matches the existing static-site and Helm CI provider boundary.

3. Model chart selection as caller-provided chart component roots plus explicit diff mode.

   Pull request validation should use merge-base diff behavior against a caller-provided base ref. Release publication should compare a caller-provided previous ref against a caller-provided head ref. The caller provides glob-like chart component roots, for example `charts/*` and `libs/*`, through repeatable `charts_path` inputs. The scenario passes those roots to the Git module for changed component detection, then validates or publishes the returned chart component directories. This avoids encoding `master`, `main`, `HEAD^`, provider checkout assumptions, or repository-specific root expansion in Dagger while still supporting the `helm-shared` default branch.

   Example changed validation call:

   ```bash
   dagger -m ./scenarios/helm-ci call verify-charts \
     --source=. \
     --base-ref=origin/master \
     --head-ref=HEAD \
     --charts-path='charts/*' \
     --charts-path='libs/*' \
     --release-name=ci-release
   ```

4. Treat application and library charts differently during verification.

   `helm lint` and dependency update apply to both chart types. `helm template` should run for application charts and be skipped for `type: library`, as the existing Helm module already does. This preserves current behavior and lets `libs/common` pass validation as a library chart.

5. Add Helm unittest as a separate module and compose it from Helm CI.

   `modules/helm-unittest` should wrap the public `helmunittest/helm-unittest` image and expose a small public API for running chart unit tests. `scenarios/helm-ci` should auto-detect Helm unittest suites without requiring a public enable or disable flag. A chart that contains suite files under `tests/` should run Helm unittest. A chart without suite files under `tests/` should skip unittest and still pass the rest of verification. This keeps `modules/helm` focused on Helm CLI primitives and keeps unittest reusable for callers that do not need the full CI scenario.

6. Add multi-chart publication at the scenario layer.

    The Helm module should continue to own one-chart package and push primitives. The Helm unittest module should own one-chart unittest execution. The scenario should own selecting changed charts, computing dev versions, checking idempotency, and aggregating validation and publication results across charts. This keeps reusable tool modules small while giving CI one stable workflow function.

7. Allow pull request workflows to publish development chart versions.

   Development publication is useful before merge when downstream consumers need to install or test the exact chart changes from a pull request. Provider workflows may call development publication after changed-chart validation succeeds on pull request events. The provider supplies refs, registry destination, credentials, and build metadata such as `pr.<number>.run.<run>.sha.<short-sha>`. The scenario computes chart versions as `<chart-version>+<build-metadata>` and returns registry-visible references so workflow summaries can point to the published artifacts.

8. Clean pull request development versions through OCI registry APIs.

   Development artifacts should be removable when the pull request closes. Cleanup should be provider-neutral and operate through the OCI registry API rather than the GitHub Packages API. Provider workflows remain responsible for deciding when cleanup runs, for example on `pull_request.closed` or by manual retry with a pull request number. The cleanup operation should select development versions by a caller-provided marker such as `pr.<number>` and must not delete release versions. If direct OCI registry API usage needs a containerized tool, a reusable module based on `skopeo` may be added for listing and deleting OCI tags or manifests.

9. Create release tags through the Git module, not provider APIs.

   Release publication after a default-branch merge should be automatic when the provider workflow calls the release publication function and the chart version was raised. For each successfully published chart version, the scenario should create and push a Git tag through the Git module. This keeps tagging provider-neutral and avoids GitHub-specific release or package APIs. If the repository token lacks permission to create or push the tag, the workflow should fail. If the target tag already exists, the workflow should fail instead of silently skipping, because an existing tag for a newly detected version bump indicates an inconsistent release state.

10. Use chart-scoped release tags.

   A repository can publish multiple charts independently, so release tags should include chart scope rather than using only `v<version>`. A stable default format such as `<chart-path>/v<chart-version>` allows `charts/appchart/v1.2.3` and `libs/common/v1.2.3` to coexist. The scenario may expose an override for tag formatting only if the implementation can keep the default safe and deterministic.

11. Return structured publication and cleanup result objects or JSON-compatible records.

    Validation workflows can remain fail-fast and use normal command failures for lint, template, and unittest checks. Publication and cleanup workflows need typed Dagger objects or JSON-compatible values containing chart path, chart name, chart version, published version, action, status, message, package name, release tag where applicable, and registry-visible OCI fields: `oci_reference`, `oci_registry`, `oci_repository`, `oci_tag`, and `oci_digest` when available. Functions should return deterministic ordered lists of result records rather than dictionaries keyed by chart path, OCI repository, or tag. Provider adapters can render summaries and cleanup logs from these values without parsing command output. Returned values must not include registry credentials or secret-derived values.

    Example publication result list:

    ```json
    [
      {
        "chart_path": "charts/appchart",
        "chart_name": "appchart",
        "chart_version": "1.2.3",
        "published_version": "1.2.3+pr.42.run.100.sha.abc1234",
        "status": "published",
        "action": "dev_published",
        "package_name": "appchart-1.2.3+pr.42.run.100.sha.abc1234.tgz",
        "oci_reference": "oci://ghcr.io/riftonix/charts/appchart:1.2.3_pr.42.run.100.sha.abc1234",
        "oci_registry": "ghcr.io",
        "oci_repository": "riftonix/charts/appchart",
        "oci_tag": "1.2.3_pr.42.run.100.sha.abc1234",
        "oci_digest": "sha256:0123456789abcdef",
        "release_tag": "",
        "message": "Development chart published",
        "warnings": []
      }
    ]
    ```

12. Validate docs as repository content only.

    The `helm-shared` chart tree includes documentation content, but publication belongs to the main site that imports external component docs. Helm CI can validate that required documentation files exist, are non-empty when required, or are generated consistently if the repository defines such a check. It must not call `scenarios/static-site` for site rendering unless a future change explicitly adds a docs site to `helm-shared`.

13. Use public runtime defaults with mirror overrides.

   Helm and Git already default to public images. The Helm unittest module should default to the public `helmunittest/helm-unittest` image. Any documentation validation runtime must also default to a public image and expose prefixed runtime inputs so consumers can use mirrors without changing scenario behavior.

## Risks / Trade-offs

- Changed-chart detection may select directories that are not chart roots -> Validate `Chart.yaml` before running Helm and report skipped paths clearly.
- Release publication could republish existing chart versions -> Provide an idempotent mode that checks `is_already_published` before pushing and reports skipped existing versions.
- Release tag creation can fail because the provider token lacks permission -> Let the workflow fail so repository permissions are fixed explicitly.
- Existing release tags can indicate already-completed or inconsistent releases -> Fail when a release tag already exists for a detected version bump instead of skipping tag creation.
- Pull request development publications can leave stale artifacts after failed cleanup -> Support explicit cleanup by pull request marker so provider workflows can retry cleanup manually, including from local `act` runs.
- OCI tag normalization can differ from SemVer build metadata -> Return registry-visible references and have cleanup match the marker in registry-visible tags or metadata.
- Helm unittest image tags can lag Helm tags -> Keep Helm and Helm unittest runtime inputs separate and test the default combination.
- Structured result objects can be awkward in Dagger CLI output -> Prefer simple JSON-compatible records or scenario-owned object types with stable primitive fields.
- Documentation validation requirements may be too weak at first -> Keep validation minimal and explicit, then add stronger doc checks in a future capability if `helm-shared` defines a concrete doc generation contract.
- GitHub default branch confusion between `main` and `master` can cause wrong diffs -> Require provider adapters to pass explicit refs and document `helm-shared` as using `master` for the current full chart tree.

## Migration Plan

1. Add the `modules/helm-unittest` module and tests.
2. Extend the Helm CI scenario API and tests in daggerverse.
3. Release or pin the updated modules and scenario version for downstream consumers.
4. Update `helm-shared` GitHub Actions to call the scenario with explicit `master` refs, chart roots `charts/*` and `libs/*`, and registry credentials.
5. Ensure the release workflow passes Git credentials that can create and push chart-scoped release tags.
6. Add `helm-shared` provider workflow cleanup on pull request close and a manual retry path that can be invoked with a pull request number, including from local `act` runs.
7. Keep existing one-chart verification and publication functions available so existing callers are not forced to migrate immediately.

## Open Questions

- Which OCI registry and repository should `helm-shared` use for dev and release chart publication?
- Should dev publication be idempotent or always push a unique build-metadata version?
- Which OCI registry API capabilities are available for deleting pull-request development chart versions, and is a `skopeo` module needed for portable cleanup?
- Should the chart-scoped release tag format be fixed to `<chart-path>/v<chart-version>` or made caller-configurable with that default?
- Which documentation files are required for `helm-shared` charts, and should validation only check presence or also generated consistency?
- Should chart-testing be added in this change, or should Helm lint, template, dependency update, and unittest be the initial public workflow?
