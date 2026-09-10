## ADDED Requirements

### Requirement: Lockfile-Pinned Npm Theme Dependencies
The Hugo module SHALL require `package.json` and `package-lock.json` in the site root and SHALL install the lockfile-pinned dependencies with lifecycle scripts disabled before build and validation.

#### Scenario: Site dependencies are installed
- **WHEN** a caller builds or validates a site with npm manifests
- **THEN** the module installs the exact dependencies from `package-lock.json` before invoking Hugo

#### Scenario: Missing npm manifest fails
- **WHEN** a caller builds or validates a site without `package.json` or `package-lock.json`
- **THEN** the module fails with an error identifying the missing required manifest

### Requirement: Go-Free Hugo Execution
The Hugo module SHALL build and validate sites without invoking Hugo Module commands or requiring Go module metadata.

#### Scenario: Npm-based Docsy site renders without Go metadata
- **WHEN** a valid site configures Docsy from `node_modules` and contains no `go.mod` or `go.sum`
- **THEN** the module renders and validates the site without invoking `hugo mod`

## REMOVED Requirements

### Requirement: No Runtime Npm Install in Normal Build
**Reason:** Npm installation is now the required mechanism for obtaining the site's lockfile-pinned theme dependencies.

**Migration:** Commit `package.json` and `package-lock.json` in the site root and declare `@docsy/theme` as a dependency.

### Requirement: Hugo Module Preparation
**Reason:** Hugo Module initialization and dependency resolution require Go and conflict with the Go-free site contract.

**Migration:** Remove site and content-module Go metadata, obtain themes through npm, and compose external content through the static-site scenario.

### Requirement: Content Module Path Neutrality
**Reason:** Content composition moves from Hugo Modules to the static-site scenario.

**Migration:** Keep source content path-neutral and pass it to the static-site scenario as an explicit content mount.

### Requirement: Multiple Hugo Module Roots
**Reason:** Independent Go-backed Hugo module roots are no longer prepared by the Hugo module.

**Migration:** Pass each external source directory directly to the static-site scenario with its source and target paths.
