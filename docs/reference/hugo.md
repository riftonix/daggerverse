# Hugo Module Reference

`modules/hugo` builds and validates npm-based Hugo sites in a pinned container. It does not use Go or Hugo Modules.

## Defaults

- Image: `ghcr.io/riftonix/container-images/hugo-autoprefixer:0.165.0-10.5.5`
- Container user: `65532`
- Workdir: `/tmp/hugo/site`
- npm registry: npm default

The image supplies Hugo, Autoprefixer, Sass, and the other global build tools. A site does not need to declare `sass-embedded` when it intentionally relies on this pinned image.

The site must contain `package.json` and `package-lock.json`. Build and validation run `npm ci --ignore-scripts` before Hugo. Downloads use the shared `hugo-npm-cache` Dagger cache. Set `npm_registry` to an npm-compatible proxy when required.

## Site Configuration

Declare Docsy in `package.json`:

```json
{
  "private": true,
  "devDependencies": {
    "@docsy/theme": "0.17.0"
  }
}
```

Commit the generated `package-lock.json` and configure Hugo to load the package from `node_modules`:

```yaml
theme: "@docsy/theme"
themesDir: node_modules
```

Do not add `go.mod`, `go.sum`, or `module.imports` for the theme.

## Functions

`build(source, site_base_url)` installs npm dependencies, renders the site, and returns `public` as a Dagger `Directory`.

`validate(source, site_base_url)` installs npm dependencies and runs Hugo configuration and rendering checks with strict warning, path, and localization flags.

`with_npm_dependencies(source)` returns the prepared runtime for inspection or extension.

## Examples

```bash
dagger -m ./modules/hugo call \
  --source=./site \
  --image-tag=0.165.0-10.5.5 \
  build \
  --site-base-url=https://example.com/ \
  --output=./public
```

```bash
dagger -m ./modules/hugo call \
  --source=./site \
  --image-tag=0.165.0-10.5.5 \
  validate \
  --site-base-url=https://example.com/
```

## External Content

The Hugo module receives one complete site tree. Use `scenarios/static-site` when documentation from several repositories must be mounted into that tree. External content directories remain path-neutral and require no Go metadata.

## Provider Boundary

The module does not publish Pages artifacts, manage environments, calculate preview URLs, or inspect provider event metadata. Workflows pass the final `site_base_url` and publish the returned directory.
