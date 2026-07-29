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
- Publish one caller-selected release chart per `publish_chart` invocation using the version from `Chart.yaml` by default, with an optional explicit version override.
- Run Helm dependency update before release publication by default, with an explicit `with_dependency_update=false` opt-out for callers that use already prepared or vendored dependencies.
- Create release Git tags through the Git module within the same `publish_chart` invocation after successful release publication.
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

   The existing scenario already owns provider-neutral Helm chart orchestration and composes the correct low-level modules. Adding release publication, unittest validation, and structured results there preserves a single workflow-facing module for chart repositories. A new `helm-shared-ci` scenario would overfit one downstream repository and duplicate most of the existing Helm CI surface.

2. Keep GitHub Actions as an adapter, not part of the Dagger contract.

   `helm-shared` will likely call this scenario from GitHub Actions, but the scenario will accept explicit refs and chart roots for validation and explicit chart, registry, and Git inputs for publication. It will not inspect `GITHUB_*`, `CI_*`, or provider event variables. This matches the existing static-site and Helm CI provider boundary.

3. Model chart selection as provider workflow matrix preparation.

   Pull request validation uses `modules/git.get_changed_components` with explicit refs and component roots such as `charts/*` and `libs/*`. The provider workflow builds one matrix job per returned chart and supplies that chart directory as the Helm CI scenario-level `source`. This avoids encoding `master`, `main`, `HEAD^`, provider checkout assumptions, repository-specific root expansion, or multi-chart log aggregation in Helm CI.

   Example changed validation call:

   ```bash
   dagger -m ./scenarios/helm-ci call \
     --source=charts/app \
     verify-chart \
     --release-name=ci-release
   ```

4. Treat application and library charts differently during verification.

   `helm lint` and dependency update apply to both chart types. `helm template` should run for application charts and be skipped for `type: library`, as the existing Helm module already does. This preserves current behavior and lets `libs/common` pass validation as a library chart.

5. Add Helm unittest as a separate module and compose it from Helm CI.

   `modules/helm-unittest` should wrap the public `helmunittest/helm-unittest` image and expose a small public API for running chart unit tests. `scenarios/helm-ci` should auto-detect Helm unittest suites without requiring a public enable or disable flag. A chart that contains suite files under `tests/` should run Helm unittest. A chart without suite files under `tests/` should skip unittest and still pass the rest of verification. This keeps `modules/helm` focused on Helm CLI primitives and keeps unittest reusable for callers that do not need the full CI scenario.

6. Create release tags through the Git module, not provider APIs.

   `publish_chart` is the single release entrypoint. It checks the chart-scoped release tag before registry login or chart publication. An existing tag means the release is already complete, so the function returns a successful no-op without publishing or tagging again. When the tag is missing, one invocation publishes one caller-selected chart and only then calls the Git module's `ensure_pushed_tag` function. This keeps tagging provider-neutral, avoids separate Dagger calls, and avoids GitHub-specific release APIs. If the repository token lacks permission to create or push the tag after publication, the workflow should fail.

   Registry credentials use explicit `registry_login` and `registry_password` inputs. `git_token` remains separate because it authenticates release tag operations rather than OCI publication.

7. Use chart-scoped release tags.

   A repository can publish multiple charts independently, so release tags should include chart scope rather than using only `v<version>`. `publish_chart` accepts a caller-provided `git_tag_prefix` and computes `<git-tag-prefix>/v<chart-version>`, allowing `charts/appchart/v1.2.3` and `libs/common/v1.2.3` to coexist.

   The same prefix is preserved as the OCI chart repository path. With `oci_base_url=ghcr.io/riftonix`, `charts/appchart` publishes under `ghcr.io/riftonix/charts/appchart`, `libs/common` publishes under `ghcr.io/riftonix/libs/common`, and `libs/test/common` publishes under `ghcr.io/riftonix/libs/test/common`. This keeps repository-specific shell parsing out of provider workflows.

8. Separate repository and chart directory inputs without path reconstruction.

   Scenario-level `source` remains the full Git repository directory and is always passed to the Git module. `verify_chart` and `publish_chart` accept optional `chart_source: dagger.Directory | None` and resolve Helm input as `chart_source or self.source`. This avoids adding string chart path handling or changing the Helm module mount model. The caller supplies a Dagger directory for a nested chart when needed. Local Helm dependencies outside that directory remain unsupported by this model.

9. Return a structured publication result.

    Validation workflows can remain fail-fast and use normal command failures for lint, template, and unittest checks. `publish_chart` needs a typed Dagger object or JSON-compatible value containing chart path, chart name, chart version, published version, action, status, message, package name, release tag, and registry-visible OCI fields when available. Provider adapters can render summaries from this value without parsing command output. The returned value must not include registry credentials or secret-derived values.

    Example publication result:

    ```json
    {
        "chart_path": "charts/appchart",
        "chart_name": "appchart",
        "chart_version": "1.2.3",
        "published_version": "1.2.3",
        "status": "published",
        "action": "release_published",
        "package_name": "appchart-1.2.3.tgz",
        "oci_reference": "oci://ghcr.io/riftonix/charts/appchart:1.2.3",
        "oci_registry": "ghcr.io",
        "oci_repository": "riftonix/charts/appchart",
        "oci_tag": "1.2.3",
        "oci_digest": "sha256:0123456789abcdef",
        "release_tag": "charts/appchart/v1.2.3",
        "message": "Release chart published and tagged",
        "warnings": []
    }
    ```

10. Validate docs as repository content only.

    The `helm-shared` chart tree includes documentation content, but publication belongs to the main site that imports external component docs. Helm CI can validate that required documentation files exist, are non-empty when required, or are generated consistently if the repository defines such a check. It must not call `scenarios/static-site` for site rendering unless a future change explicitly adds a docs site to `helm-shared`.

11. Use public runtime defaults with mirror overrides.

   Helm and Git already default to public images. The Helm unittest module should default to the public `helmunittest/helm-unittest` image. Any documentation validation runtime must also default to a public image and expose prefixed runtime inputs so consumers can use mirrors without changing scenario behavior.

## Risks / Trade-offs

- Changed-chart detection may select directories that are not chart roots -> Validate `Chart.yaml` before running Helm and report skipped paths clearly.
- A chart can be published but its Git tag push can still fail -> Fail the call and leave recovery to a later explicit invocation; OCI and Git operations cannot be transactional.
- Release tag creation can fail because the provider token lacks permission -> Let the workflow fail so repository permissions are fixed explicitly.
- Existing release tags identify an already-completed release -> Check before registry login or publication and return a successful no-op.
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
6. Keep the provider workflow responsible for selecting one chart per release publication job.

## Open Questions

- Which OCI registry and repository should `helm-shared` use for release chart publication?
- Should the chart-scoped release tag format be fixed to `<chart-path>/v<chart-version>` or made caller-configurable with that default?
- Which documentation files are required for `helm-shared` charts, and should validation only check presence or also generated consistency?
- Should chart-testing be added in this change, or should Helm lint, template, dependency update, and unittest be the initial public workflow?
