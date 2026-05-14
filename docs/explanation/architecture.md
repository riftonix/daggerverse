# Architecture

Daggerverse is a collection of small Dagger modules. Each module owns one tool or workflow boundary and can be called independently.

## Module Boundary

Modules live under `modules/<name>`. This keeps repository-level files separate from Dagger module roots and makes it clear which directories are published or called as modules.

Each module contains its own:

- `dagger.json`
- Python project metadata
- source package
- module-local README
- optional test assets

## Local Dependencies

The `pipelines` module composes lower-level modules instead of duplicating their behavior. It uses local dependencies for `helm` and `git`:

```json
{
  "name": "helm",
  "source": "../helm"
}
```

Local dependencies keep development and validation consistent with the repository layout.

## Documentation Boundary

Module READMEs are intentionally short and close to the code. The `docs/` directory is the source for cross-module workflows, learning paths, and architectural explanations.
