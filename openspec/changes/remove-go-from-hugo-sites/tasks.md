## 1. Hugo Runtime

- [x] 1.1 Remove Hugo Module and theme URL APIs from `modules/hugo` and verify generated module code has no `hugo mod` invocation.
- [x] 1.2 Require npm manifests and run `npm ci --ignore-scripts` before build and validation; verify focused tests cover installation and missing manifests.

## 2. Static Site Composition

- [x] 2.1 Add typed external content mounts and compose them into the site source before invoking Hugo; verify composed files appear under selected target paths.
- [x] 2.2 Replace Hugo config import collision validation with explicit mount collision validation; verify unique paths pass and duplicate paths identify contributors.
- [x] 2.3 Remove `hugo_theme_url` from the static-site API and verify Hugo operations delegate with only runtime and base URL inputs.

## 3. Tests and Fixtures

- [x] 3.1 Convert Hugo and static-site Docsy fixtures to `@docsy/theme` npm manifests and `node_modules` theme configuration; verify no fixture contains Go metadata.
- [x] 3.2 Rewrite Hugo module tests for npm theme installation and Go-free rendering; verify the component test command exercises the updated contract.
- [x] 3.3 Rewrite static-site scenario tests for explicit content composition and collisions; verify the scenario test command exercises the updated contract.

## 4. Contracts and Documentation

- [ ] 4.1 Update main Hugo and static-site specifications to describe the implemented npm and Dagger composition behavior; verify they contain no current Hugo Module requirements. Deferred to OpenSpec archive, which applies the validated delta specs.
- [x] 4.2 Update module, scenario, and repository documentation and command examples; verify documented APIs, image tags, and site layouts match implementation.

## 5. Verification

- [x] 5.1 Run OpenSpec strict validation, formatting, linting, and available fast unit checks and resolve reported issues.
- [x] 5.2 Provide the exact repository Dagger integration test commands for user execution because those tests start containers.
