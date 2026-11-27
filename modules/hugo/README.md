# Hugo Module

Containerized npm-based Hugo build and validation primitives for Dagger pipelines.

The detailed contract, defaults, module layout recommendations, and examples
live in [Hugo module reference](../../docs/reference/hugo.md).

## Runtime Image Inputs

- `image_registry`: `ghcr.io`
- `image_repository`: `riftonix/container-images/hugo-autoprefixer`
- `image_tag`: `0.165.0-10.7.0`
- `container_user_id`: `65532`
- `npm_registry`: unset, uses the npm default or caller configuration

Pin `image_tag` in CI when Hugo rendering must be reproducible or when a site
uses `module.hugoVersion.min` to describe the runtime builder version.

```bash
dagger -m ./modules/hugo call \
  --source=./site \
  --npm-registry=https://npm.example.test/ \
  --image-tag=0.165.0-10.7.0 \
  build \
  --site-base-url=https://example.com/
```

Build and validation require `package.json` and `package-lock.json`, then run
`npm ci --ignore-scripts`. Configure Docsy as `@docsy/theme` from `node_modules`;
the pinned image supplies Sass and other global build tools.

When upgrading from `modules/hugo/v0.4.0`, replace `--user-id` with
`--container-user-id` (`user_id` with `container_user_id` in Python). Static Site
callers keep using its prefixed `--hugo-container-user-id` option.

Run `make tests module hugo` from the repository root. To use a mirror, run
`dagger -m ./modules/hugo/tests call --image-registry=<mirror> all`. The test
module also accepts `--image-repository`, `--image-tag`, `--container-user-id`,
and `--npm-registry`.

## Local Paths

- Module source: `src/hugo/`
- Dagger metadata: `dagger.json`
- Dagger tests: `tests/`

## License

See the repository root LICENSE file.
