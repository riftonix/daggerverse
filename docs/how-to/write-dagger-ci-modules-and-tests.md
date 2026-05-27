# Write Dagger CI Modules And Tests

Use this guide when adding a reusable Dagger module or when adding Dagger-native tests for an existing module.

The Helm module is the current reference implementation:

- Module: `modules/helm`
- Module source: `modules/helm/src/helm/main.py`
- Test module: `modules/helm/tests`
- Test source: `modules/helm/tests/src/tests/main.py`

## Module Structure

Create each reusable module under `modules/<name>`:

```text
modules/<name>/
|-- dagger.json
|-- pyproject.toml
|-- README.md
`-- src/
    `-- <package>/
        `-- main.py
```

Keep the module focused on one tool or workflow boundary. A module should expose a small public API around that tool instead of becoming a general pipeline script.

For example, the Helm module owns Helm operations such as linting, templating, packaging, pushing, and publication lookup. It does not own repository-wide CI orchestration.

## Public API

Expose module behavior through Dagger functions:

```python
from typing import Annotated, Self

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class Example:
    source: dagger.Directory

    @classmethod
    async def create(
        cls,
        source: Annotated[dagger.Directory, Doc("Input source directory")],
    ):
        return cls(source=source)

    @function
    def container(self) -> dagger.Container:
        return (
            dag.container()
            .from_("example/tool:1.0.0")
            .with_directory("/workspace", self.source)
            .with_workdir("/workspace")
        )

    @function
    async def check(self) -> str:
        return await self.container().with_exec(["tool", "check", "."]).stdout()
```

Prefer typed arguments and `Doc(...)` annotations for public inputs. This keeps CLI help and generated SDKs useful.

Use stable return types:

- `str` for command output that callers need to inspect
- `bool` for existence or status checks
- `dagger.File` or `dagger.Directory` for artifacts
- `Self` for chainable configuration methods
- `dagger.Container` when callers need a configured execution environment

## Container Construction

Build containers through module methods instead of repeating setup in every function.

The usual pattern is:

1. Start from a pinned image.
2. Set deterministic environment variables.
3. Mount the input directory at a stable path.
4. Set a stable workdir.
5. Use `with_exec(...)` in public functions.

Keep image registry, repository, tag, and user configurable when that helps tests or downstream users. Use conservative defaults that work without external credentials.

Avoid relying on host tools. Dagger functions should run inside Dagger containers unless the function is only assembling Dagger objects.

## Secrets

Pass credentials as `dagger.Secret`, not as plain strings.

Use secret variables only at the point where the tool needs them:

```python
container = container.with_secret_variable("REGISTRY_PASSWORD", password)
```

Do not return secret values, print them, or bake them into files that are later returned as artifacts.

## Local Dependencies

When one repository module composes another, use local Dagger dependencies in `dagger.json`:

```json
{
  "dependencies": [
    {
      "name": "helm",
      "source": "../helm"
    }
  ]
}
```

Call the dependency through the generated client, for example `dag.helm(...)`. Do not shell out to `dagger -m ... call ...` from module code.

## Module README

Each module should keep a short README close to the code. The README should cover:

- What the module does
- Main features
- Important defaults
- Public API summary
- Minimal CLI examples
- Link to `../../docs/README.md`

Keep broader conventions, learning paths, and cross-module workflows in `docs/`.

## Test Module Structure

Add Dagger-native tests as a neighboring Dagger module:

```text
modules/<name>/tests/
|-- dagger.json
|-- pyproject.toml
|-- src/
|   `-- tests/
|       `-- main.py
`-- fixtures-or-test-assets/
```

The test module should depend on the parent module with a local dependency:

```json
{
  "name": "tests",
  "dependencies": [
    {
      "name": "<name>",
      "source": ".."
    }
  ]
}
```

Test functions should call the parent module public API:

```python
from dagger import dag, function, object_type


@object_type
class Tests:
    @function
    async def all(self) -> None:
        await self.check()

    @function
    async def check(self) -> None:
        result = await dag.example(source=self._fixture()).check()
        assert result
```

Do not test the parent module by shelling out to the Dagger CLI. Calling the public API through the generated dependency catches the same integration points that downstream Dagger users will use.

## Test Design

Write tests around the module contract, not around implementation details.

Good Dagger module tests usually cover:

- The happy path for each important public function
- Artifact names and non-empty artifact contents
- Rendered or generated structured output
- Optional inputs that change command behavior
- Integration with local services when the module talks to a network service

Use deterministic fixtures under the test module. For Helm, `modules/helm/tests/charts/ns-configurator` provides a real chart fixture and tests assert the rendered Kubernetes manifest structure.

When a workflow needs an external service, prefer an ephemeral Dagger service over a real external dependency. The Helm push test starts a local registry service, pushes a chart to it, and verifies publication lookup without requiring GitHub Container Registry credentials.

## Aggregate Test Function

Every test module used by CI should expose:

```python
@function
async def all(self) -> None:
    ...
```

`all` should run the checks that gate pull requests for that module. Individual test functions can remain callable for debugging.

Keep `all` explicit:

```python
@function
async def all(self) -> None:
    await self.lint()
    await self.template()
    await self.package()
    await self.push()
```

This makes CI behavior clear from the test module source.

## Assertions

Python Dagger module functions are not pytest tests. Use normal Python assertions or `unittest.TestCase` assertions inside callable Dagger functions.

For structured command output, parse the output and assert fields rather than matching long raw strings. The Helm template test parses YAML manifests and checks the Kubernetes resource fields that matter.

## Running Checks

Use the root `Makefile` for supported local checks:

```bash
make tests module <module>
make lint-check module <module>
make format-check module <module>
```

For Helm:

```bash
make tests module helm
make lint-check module helm
make format-check module helm
```

`make tests module <module>` enters `modules/<module>/tests` and calls the test module aggregate function.

Use raw `dagger call` commands only for local debugging:

```bash
cd modules/helm/tests
DAGGER_NO_NAG=1 DO_NOT_TRACK=1 dagger call --progress=plain all
```

## CI Expectations

Pull request CI discovers tested modules and scenarios with:

```text
modules/<module>/tests/dagger.json
scenarios/<scenario>/tests/dagger.json
```

Only those components are included in the test matrix. Components without Dagger test modules are skipped until tests are added.

CI should call the same `Makefile` entrypoints used by local development. Do not duplicate module-specific raw Dagger calls in workflow YAML.

## Review Checklist

Before considering a module ready:

- The module has a focused responsibility.
- Public functions have typed inputs and useful `Doc(...)` annotations.
- Tool execution happens inside Dagger containers.
- Images and tool versions are pinned or intentionally configurable.
- Secrets use `dagger.Secret`.
- Returned artifacts are files or directories, not host paths.
- Tests live in `modules/<name>/tests`.
- The test module depends on the parent module through `source: ".."`.
- Tests call the parent public API through `dag.<module>(...)`.
- The test module exposes `all`.
- `make tests module <module>` passes locally.
- Module README links back to `docs/README.md`.
