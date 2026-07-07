# Hugo Module

Containerized Hugo build, validation, and Hugo module preparation primitives for
Dagger pipelines.

The detailed contract, defaults, module layout recommendations, and examples
live in [Hugo module reference](../../docs/reference/hugo.md).

## Runtime Image Inputs

- `image_registry`: `ghcr.io`
- `image_repository`: `riftonix/container-images/hugo-autoprefixer`
- `image_tag`: `0.154.5-10.5.0`
- `user_id`: `65532`

Pin `image_tag` in CI when Hugo rendering must be reproducible or when a site
uses `module.hugoVersion.min` to describe the runtime builder version.

```bash
dagger -m ./modules/hugo call \
  --source=./site \
  --image-tag=0.154.5-10.5.0 \
  build \
  --hugo-theme-url=github.com/google/docsy@v0.13.0 \
  --site-base-url=https://example.com/
```

## Local Paths

- Module source: `src/hugo/`
- Dagger metadata: `dagger.json`
- Dagger tests: `tests/`

## License

See the repository root LICENSE file.
