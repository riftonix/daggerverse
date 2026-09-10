# Static Site Scenario

Provider-neutral static-site verification and rendering scenario.

Detailed engine selection, Hugo usage, mount collision validation, and CI
provider boundaries live in
[Static site scenario reference](../../docs/reference/static-site.md).

## CLI Shape

Pass the npm-based site tree through the scenario constructor as `--source`:

```bash
dagger -m ./scenarios/static-site call \
  --source=./site \
  --npm-registry=https://npm.example.test/ \
  --hugo-image-tag=0.165.0-10.5.5 \
  verify-site \
  --site-base-url=https://example.com/ \
  --engine=hugo
```

Render uses the same constructor inputs:

```bash
dagger -m ./scenarios/static-site call \
  --source=./site \
  --hugo-image-tag=0.165.0-10.5.5 \
  render-site \
  --site-base-url=https://example.com/ \
  --engine=hugo \
  --output=./public
```

## Hugo Runtime Image Inputs

Hugo-backed operations accept constructor-level runtime image inputs and pass
them to the Hugo module:

- `hugo_image_registry`: `ghcr.io`
- `hugo_image_repository`: `riftonix/container-images/hugo-autoprefixer`
- `hugo_image_tag`: `0.165.0-10.5.5`
- `hugo_container_user_id`: `65532`
- `npm_registry`: optional npm registry or caching proxy URL

Hugo-backed operations require `package.json` and `package-lock.json` and run
`npm ci --ignore-scripts` before Hugo. External content is supplied through
aligned source, source path, target path, and contributor arrays and composed by
Dagger, not through Hugo Modules.

Pin `hugo_image_tag` in workflows where reproducibility matters or where
`module.hugoVersion.min` must track the same Hugo version as the builder image.

The site declares `@docsy/theme` and configures `themesDir: node_modules`. The
runtime image supplies Sass, so site manifests do not need `sass-embedded` when
they use the pinned image.

## Local Paths

- Scenario source: `src/static_site/`
- Dagger metadata: `dagger.json`
- Dagger tests: `tests/`

## License

See the repository root LICENSE file.
