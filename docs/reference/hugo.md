# Hugo Module Reference

`modules/hugo` wraps Hugo in a pinned container image and exposes reusable
engine-level operations for static-site pipelines.

## Defaults

- Image registry: `ghcr.io`
- Image repository: `riftonix/container-images/hugo-autoprefixer`
- Image tag: `0.154.5-10.5.0`
- Container user: `65532`
- Workdir: `/tmp/hugo/site`

The default image is `ghcr.io/riftonix/container-images/hugo-autoprefixer:0.154.5-10.5.0`.
The normal build and validation paths rely on tools already present in that
image. They do not install npm packages at runtime.

## Functions

`build(source, hugo_theme_url, site_base_url)` renders a Hugo site and returns
the generated `public` directory as a Dagger `Directory`.

`validate(source, hugo_theme_url, site_base_url)` runs Hugo configuration and
strict render checks. The validation path uses Hugo build/config behavior with
strict flags such as warning and path checks; markdown, link, HTML,
accessibility, and policy linting remain separate concerns.

`init_module(source, module_path)` initializes Hugo module metadata without
rendering a static site.

`prepare_module(source, hugo_module_url)` resolves Hugo module dependencies
without producing a `public` directory.

## Site Build Example

```bash
dagger -m ./modules/hugo call \
  --source ./site \
  build \
  --hugo-theme-url github.com/google/docsy@v0.13.0 \
  --site-base-url https://example.com/
```

## Strict Validation Example

```bash
dagger -m ./modules/hugo call \
  --source ./site \
  validate \
  --hugo-theme-url github.com/google/docsy@v0.13.0 \
  --site-base-url https://example.com/
```

## Hugo Module Preparation

Use Hugo module preparation when a repository is a reusable Hugo module rather
than the final rendered site:

```bash
dagger -m ./modules/hugo call \
  --source ./docs \
  prepare-module
```

Preparation is intentionally an engine-specific Hugo operation. The
`scenarios/static-site` API only exposes common static-site render and verify
operations.

Scenario-level Hugo verification passes the site as constructor `source` and
the Hugo theme as constructor `hugo_theme_url`:

```bash
dagger -m ./scenarios/static-site call \
  --source=./site \
  --hugo-theme-url=github.com/google/docsy@v0.13.0 \
  verify-site \
  --site-base-url=https://example.com/ \
  --engine=hugo
```

## Recommended `docs` Module Layout

A component documentation module should stay path-neutral. It should expose
normal Hugo component directories and let the importing site choose the final
URL path with mounts.

```text
docs/
├── README.md
├── go.mod
└── content/
    └── how-to/
        └── example.md
```

Example `go.mod`:

```go
module github.com/riftonix/example/docs
```

Content under `docs/content` should not encode a final site path such as
`docs/components/example`. The main site owns that placement.

## Recommended `openspec` Module Layout

An OpenSpec module should keep OpenSpec-owned files unchanged. Hugo can mount
the existing trees directly:

```text
openspec/
├── go.mod
├── specs/
│   └── capability-name/
│       └── spec.md
└── changes/
    └── archive/
        └── completed-change/
            ├── proposal.md
            ├── design.md
            └── tasks.md
```

Example `go.mod`:

```go
module github.com/riftonix/example/openspec
```

Optional Hugo sidecar `_index.md` files may be added next to OpenSpec
directories when Docsy navigation needs section pages. Do not rewrite
OpenSpec-owned `spec.md`, `proposal.md`, `design.md`, or `tasks.md` solely for
Hugo.

## Provider-Neutral Usage

Provider workflows should compute values such as preview URLs and then pass the
explicit `site_base_url` to Hugo or to the static-site scenario. The Hugo module
does not publish Pages artifacts, manage deployment environments, delete
previews, comment on pull requests, or derive provider metadata from CI
environment variables.
