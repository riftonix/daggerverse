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

## Container User Migration

Set `--container-user-id` (Python: `container_user_id`) to override the default
UID `65532`. When upgrading from `modules/git/v1.0.4`, replace `--user-id` or
`user_id` in direct module calls.

Run `make tests module git` from the repository root. For mirrored images, run
`dagger -m ./modules/git/tests call --image-registry=<mirror> all`. The test
module also accepts `--image-repository`, `--image-tag`, and `--container-user-id`.

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
