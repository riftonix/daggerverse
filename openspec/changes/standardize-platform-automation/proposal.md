## Why

Riftonix repositories repeat the same Renovate rules, GitHub Actions workflow structure, Dagger setup, local `act` handling, and Makefile command wrappers with small repository-specific edits. This makes the organization harder to present as a platform engineering demo because every consumer repository owns low-level automation details instead of consuming a paved road.

## What Changes

- Add a reusable platform automation layer for Riftonix repositories.
- Introduce organization-level Renovate presets that can be composed by repository type and technology stack.
- Introduce reusable GitHub Actions workflows for common Riftonix CI and publication paths.
- Introduce small composite GitHub Actions for repeated step-level behavior such as Dagger setup, local `act` source detection, and required job result checks.
- Keep Dagger modules and scenarios responsible for portable build, verify, render, and publish logic.
- Keep repository workflows responsible for repository-specific events, branch/path filters, permissions, concurrency, and inputs.
- Migrate repository-local Makefile command wrappers to GitHub Actions workflows runnable both in GitHub and through `act`.
- Add migration documentation and examples for `riftonix.github.io`, `container-images`, `daggerverse`, and older Go/Terraform/Helm repositories.
- **BREAKING**: The Daggerverse repository command interface will no longer treat the root `Makefile` as the long-term supported automation interface after equivalent workflows and `act` usage are available.

## Capabilities

### New Capabilities

- `platform-automation`: Defines shared Renovate presets, reusable GitHub Actions workflows, composite actions, local `act` support, and consumer repository conventions for Riftonix platform automation.

### Modified Capabilities

- `daggerverse`: Update repository automation expectations so local and CI workflows are exposed through GitHub Actions and `act` instead of depending on a root Makefile as the stable interface.

## Impact

- Affected code: new automation repository or organization `.github` repository, repository Renovate configs, repository workflow files, local `act` configuration, Daggerverse docs, and Daggerverse OpenSpec baseline.
- API impact: consumer repositories will call reusable workflows and Renovate presets by versioned references instead of copying full workflow and Renovate JSON bodies.
- CI impact: GitHub Actions workflows become the primary entrypoint for both hosted CI and local `act` runs; Dagger remains the execution engine for portable domain logic.
- Repository impact: Makefile targets in participating repositories will be removed or demoted after equivalent reusable workflows exist.
- Migration impact: existing repositories need a staged migration so required branch checks, release publishing, Renovate automerge behavior, and local developer workflows remain available during the transition.
