# Project Context

Daggerverse is a collection of reusable Dagger CI modules. Each module lives under `modules/<name>` and can be used independently through the Dagger CLI or composed by another module.

## Structure

- Repository documentation lives in `docs/`.
- Dagger modules live in `modules/`.
- OpenSpec baseline specifications live in `openspec/specs/`.
- OpenSpec change proposals live in `openspec/changes/` when future behavior is planned.

## Documentation Language

OpenSpec content and repository documentation are written in English.

## Development Guidelines

- Keep modules small and focused on one tool or workflow boundary.
- Prefer local module dependencies for composition inside this repository.
- Use change proposals only for planned changes. Document already implemented behavior in baseline specs.
