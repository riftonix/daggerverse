# Static Site Scenario Reference

`scenarios/static-site` provides provider-neutral static-site verification and
rendering. Hugo is the first supported engine, and future engines can be added
behind the same scenario-level command shape.

## Scope

The public scenario API is limited to common static-site operations:

- verify a site directory with an explicit `site_base_url`
- render a site directory and return the generated static output
- validate Hugo virtual mount collisions from a Hugo YAML module import layout

Engine-specific operations remain in engine modules. For example, Hugo module
initialization and dependency resolution stay in `modules/hugo`.

## Engine Selection

Use the `engine` argument to choose the static-site engine. The only supported
engine today is `hugo`.

Unsupported engines fail with a clear error. Adding a future engine such as
Jekyll should route the existing render and verify operations to that engine
without moving provider-specific publication behavior into this scenario.

## Verify Example

```bash
dagger -m ./scenarios/static-site call verify-site \
  --site ./site \
  --site-base-url https://example.com/ \
  --engine hugo
```

## Render Example

```bash
dagger -m ./scenarios/static-site call render-site \
  --site ./site \
  --site-base-url https://example.com/ \
  --engine hugo \
  --output ./public
```

## Main Site Import Layout

The recommended main Hugo site imports component `docs` modules into
component-specific documentation paths and imports `openspec` modules into
shared specs and archived changes paths.

```yaml
module:
  imports:
    - path: github.com/riftonix/daggerverse/docs
      mounts:
        - source: content
          target: content/docs/components/daggerverse

    - path: github.com/riftonix/container-images/docs
      mounts:
        - source: content
          target: content/docs/components/container-images

    - path: github.com/riftonix/daggerverse/openspec
      mounts:
        - source: specs
          target: content/docs/specs
        - source: changes/archive
          target: content/docs/changes/archive

    - path: github.com/riftonix/container-images/openspec
      mounts:
        - source: specs
          target: content/docs/specs
        - source: changes/archive
          target: content/docs/changes/archive
```

Example rendered URL mapping:

```text
daggerverse/docs/content/how-to/foo.md
-> /docs/components/daggerverse/how-to/foo/

container-images/docs/content/how-to/foo.md
-> /docs/components/container-images/how-to/foo/

daggerverse/openspec/specs/git-module/spec.md
-> /docs/specs/git-module/spec/

container-images/openspec/specs/container-images-scenario/spec.md
-> /docs/specs/container-images-scenario/spec/

daggerverse/openspec/changes/archive/add-git-module/proposal.md
-> /docs/changes/archive/add-git-module/proposal/
```

## Mount Collision Validation

Hugo module mounts can overwrite content when multiple imports contribute the
same virtual path. Validate the mount layout before rendering when shared
targets are used.

`validate-hugo-mounts` reads a Hugo YAML config file and receives imported
module directories in the same order as `module.imports`:

```bash
dagger -m ./scenarios/static-site call validate-hugo-mounts \
  --config ./hugo.yml \
  --modules ./daggerverse-docs \
  --modules ./container-images-docs \
  --modules ./daggerverse-openspec \
  --modules ./container-images-openspec
```

The validator walks each configured `mount.source`, maps files to
`mount.target`, and fails when more than one import contributes the same virtual
path. This is generic Hugo mount validation; it is not limited to `docs` or
`openspec` directories.

Use `get-hugo-mount-collisions` when you need a report without failing the
call:

```bash
dagger -m ./scenarios/static-site call get-hugo-mount-collisions \
  --config ./hugo.yml \
  --modules ./daggerverse-docs \
  --modules ./container-images-docs \
  --modules ./daggerverse-openspec \
  --modules ./container-images-openspec
```

Collision messages include the virtual path and the contributing import paths
and mounts.

## CI Provider Boundary

GitHub Actions and GitLab CI workflows remain responsible for:

- event rules and changed-path selection
- preview URL calculation
- GitHub Pages or GitLab Pages publication
- preview cleanup
- pull request or merge request comments
- tokens, permissions, and environments

Workflows should pass already computed values such as `site_base_url` into the
scenario. The scenario does not derive GitHub or GitLab metadata from provider
environment variables and does not publish Pages artifacts itself.
