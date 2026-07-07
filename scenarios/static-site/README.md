# Static Site Scenario

Provider-neutral static-site verification and rendering scenario.

Detailed engine selection, Hugo usage, mount collision validation, and CI
provider boundaries live in
[Static site scenario reference](../../docs/reference/static-site.md).

## CLI Shape

Pass the primary site tree through the scenario constructor as `--source`.
Hugo-backed operations also require an explicit Hugo theme module URL:

```bash
dagger -m ./scenarios/static-site call \
  --source=./site \
  --hugo-theme-url=github.com/google/docsy@v0.13.0 \
  --hugo-image-tag=0.154.5-10.5.0 \
  verify-site \
  --site-base-url=https://example.com/ \
  --engine=hugo
```

Render uses the same constructor inputs:

```bash
dagger -m ./scenarios/static-site call \
  --source=./site \
  --hugo-theme-url=github.com/google/docsy@v0.13.0 \
  --hugo-image-tag=0.154.5-10.5.0 \
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
- `hugo_image_tag`: `0.154.5-10.5.0`
- `hugo_container_user_id`: `65532`

Pin `hugo_image_tag` in workflows where reproducibility matters or where
`module.hugoVersion.min` must track the same Hugo version as the builder image.

Migration from older static-site scenario calls:

- Replace function-level `--site=<dir>` with constructor `--source=<dir>`.
- Add constructor `--hugo-theme-url=<module-ref>` when `--engine=hugo`.
- Treat this as a breaking CLI change. The updated scenario requires a new
  release tag; workflows pinned to `scenarios/static-site/v0.1.0` can stay on
  that tag until they migrate.
- Adding Hugo runtime image inputs changes the public scenario API and should be
  released under a new scenario tag.

## Local Paths

- Scenario source: `src/static_site/`
- Dagger metadata: `dagger.json`
- Dagger tests: `tests/`

## License

See the repository root LICENSE file.
