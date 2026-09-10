## Context

`modules/hugo` currently runs `hugo mod get` and exposes module preparation functions. `scenarios/static-site` parses Hugo `module.imports` to inspect content contributed by separately supplied directories. The selected runtime image already provides Hugo, npm, Autoprefixer, and Sass tooling; only the site theme and its npm dependencies need to be installed from the committed lockfile.

## Goals / Non-Goals

**Goals:**

- Make Hugo build and validation independent of Go and Hugo Modules.
- Keep npm dependency resolution reproducible and script-free.
- Preserve path-neutral external content while moving composition into Dagger.
- Detect conflicting target files before rendering.

**Non-Goals:**

- Supporting both Hugo Modules and npm themes.
- Installing `sass-embedded` in each site when the runtime image supplies it.
- Fetching external content repositories inside the static-site scenario.

## Architecture and Component Boundaries

### Architecture Overview

The caller supplies the base site as `source` and parallel content mount arrays. Each mount combines a Dagger directory, a source path within that directory, a target path in the site, and a diagnostic contributor name at the same array index. The scenario validates all resulting target file paths, overlays each selected source directory onto a derived site directory, and constructs the Hugo module with that derived directory.

### Component Responsibilities

- The Hugo module validates npm manifests, executes `npm ci --ignore-scripts`, and runs Hugo.
- The static-site scenario validates and materializes content mounts before invoking Hugo.
- The site declares `@docsy/theme` and configures Hugo to resolve it from `node_modules`.
- The runtime image supplies globally installed build tools, including Sass.

### Component Boundaries

The scenario does not fetch repositories or infer component layouts. Callers provide each directory and mapping explicitly. The Hugo module does not inspect or manipulate content composition.

## Component Changes

### Hugo Module

Remove theme URL inputs and all `hugo mod` operations. Replace optional npm installation with a manifest check followed by unconditional lockfile installation for build and validation. Keep `with_npm_dependencies` as a public runtime inspection primitive used by tests.

### Static Site Scenario

Add constructor arrays for content sources, source paths, target paths, and contributor names. Replace config-based collision functions with mount-based collision functions. Build a derived source tree before creating `dag.hugo`.

## Interfaces

### Command-Line Interface

Hugo build and validation accept only `site_base_url` at function level. Static-site constructor calls repeat aligned content source, source path, target path, and contributor inputs. The theme URL argument is removed.

### Internal Interfaces

The parallel arrays expose `content_sources`, `content_source_paths`, `content_target_paths`, and `content_contributors`. Their lengths must match. Paths are normalized by stripping leading and trailing slashes. Empty source, target, or contributor values are rejected.

## Error Handling

### Error Categories

Missing npm manifests fail before npm or Hugo runs. Invalid mount paths and mismatched source directories fail during composition. Duplicate target files fail before Hugo runs and include all contributor mappings.

### Logging and Diagnostics

Collision messages retain the target file and contributor mappings so callers can identify which mount must change.

## Decisions

### Decision: Install only site-declared npm dependencies

The site declares `@docsy/theme`, while globally available compiler tooling remains owned by the image. This avoids duplicating `sass-embedded` in every lockfile. Installing the theme dynamically from a module argument was rejected because it would make the build state differ from the committed lockfile.

### Decision: Compose directories before Hugo execution

Dagger directory overlays replace Hugo Module mounts. This removes Go while preserving explicit source-to-target mappings. Copying content in CI scripts was rejected because it would duplicate composition behavior outside the reusable scenario.

### Decision: Use aligned mount input arrays

Aligned arrays use Dagger-supported constructor input types while retaining one explicit source, source path, target path, and contributor per index. A custom input object was rejected because Dagger object types are returned by module functions and cannot be constructed directly by dependent modules. Parsing Hugo configuration was rejected because the configuration can no longer resolve external directories without Hugo Modules.

## Risks / Trade-offs

- The site lockfile may omit tools expected by a newer Docsy release -> Keep the runtime image version pinned and validate the Docsy fixture against it.
- Directory overlays could silently replace files -> Enumerate target files and reject collisions before applying overlays.
- Removing APIs breaks existing workflows -> Release new module and scenario versions and require callers to migrate directly.

## Migration Plan

### Rollout

Update the Hugo module, static-site scenario, fixtures, specifications, and documentation together. Consumers then remove Go metadata, add npm manifests, configure Docsy from `node_modules`, and replace Hugo imports with content mounts.

### Backward Compatibility

No backward-compatible arguments or operations are retained.

### Rollback

Consumers can remain pinned to the previous released module and scenario versions until their sites are migrated.
