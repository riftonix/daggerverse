# Docker Dagger Module

Reusable Dagger-native Docker and OCI image helpers for CI workflows. The module builds and publishes OCI images from explicit source directories, context paths, Dockerfiles, build arguments, platforms, smoke commands, and registry credentials without requiring a Docker daemon.

## Quick Example

```bash
dagger -m ./modules/docker call build \
  --source=. \
  --context-path=modules/docker/tests/fixtures/basic-image \
  container
```

## Documentation Path

Use this README only as the local module entry point. The main documentation lives under `docs/`:

1. Start with [Use modules from this repository](../../docs/how-to/use-modules.md) for the common Dagger command shape.
2. Read [Docker module reference](../../docs/reference/docker.md) for the supported API and examples.
3. Read [CI and module test conventions](../../docs/reference/ci.md) for how module tests are discovered and run.
4. Use [Module reference](../../docs/reference/modules.md) when you need repository-level module paths and responsibilities.

## Local Paths

- Module source: `src/docker/`
- Dagger test module: `tests/`
- Public facade: `src/docker/main.py`

## License

See the repository root LICENSE file.
