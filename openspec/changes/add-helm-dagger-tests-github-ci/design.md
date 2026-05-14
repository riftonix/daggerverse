# Design

## Context

The Helm module currently has shell smoke tests under `modules/helm/tests/test.sh`. The new test pattern follows the Dagger module testing practice from the current Dagger documentation: create a neighboring test module, install the parent module as a local dependency, call the parent module public API from test functions, and expose an `all` function for CI.

The repository also needs to standardize this change on Dagger `0.20.6`, including module metadata and GitHub Actions.

## Decisions

### Repository Command Interface

Use the root `Makefile` as the primary command interface for supported local and CI workflows. Module-specific commands use a positional module argument, for example `make lint helm`, `make format helm`, and `make tests helm`.

CI should call the same `Makefile` targets that developers use locally instead of embedding raw `dagger call` commands directly in workflow steps. Direct tool commands remain useful for debugging, but the documented and expected path is through `make`.

### Helm Test Module

Create `modules/helm/tests` as a Dagger test module. It depends on the parent Helm module through `dagger install ..`, so test code calls `dag.helm()` rather than shelling out to `dagger call` against the parent module.

Use the existing fixture chart at `modules/helm/tests/charts/ns-configurator`.

### Push And Publication Lookup Tests

Cover `push` and `is_already_published` as integration-style tests against an ephemeral local OCI registry service. Do not push to GitHub Container Registry from pull request CI.

The test module should start a registry container as a Dagger service, bind it into the Helm module's Helm container, log in with test credentials if the selected registry setup requires authentication, push the packaged chart to the local registry, then verify the pushed version through `is_already_published`.

This keeps the test deterministic and avoids requiring `GITHUB_TOKEN` or any external registry state in pull requests.

### CI Scope

The first CI workflow runs the Helm test module aggregate function through `make tests helm`. It should be structured so additional module test calls can be added later, but it must not fail because other modules do not yet have Dagger test modules.

### Legacy Shell Test

Keep `modules/helm/tests/test.sh` until the Dagger-native test module and CI are implemented and validated. After that, remove the shell test so there is one canonical test path for Helm.

## Open Questions

- Whether the local OCI registry test needs authentication depends on the chosen registry image and Helm behavior. Prefer the simplest registry setup that validates push and lookup without external secrets.
