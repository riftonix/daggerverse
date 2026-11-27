# Extract a Reusable Go Module and Release Go CI Design

## Context

The [Go CI baseline](../../specs/go-ci-scenario/spec.md) defines the checks already provided by `verify-app`. The [preview rollout](../archive/2026-11-27-add-go-ci/design.md#rollout) stopped at two open consumer pull requests using the same commit SHA. Kafgres passed; Kelm reached `go test ./...` and reported missing `go.sum` entries.

## Goals / Non-Goals

- Follow the local dependency and constructor conventions used by `helm-ci` and `static-site`. Keep the current scenario call shape and verification semantics when the new user input is omitted.
- Keep GitHub event handling and checkout in the consumers' YAML. Keep release and Renovate policy outside both Dagger components.

## Architecture and Component Boundaries

| Component | Responsibility |
| --- | --- |
| `modules/go` | Owns the Go image, UID, cache and source setup; exposes `validate-package`, `check-format`, `test`, and `build` as separate operations. |
| `scenarios/go-ci` | Declares `../../modules/go` as a local `go` dependency. Forwards the source and `go_*` runtime inputs. Calls the four operations in order and returns the existing verification summary. |
| Consumer CI | Owns checkout, the Dagger CLI and scenario pins, and the `CI Passed` gate. |

## Decisions

### Decision: Extract tool behavior into a local Python SDK module

Move the existing Go commands, package validation, mount setup, and step diagnostics into the new module. Keep the source tree available in each operation, including vendor and embed inputs. Keep the verification-only `go build -o` output on a temporary path and materialize each requested operation before returning; there is no need to introduce a binary artifact API for this flow. Each operation can be called standalone. A standalone build validates its target; the scenario can also validate upfront so a bad package still fails before formatting or tests.

Use the Python SDK and matching engine metadata, with neighboring test modules that call their parent modules through local dependencies. Keep raw Go invocations in `modules/go`; the scenario is responsible for ordering and its public summary. A local module fits the existing composition pattern and keeps the runtime, path validation, and formatting behavior under the same contract. An external Go wrapper would still leave the repository responsible for those checks and for matching its user and cache conventions.

### Decision: Pass the UID through and make the runtime writable for that user

Keep the current pinned public image and prefixed image overrides. Follow the repository's [runtime image conventions](../../../docs/reference/runtime-images.md): the module exposes `container_user_id`, the scenario exposes `go_container_user_id`, and duplicate image defaults use the same Renovate metadata. Use `65532` as the proposed default, matching neighboring modules. Apply the UID to all check commands and set a writable home and temporary build location; set `GOMODCACHE` and `GOCACHE` explicitly and give the selected UID access to each cache. If cache ownership is UID-specific, scope cache keys by UID so switching users does not reuse an incompatible mount. Verify the default and a distinct numeric UID, including one without an image-local account.

Keep `GOTOOLCHAIN=local` and `GOWORK=off`. Keep `-buildvcs=false` on test and build. A missing or inconsistent dependency checksum remains a Go error rather than causing the verifier to rewrite `go.mod` or `go.sum`.

### Decision: Roll forward through the existing consumer pull requests

Review Kelm's Go module requirements and checksums at the PR head to identify why Go reports missing `go.sum` entries. Commit the necessary dependency metadata correction in Kelm and verify the resulting diff. Do not change the verifier to bypass module integrity checks.

After the module and scenario are verified on `master`, publish the selected `scenarios/go-ci/vX.Y.Z` tag through the repository's `make release` workflow. The local module is included in the tagged repository snapshot; consumer workflows only reference the scenario tag. Update each open consumer PR from its temporary SHA to the released tag and add:

```text
# renovate: datasource=github-tags depName=riftonix/daggerverse versioning=semver extractVersion=^scenarios/go-ci/v(?<version>.*)$
```

Retain the preview PRs' GitHub-reference regex fix, the numeric Dagger pin, and `permissions: contents: read`. Keep `needs: verify`, `if: ${{ always() }}`, and the explicit `success` check on the `CI Passed` job. Use one scenario call per app and verify both PRs before merging the consumer workflows.

## Risks / Trade-offs

- The default Go image and image overrides can have root-owned home or cache paths. The explicit UID, home and cache configuration must be exercised in the contract suite so image selection remains usable.
- The Kelm error is currently observed on the preview branch. Verify the cause and the fix on that branch before treating consumer rollout as complete.

## Migration Plan

- Existing `verify-app` callers keep their arguments; the user override is optional. SHA-pinned consumers move to the released tag and its Renovate annotation together.
- If adoption must be rolled back after merge, revert the affected downstream workflow change. Published tags stay immutable.
