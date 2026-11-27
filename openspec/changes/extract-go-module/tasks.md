## 1. Reusable Go module

- [ ] 1.1 Add the Python SDK module under `modules/go` with repository-aligned metadata, a Renovate-managed image, and a `container_user_id` override. Verify separate writable caches and temporary paths with the default and a distinct numeric UID, and verify a compatible image override and a below-minimum toolchain diagnostic.
- [ ] 1.2 Extract `validate-package`, `check-format`, `test`, and `build`. Exercise each through `modules/go/tests`: package and manifest errors, formatting diagnostics and exclusions, failure in a sibling package's tests, an embedded build input, and a link failure after successful tests.
- [x] 1.3 Document standalone Go module calls and runtime inputs in `modules/go/README.md`; verify the examples use the public module API.

## 2. Compose Go CI

- [x] 2.1 Add the local Go dependency to `scenarios/go-ci` and delegate the checks in order. Verify that `verify-app` remains the only public workflow and preserves the existing source, package, diagnostics, and summary contract.
- [ ] 2.2 Expose `go_container_user_id` and pass it to the module with the existing Go image inputs. Verify the default and overridden UID through the scenario API and update the scenario README.
- [ ] 2.3 Run `make tests module go`, `make tests scenario go-ci`, and the repository's quality checks. Obtain authorization for Dagger runs when required; verify both components are discovered by normal repository CI.

## 3. Release and adoption

- [ ] 3.1 Diagnose the missing `go.sum` entries in [kelm #36](https://github.com/riftonix/kelm/pull/36) and update its dependency metadata as needed. Verify `verify-app` succeeds without weakening the checksum checks.
- [ ] 3.2 After the module and scenario are merged and verified, select and publish a `scenarios/go-ci/vX.Y.Z` tag through `make release` with authorization for the selected tag. Confirm the remote tag resolves to the expected scenario and local Go module.
- [ ] 3.3 Replace the SHA pins in [kelm #36](https://github.com/riftonix/kelm/pull/36) and [kafgres #27](https://github.com/riftonix/kafgres/pull/27) with the release tag and add the Renovate annotations. Verify version replacement preserves `v`, ignores unrelated component tags, and leaves one read-only `verify-app` call per workflow.
- [ ] 3.4 Verify both consumer PRs pass `Verify Go application` and `CI Passed` on the released tag, and check that `CI Passed` rejects failed, cancelled, and skipped verification. Complete adoption when the consumer PRs are approved for merge.
