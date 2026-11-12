# Updatecli

Reusable Dagger runtime for Updatecli manifests. It previews and applies changes,
renders Go templates with values files, and returns the updated working tree for
local targets. Source selection, commits, and pull request behavior belong to the
caller-provided manifest, not this module.

## Runtime

The default image is `ghcr.io/updatecli/updatecli`, using the Renovate-managed
`DEFAULT_IMAGE_TAG` in [main.py](src/updatecli/main.py), with container user
`65532`. Override it through `image_registry`, `image_repository`, `image_tag`,
and `container_user_id`.

The working tree is mounted at `/work`; `source` is optional and defaults to an
empty directory. A writable home is configured at `/tmp/updatecli-home`.
The official non-slim image includes a shell but no git binary, Python, or
Node.js. Use a custom runtime image when shell resources need those tools.

## Functions

- `container()` returns the configured runtime container.
- `with_secret_variable(name, secret)`, `with_env_variable(name, value)`, and
  `with_directory(path, directory)` configure the runtime and return the module
  for chaining.
- `diff(config, values)` previews changes.
- `apply(config, values)` applies changes and any manifest-defined SCM actions.
- `applied_source(config, values)` applies changes and returns `/work` as a
  `Directory`. It does not return separate SCM checkouts.
- `manifest_show(config, values)` renders manifests without executing pipelines.

`config` is a YAML or JSON `File`, optionally using Go templates. `values` is an
optional list of YAML or JSON files, merged in the order supplied. Commands
return combined stdout and stderr and fail the Dagger call when Updatecli exits
with an error. A pipeline that Updatecli skips, for example after a source
failure, is not an error. Dagger masks secret environment values in command
output.

## Examples

Preview the local fixture:

```bash
dagger -m ./modules/updatecli call \
  --source=./modules/updatecli/tests/fixtures/source \
  diff --config=./modules/updatecli/tests/fixtures/manifests/local.yaml
```

Export updated files without modifying the input directory:

```bash
dagger -m ./modules/updatecli call \
  --source=./modules/updatecli/tests/fixtures/source \
  applied-source --config=./modules/updatecli/tests/fixtures/manifests/local.yaml \
  export --path=./updatecli-output
```

Pass a GitHub token to a manifest that declares a GitHub SCM and pull request
action:

```bash
dagger -m ./modules/updatecli call \
  with-secret-variable --name=UPDATECLI_GITHUB_TOKEN --secret=env:GITHUB_TOKEN \
  apply --config=./updatecli.yaml
```

## Tests

```bash
make tests module updatecli
```

Tests use local manifests and fixtures, without upstream services or real
credentials. The Dagger engine, SDK provisioning, and runtime image must be
available. Tests also accept the runtime image inputs for registry mirrors.

## Documentation

- [Repository documentation](../../docs/README.md)
- [Updatecli reference](../../docs/reference/updatecli.md)
