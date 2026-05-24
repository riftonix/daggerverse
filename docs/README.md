# Daggerverse Documentation

This documentation separates learning material, task-oriented guides, reference material, and design explanations so each page has one clear purpose.

## Recommended Learning Path

1. Start with [Get started with the Helm module](tutorials/get-started-with-helm.md) to run a real module call.
2. Read [Use modules from this repository](how-to/use-modules.md) to understand local module paths and source directories.
3. Read [Run module checks](how-to/run-module-checks.md) to run local test, lint, and format commands.
4. Read [Write Dagger CI modules and tests](how-to/write-dagger-ci-modules-and-tests.md) before adding or testing a module.
5. Read [Run Helm checks through the transitional pipeline](how-to/run-helm-checks-through-pipelines.md) if you want the current CI-oriented Helm orchestration.
6. Use [Module reference](reference/modules.md) when you need available modules, responsibilities, and entry points.
7. Read [Architecture](explanation/architecture.md) when you need the reasoning behind the repository layout and module dependencies.

## Documentation Structure

- [Tutorials](tutorials/README.md) teach by walking through complete examples.
- [How-to guides](how-to/README.md) solve concrete operational tasks.
- [Reference](reference/README.md) lists stable facts, module contracts, paths, and command shapes.
- [Explanation](explanation/README.md) describes design choices and tradeoffs.

## Module Documentation

Each module keeps a short README in `modules/<name>/README.md` for local discovery. This `docs/` directory is the primary documentation source for repository-level guidance and cross-module workflows.
