# Static Site Scenario Reference

`scenarios/static-site` provides provider-neutral verification, rendering, and external content composition. Hugo is currently the only supported engine.

## Hugo Sites

The constructor accepts the site through `source` plus optional Hugo image and npm registry inputs. The site owns its npm theme declaration and lockfile. There is no `hugo_theme_url` input and no Go module resolution.

```bash
dagger -m ./scenarios/static-site call \
  --source=./site \
  --npm-registry=https://npm.example.test/ \
  --hugo-image-tag=0.165.0-10.5.5 \
  verify-site \
  --site-base-url=https://example.com/ \
  --engine=hugo
```

```bash
dagger -m ./scenarios/static-site call \
  --source=./site \
  --hugo-image-tag=0.165.0-10.5.5 \
  render-site \
  --site-base-url=https://example.com/ \
  --engine=hugo \
  --output=./public
```

See [Hugo module reference](hugo.md) for the required `package.json`, `package-lock.json`, and Hugo theme configuration.

## Content Mounts

A content mount uses values at the same index in four constructor arrays:

- `content_sources`: caller-provided Dagger directories
- `content_source_paths`: paths selected inside those directories
- `content_target_paths`: paths inside the final site tree
- `content_contributors`: stable names used in collision diagnostics

All four arrays must have the same length.

The scenario enumerates mapped files before applying overlays. If multiple mounts produce the same target file, verification and rendering fail before Hugo starts.

Recommended mappings for component repositories:

```text
daggerverse docs/content
-> content/docs/components/daggerverse

container-images docs/content
-> content/docs/components/container-images

daggerverse openspec/specs
-> content/docs/specs

daggerverse openspec/changes/archive
-> content/docs/changes/archive
```

Sources remain unchanged and do not need `go.mod`. The caller obtains or checks out repositories and passes their directories explicitly. The scenario does not fetch repositories.

`validate-content-mounts` validates the constructor mounts and returns `validated content mount paths`. `get-content-mount-collisions` returns collision descriptions without failing the call.

## Runtime Inputs

- `hugo_image_registry`: `ghcr.io`
- `hugo_image_repository`: `riftonix/container-images/hugo-autoprefixer`
- `hugo_image_tag`: `0.165.0-10.5.5`
- `hugo_container_user_id`: `65532`
- `npm_registry`: optional npm registry or proxy URL

## Provider Boundary

Provider workflows remain responsible for checkout, event rules, preview URL calculation, publication, cleanup, permissions, and change-request comments. The scenario accepts computed inputs and returns rendered content.
