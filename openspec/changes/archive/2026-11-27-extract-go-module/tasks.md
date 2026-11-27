## 1. Reusable Go module

- [x] 1.1 Add the Python SDK module under `modules/go` with repository-aligned metadata, a Renovate-managed image, and a `container_user_id` override. Verify separate writable caches and temporary paths with the default and a distinct numeric UID, and verify a compatible image override and a below-minimum toolchain diagnostic.
- [x] 1.2 Extract `validate-package`, `check-format`, `test`, and `build`. Exercise each through `modules/go/tests`: package and manifest errors, formatting diagnostics and exclusions, failure in a sibling package's tests, an embedded build input, and a link failure after successful tests.
- [x] 1.3 Document standalone Go module calls and runtime inputs in `modules/go/README.md`; verify the examples use the public module API.

## 2. Compose Go CI

- [x] 2.1 Add the local Go dependency to `scenarios/go-ci` and delegate the checks in order. Verify that `verify-app` remains the only public workflow and preserves the existing source, package, diagnostics, and summary contract.
- [x] 2.2 Expose `go_container_user_id` and pass it to the module with the existing Go image inputs. Verify the default and overridden UID through the scenario API and update the scenario README.
- [x] 2.3 Verify that normal repository CI discovers both components and passes `make tests module go`, `make tests scenario go-ci`, and the quality checks. See [Daggerverse CI](https://github.com/riftonix/daggerverse/actions/runs/45970654393).

## 3. Release and adoption

- [x] 3.1 Publish `scenarios/go-ci/v0.1.0` after the module and scenario pass CI. Confirm the remote tag resolves to the commit containing both components.
- [x] 3.2 Replace the SHA pin in [kafgres #27](https://github.com/riftonix/kafgres/pull/27) with the release tag and add the Renovate annotation. Verify version replacement preserves `v`, ignores unrelated component tags, and leaves one read-only `verify-app` call in the workflow.
- [x] 3.3 Verify Kafgres passes `Verify Go application` and `CI Passed` on the released tag, check that the gate rejects failed, cancelled, and skipped verification, and confirm the workflow is merged into `master`.
