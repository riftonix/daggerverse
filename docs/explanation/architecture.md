# Architecture

Daggerverse is a collection of small reusable Dagger modules plus ready-to-run scenarios. Modules own reusable tool boundaries and can be called independently. Scenarios compose modules and other scenarios into concrete CI jobs.

## Module Boundary

Modules live under `modules/<name>`. This keeps repository-level files separate from Dagger module roots and makes it clear which directories are published or called as modules.

Each module contains its own:

- `dagger.json`
- Python project metadata
- source package
- module-local README
- optional test assets

Ready-to-run CI jobs should not live under `modules/`. They belong under `scenarios/<name>` so reusable primitives and concrete CI workflows do not share the same namespace.

Modules are leaf building blocks. A module must be self-contained and must not import repository scenarios or other repository modules. This keeps modules independently reusable and lets DevOps teams choose module versions explicitly when they build their own scenarios.

## Scenario Boundary

Scenarios are compositions. A scenario may depend on modules, other scenarios, or both:

```text
scenario = module + module
scenario = scenario + scenario + module
```

For example, a Helm CI scenario can depend on local `helm` and `git` modules:

```json
{
  "name": "helm",
  "source": "../helm"
}
```

Local dependencies keep development and validation consistent with the repository layout.

A released scenario should be self-consistent: it pins the module or scenario versions it composes and is tested against those versions. A scenario may use implementation modules internally, but its public API should expose only stable, scenario-level inputs and outputs such as `Directory`, `Secret`, `str`, `list[str]`, `Platform`, or scenario-owned spec/result objects. It should not expose implementation-module object types such as another module's build or image result objects.

This prevents version collisions when a user composes their own scenario from multiple released building blocks. For example, a user may depend on `container-images@v1` and also use `docker@v2` directly. That is safe when `container-images@v1` hides its internal `docker` dependency behind primitive or scenario-owned return types. If a scenario exposed `DockerBuild` or `DockerImage` from its internal dependency, the user's direct `docker@v2` objects could become incompatible with the scenario's internal `docker@v1` objects.

If users need a newer module behavior than a released scenario provides, they should either use the module directly in their own scenario, upgrade to a newer scenario release, or fork/recompose the scenario with their chosen module version.

The current `modules/pipelines` directory is transitional. Treat it as a temporary Helm CI wrapper; the final `scenarios/` layout, naming, and provider-specific job shape should be defined in a separate proposal.

## Documentation Boundary

Module READMEs are intentionally short and close to the code. The `docs/` directory is the source for cross-module workflows, learning paths, and architectural explanations.
