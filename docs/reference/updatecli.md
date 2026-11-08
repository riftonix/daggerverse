# Updatecli Module Reference

`modules/updatecli` runs Updatecli manifests in a container. It does not discover
dependencies, generate source-specific pipelines, or schedule runs. Sources,
conditions, targets, and SCM actions are declared by the caller's manifest.

## Constructor and Runtime

| Input | Default | Meaning |
| --- | --- | --- |
| `source` | Empty directory | Local working tree for manifests without an SCM |
| `image_registry` | `ghcr.io` | Runtime image registry |
| `image_repository` | `updatecli/updatecli` | Runtime image repository |
| `image_tag` | `DEFAULT_IMAGE_TAG` in [the module source](../../modules/updatecli/src/updatecli/main.py) | Renovate-managed runtime version |
| `container_user_id` | `65532` | User for Updatecli and shell resources |

The module prepares writable directories as root, then switches to the selected
user. The runtime paths are:

- `/work`: caller-provided `source` or an empty working tree;
- `/updatecli/manifest.yaml`: the supplied manifest;
- `/updatecli/values-<index>.yaml`: supplied values files, indexed in order;
- `/tmp/updatecli-home`: writable `HOME`.

The image must provide `updatecli`, `sh`, `mkdir`, and `chown`. The official
non-slim image satisfies these requirements. The official `-slim` image has no
shell and cannot run this wrapper. Use an image with additional tools when the
manifest calls git, Python, or `npx` from shell resources.

Each execution gets a new `UPDATECLI_RUN_ID` environment value so Dagger does
not reuse a result that depends on old upstream state. Runtime preparation and
input files remain cacheable.

Every Updatecli command runs with `--disable-version-check`: the Updatecli
version is set by the image tag, so the module skips the release lookup.

## Functions

| Function | Result | Behavior |
| --- | --- | --- |
| `container()` | `Container` | Return the configured runtime without running Updatecli |
| `with_secret_variable(name, secret)` | Module instance | Add a secret environment variable |
| `with_env_variable(name, value)` | Module instance | Add a non-secret environment variable |
| `with_directory(path, directory)` | Module instance | Add runtime helper files owned by the configured user |
| `diff(config, values)` | `str` | Run `updatecli pipeline diff` |
| `apply(config, values)` | `str` | Run `updatecli pipeline apply` |
| `applied_source(config, values)` | `Directory` | Apply the manifest and return the resulting `/work` tree |
| `manifest_show(config, values)` | `str` | Run `updatecli manifest show --disable-prepare` without executing pipelines |

`config` is one Updatecli YAML or JSON manifest file, optionally containing Go
templates. `values` is an optional list of YAML or JSON files. Files with equal
basenames are mounted at different paths, and Updatecli merges their values in
the order supplied. JSON values are accepted by the YAML-compatible reader.

The module returns combined Updatecli stdout and stderr. The function result
follows the Updatecli exit status: invalid manifests, failed targets, and failed
SCM actions fail the Dagger function call with command diagnostics.

Updatecli reports a pipeline whose source or condition failed as skipped and
exits with code `0`. The module does not treat a skipped pipeline as an error:
the call succeeds and returns the report, including the source error output. A
manifest that must fail on such an error has to perform the check in a target.

The setup methods affect subsequent calls. Executions do not mutate the input
`Directory` or replace the configured runtime with the command result. Use
`applied_source` to retrieve modified files; `apply` returns only the report.
Independent calls to `apply` and `applied_source` execute independently, so choose
one of them rather than calling both when a manifest has external side effects.

## Paths and Dry Runs

Local resources resolve relative paths from `/work` by default. A manifest that
selects Updatecli's `relativepaths: manifest` mode resolves from `/updatecli`
instead. SCM-backed targets use the repository checkouts managed by Updatecli.
`applied_source` does not return those separate checkouts.

For shell targets, Updatecli executes the shell command even in `diff` mode and
sets `DRY_RUN=true`. The script must honor this variable to avoid writes or
external side effects during a preview. The wrapper does not sandbox or rewrite
caller-supplied scripts.

## Secrets and Helpers

Pass tokens as `dagger.Secret`, never as plain variables or values files:

```bash
dagger -m ./modules/updatecli call \
  with-secret-variable --name=UPDATECLI_GITHUB_TOKEN --secret=env:GITHUB_TOKEN \
  apply --config=./updatecli.yaml
```

Dagger masks secret environment values in command output. The caller is still
responsible for manifest behavior: do not write credentials into target files,
encode them for output, or return them as artifacts.

Updatecli's shell plugin forwards only an allow-list of environment variables.
Adding a variable to the container is not enough to make it available to shell
resources: list it in the shell resource's `spec.environments`:

```yaml
sources:
  helper:
    kind: shell
    spec:
      command: sh /opt/helpers/resolve.sh
      environments:
        - name: HELPER_SETTING
        - name: HELPER_TOKEN
```

The `with_directory` function can mount helper scripts at `/opt/helpers` without
mixing them with the working tree or manifest.

## Examples

Preview a local target:

```bash
dagger -m ./modules/updatecli call \
  --source=./modules/updatecli/tests/fixtures/source \
  diff --config=./modules/updatecli/tests/fixtures/manifests/local.yaml
```

Render a templated manifest with values:

```bash
dagger -m ./modules/updatecli call \
  manifest-show \
  --config=./modules/updatecli/tests/fixtures/manifests/template.yaml \
  --values=./modules/updatecli/tests/fixtures/defaults/values.yaml
```

Override the runtime tag:

```bash
dagger -m ./modules/updatecli call \
  --image-tag=<updatecli-tag> \
  diff --config=./updatecli.yaml
```

Export local changes:

```bash
dagger -m ./modules/updatecli call \
  --source=./modules/updatecli/tests/fixtures/source \
  applied-source --config=./modules/updatecli/tests/fixtures/manifests/local.yaml \
  export --path=./updatecli-output
```

## Tests

```bash
make tests module updatecli
```

The neighboring Dagger test module uses the parent module public API. Its
aggregate `all()` checks runtime setup, preview, apply, returned working trees,
rendering without pipeline execution, ordered YAML/JSON values, failure
propagation, skipped pipelines, helper mounts, plain variables, and secret scrubbing. Fixtures use
local shell and file resources without external services or real credentials;
initial Dagger/SDK provisioning and image pulls still need their normal setup.

For a mirror, the test constructor accepts `image_registry`,
`image_repository`, `image_tag`, and `container_user_id`.
