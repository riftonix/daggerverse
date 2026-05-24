# Architecture

Daggerverse is a collection of small reusable Dagger modules plus ready-to-run scenarios. Modules own reusable tool boundaries and can be called independently. Scenarios compose modules into concrete CI jobs.

## Module Boundary

Modules live under `modules/<name>`. This keeps repository-level files separate from Dagger module roots and makes it clear which directories are published or called as modules.

Each module contains its own:

- `dagger.json`
- Python project metadata
- source package
- module-local README
- optional test assets

Ready-to-run CI jobs should not live under `modules/`. They belong under `scenarios/<name>` so reusable primitives and concrete CI workflows do not share the same namespace.

## Scenario Boundary

Scenarios compose lower-level modules instead of duplicating their behavior. For example, a Helm CI scenario can depend on local `helm` and `git` modules:

```json
{
  "name": "helm",
  "source": "../helm"
}
```

Local dependencies keep development and validation consistent with the repository layout.

The current `modules/pipelines` directory is transitional. Treat it as a temporary Helm CI wrapper; the final `scenarios/` layout, naming, and provider-specific job shape should be defined in a separate proposal.

## Documentation Boundary

Module READMEs are intentionally short and close to the code. The `docs/` directory is the source for cross-module workflows, learning paths, and architectural explanations.
