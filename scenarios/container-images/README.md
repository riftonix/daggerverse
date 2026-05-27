# Container Images Scenario

Portable container image verification and publication scenario for CI workflows. The scenario composes the reusable Docker module while keeping CI-provider trigger policy, changed path selection, tag parsing, and image reference mapping outside the scenario.

## Documentation Path

Use this README only as the local scenario entry point. Full examples are added with the scenario behavior:

1. Use the root `Makefile` command shape for local checks.
2. Pass explicit source directories, context paths, and image references from CI provider workflows.
3. Keep provider-specific event handling outside this scenario.

## Local Paths

- Scenario source: `src/container_images/`
- Dagger test module: `tests/`
- Public facade: `src/container_images/main.py`

## License

See the repository root LICENSE file.
