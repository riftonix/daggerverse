## Why

Hugo sites currently use Go-backed Hugo Modules both to resolve Docsy and to compose documentation from component repositories. Docsy is available as the `@docsy/theme` npm package, and Dagger can compose external content directly, so requiring Go metadata and module resolution is unnecessary.

## What Changes

- **BREAKING** Remove `hugo_theme_url`, `init_module`, and `prepare_module` from the Hugo and static-site APIs.
- Require Hugo site sources to provide `package.json` and `package-lock.json`; install the lockfile-pinned npm dependencies before every build and validation.
- Configure Docsy as an npm theme through `theme: "@docsy/theme"` and `themesDir: node_modules` in the site configuration.
- **BREAKING** Replace Hugo `module.imports` content composition with explicit aligned Dagger content mount inputs supplied to the static-site scenario.
- Validate content mount paths and materialize mounted directories into the Hugo source tree before verification or rendering.
- Remove Go module files and Go-dependent test coverage from Hugo and static-site fixtures.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `hugo-module`: Replace Hugo Module preparation and theme resolution with lockfile-pinned npm dependency installation.
- `static-site-scenario`: Replace Hugo module imports with explicit Dagger content composition and remove the Hugo theme URL input.

## Impact

- Public APIs in `modules/hugo` and `scenarios/static-site` change incompatibly.
- Hugo sites must commit npm manifests and configure the theme from `node_modules`.
- Callers composing component documentation must pass content mount inputs rather than maintaining `go.mod` and `module.imports`.
- Tests, OpenSpec specifications, and documentation for both components require updates.
