## 1. Scenario and runtime

- [x] 1.1 Add the Python SDK scenario under `scenarios/go-ci` with repository-aligned Dagger metadata and one public workflow, `verify-app`; confirm the CLI help exposes the required `source` and `package` inputs and no publication function.
- [x] 1.2 Configure the pinned, Renovate-managed Go runtime, split image overrides, separate Go caches, `GOTOOLCHAIN=local`, and `GOWORK=off`; verify a compatible override works and an image below the module's Go minimum fails with a toolchain diagnostic.

## 2. Verification behavior

- [x] 2.1 Validate the root `go.mod` and single local `main` package; cover a missing manifest, missing or non-`main` package, path escape, and package pattern with negative tests.
- [x] 2.2 Check formatting without writing to the source tree; cover a formatted project and an unformatted file whose path appears in the diagnostic.
- [x] 2.3 Run `go test ./...` and compile the selected application without exporting it; cover a successful plain source fixture with a `go:embed` input, a failing test in another package, and a selected `main` package that fails executable compilation after tests pass.

## 3. Tests and documentation

- [x] 3.1 Add `scenarios/go-ci/tests` with a local scenario dependency, source fixtures, and a no-argument `all` entrypoint; verify the suite through `make tests scenario go-ci` when explicitly authorized to run Dagger, or hand off that exact command.
- [x] 3.2 Document `verify-app` in the scenario README, including toolchain override behavior and copyable calls for `kelm` and `kafgres` without registry credentials; link the repository authoring guide.

## 4. GitHub Actions adoption

- [x] 4.1 Open SHA-pinned preview pull requests for both applications and record the CI results: `kafgres` passed; `kelm` reported missing `go.sum` entries.
- [x] 4.2 Update `.github/workflows/ci.yaml` in both preview pull requests to call `verify-app` once with their respective package paths and reject a failed, cancelled, or skipped verification in `CI Passed`.
- [x] 4.3 Update the GitHub reference regex in both consumers' `renovate.json` and verify extraction and replacement from `@scenarios/go-ci/v1.0.0` to `@scenarios/go-ci/v1.0.1`, and that a `helm-ci` tag is ignored. The test values do not select a release. The release pins and their annotations move to `extract-go-module`.
