# Git Dagger Module

Provider-neutral Git helpers for CI workflows. The module works with explicit refs, SHAs, paths, remotes, and credentials instead of reading GitHub, GitLab, or Bitbucket environment variables directly.

## Quick Example

```bash
dagger -m ./modules/git call get-changed-files \
  --source=. \
  --base-ref=origin/main \
  --head-ref=HEAD
```

Ensure a release tag exists on a remote:

```bash
dagger -m ./modules/git call ensure-pushed-tag \
  --source=. \
  --tag=v1.2.3
```

## Documentation Path

Use this README only as the local module entry point. The main documentation lives under `docs/`:

1. Start with [Use modules from this repository](../../docs/how-to/use-modules.md) for the common Dagger command shape.
2. Read [Git module reference](../../docs/reference/git.md) for the supported API and examples.
3. Read [CI and module test conventions](../../docs/reference/ci.md) for how module tests are discovered and run.
4. Use [Module reference](../../docs/reference/modules.md) when you need repository-level module paths and responsibilities.

## Local Paths

- Module source: `src/git/`
- Dagger test module: `tests/`
- Public facade: `src/git/main.py`

## License

See the repository root LICENSE file.
