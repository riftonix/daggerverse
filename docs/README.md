# Daggerverse Documentation

This documentation separates learning material, task-oriented guides, reference material, and design explanations so each page has one clear purpose.

## Recommended Learning Path

1. Start with [Get started with the Helm module](tutorials/get-started-with-helm.md) to run a real module call.
2. Read [Use modules from this repository](how-to/use-modules.md) to understand local module paths and source directories.
3. Read [Run module and scenario checks](how-to/run-module-checks.md) to run local test, lint, and format commands.
4. Read [Write Dagger CI modules and tests](how-to/write-dagger-ci-modules-and-tests.md) before adding or testing a module.
5. Read [Git module reference](reference/git.md) when building Git-based CI decisions.
6. Read [Helm unittest module reference](reference/helm-unittest.md) when adding chart unit tests.
7. Read [Run Helm checks through Helm CI](how-to/run-helm-checks-through-helm-ci.md) if you want CI-oriented Helm orchestration.
8. Read [Static site scenario reference](reference/static-site.md) when composing provider-neutral Hugo documentation workflows.
9. Read [Runtime image input conventions](reference/runtime-images.md) when pinning or mirroring tool runtime images.
10. Use [Module reference](reference/modules.md) when you need available modules, scenarios, responsibilities, and entry points.
11. Read [Architecture](explanation/architecture.md) when you need the reasoning behind modules, scenarios, composition rules, and dependency boundaries.

## Documentation Structure

- [Tutorials](tutorials/README.md) teach by walking through complete examples.
- [How-to guides](how-to/README.md) solve concrete operational tasks.
- [Reference](reference/README.md) lists stable facts, module contracts, paths, and command shapes.
- [Explanation](explanation/README.md) describes design choices and tradeoffs.

## Module Documentation

Each module keeps a short README in `modules/<name>/README.md` for local discovery. This `docs/` directory is the primary documentation source for repository-level guidance and cross-module workflows.
