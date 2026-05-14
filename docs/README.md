# Daggerverse Documentation

This documentation separates learning material, task-oriented guides, reference material, and design explanations so each page has one clear purpose.

## Recommended Learning Path

1. Start with [Get started with the Helm module](tutorials/get-started-with-helm.md) to run a real module call.
2. Read [Use modules from this repository](how-to/use-modules.md) to understand local module paths and source directories.
3. Read [Run Helm checks through pipelines](how-to/run-helm-checks-through-pipelines.md) if you want CI-oriented orchestration.
4. Use [Module reference](reference/modules.md) when you need available modules, responsibilities, and entry points.
5. Read [Architecture](explanation/architecture.md) when you need the reasoning behind the repository layout and module dependencies.

## Documentation Structure

- [Tutorials](tutorials/README.md) teach by walking through complete examples.
- [How-to guides](how-to/README.md) solve concrete operational tasks.
- [Reference](reference/README.md) lists stable facts, module contracts, paths, and command shapes.
- [Explanation](explanation/README.md) describes design choices and tradeoffs.

## Module Documentation

Each module keeps a short README in `modules/<name>/README.md` for local discovery. This `docs/` directory is the primary documentation source for repository-level guidance and cross-module workflows.
