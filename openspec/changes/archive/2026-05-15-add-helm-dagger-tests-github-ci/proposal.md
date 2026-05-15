# Add Helm Dagger Tests And GitHub PR CI

## Summary

Add the first Dagger-native test module for `modules/helm` and connect GitHub pull request CI so changes targeting the repository default branch run the available module tests.
Make the root `Makefile` the primary local and CI command interface for module checks, starting with `make tests helm`.

## Motivation

The repository currently keeps shell-based smoke tests close to some modules, but it does not yet follow the Dagger module testing practice documented for Dagger 0.20.6: a test Dagger module located next to the module under test and depending on its parent module.

Starting with `helm` gives the repository a concrete pattern for future module tests without making untested modules block pull requests before their test modules exist.

## Scope

- Add a Dagger test module under `modules/helm/tests`.
- Move Helm module checks into Dagger test functions that call the parent Helm module through its public API.
- Cover Helm OCI push and publication lookup with a local registry service instead of GitHub Container Registry.
- Add GitHub Actions CI for pull requests targeting the repository default branch.
- Run available module test modules in CI through the root `Makefile`.
- Use simple root `Makefile` commands as the canonical local and CI entrypoint for supported module workflows, including lint, format, and tests.
- Keep modules without test modules non-blocking until their tests are added.
- Upgrade this repository's Dagger module metadata and CI to Dagger `0.20.6`.
- Document the Dagger-native testing practice in OpenSpec so future module tests follow the same structure.

## Out Of Scope

- Release automation.
- Daggerverse publishing/tag management.
- Test modules for `git`, `hugo`, `kind`, `opentofu`, `pipelines`, or `ssh`.
- A repository-wide affected-module resolver inside Dagger.
- Pull request CI pushes to GitHub Container Registry.

## Affected Components

- Component: `daggerverse`
  - Source: `github.com/riftonix/daggerverse`
  - Reason: Owns the reusable Dagger module repository layout, module tests, and GitHub CI workflow.
  - Impact: Adds a Dagger-native test pattern for modules and enables pull request validation for available tests.
