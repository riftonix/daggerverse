# Hugo Dagger Module

Containerized Hugo build tooling for Dagger pipelines. This module wraps the Hugo CLI in a reproducible container and provides a `build` function that prepares modules, installs required npm dependencies, and renders the `public` directory.

## Features
- Reproducible Hugo environment via container image
- Hugo module download (`hugo mod get -u`)
- Configurable npm registry for assets pipeline
- Static site build with `hugo --minify`

## Defaults
- image_registry: `docker.io`
- image_repository: `hugomods/hugo`
- image_tag: `exts-0.154.2`
- container_user: `65532`
- Working directory in container: `/tmp/hugo/site`
- NPM cache/config paths: `/tmp/npm-cache` and `/tmp/.npmrc`

## API

- create(source, image_registry, image_repository, image_tag, container_user)
  - Returns a configured Hugo module instance. `source` must point to a Hugo site directory.

- container() -> dagger.Container
  - Returns the cached base container with Hugo installed and the site mounted at `/tmp/hugo/site`.

- build(hugo_theme_url: str, site_base_url: str, npm_registry_url: str = 'https://registry.npmjs.org/') -> dagger.Directory
  - Runs:
    - `hugo version`
    - `hugo mod get -u <theme>`
    - `npm config set registry <registry>`
    - `npm install autoprefixer`
    - `hugo --minify --destination public --baseURL <site_base_url> --forceSyncStatic --cleanDestinationDir`
  - Returns the `public` directory as a Dagger `Directory`.

## Usage (CLI)

Build and export to host using `--output`:

```bash
dagger -m ./hugo call --progress=plain \
  --source="./tests/site" \
  --output ./public \
  build --hugo_theme_url="github.com/google/docsy@v0.13.0" \
  --site_base_url="example.com"
```

Start `hugo serve` and expose port 1313:

```bash
dagger -m ./hugo call --progress=plain --source="./tests/site" container \
  with-default-args --args=hugo,serve,--bind,0.0.0.0,--port,1313 \
  with-exposed-port --port=1313 as-service up --ports=1313:1313
```

Open `http://localhost:1313`.

## Usage (Python SDK)

```python
import asyncio
import dagger
from dagger import dag
from hugo import Hugo

async def main():
    async with dagger.Connection(dag) as client:
        site = client.host().directory("./tests/site")
        hugo = await Hugo.create(source=site)
        public_dir = await hugo.build(
            hugo_theme_url="github.com/google/docsy@v0.13.0",
            site_base_url="example.com",
        )
        # Export to host if needed:
        # await public_dir.export("./public")

asyncio.run(main())
```

## License
See the repository root LICENSE file.
