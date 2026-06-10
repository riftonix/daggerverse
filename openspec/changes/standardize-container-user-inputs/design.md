## Context

Several modules use `user_id` to configure the Unix UID used inside a container or to set file/secret ownership. The name is generic and collides conceptually with Git users, registry users, SSH users, and CI users. The actual meaning is narrower: container execution user or container-owned file user.

This concern is separate from runtime image identity. `image_registry`, `image_repository`, and `image_tag` answer "which image runs the tool"; `container_user_id` answers "which UID runs or owns files inside that container." Not every image-backed component needs caller control over that UID.

The existing `modules/kind` is minimal and not worth preserving as a public API. Future Kubernetes lifecycle work should be introduced as a Talos-focused module rather than carrying an empty Kind wrapper forward.

## Goals / Non-Goals

**Goals:**

- Rename public `user_id` inputs to `container_user_id` where the value controls `.with_user()`, file ownership, secret ownership, or container home setup.
- Treat `container_user_id` as optional execution-user configuration, not a required part of every runtime image input set.
- Expose prefixed container user inputs in scenarios only when the composed module uses that input.
- Apply the same naming rule to Dagger test modules that expose runtime/helper image overrides for offline or mirrored-registry runs.
- Remove `modules/kind` and related documentation references.
- Document breaking API migrations and release tag requirements.

**Non-Goals:**

- Rename registry usernames, SSH users, Git author names, or other domain users to `container_user_id`.
- Add container user inputs to modules or scenarios that do not actually set container user, file ownership, secret ownership, or home directories.
- Replace `modules/kind` with a Talos module in this change.
- Change runtime image registry/repository/tag behavior; that is handled by `standardize-runtime-image-inputs`.

## Decisions

1. Use `container_user_id` for container execution UID.

   The explicit name avoids ambiguity with registry, SSH, Git, and CI users. It also documents that the input is a UID/string passed into container execution and ownership operations, not a person or account identity.

2. Make container user inputs conditional.

   `container_user_id` should be exposed only when the component uses the value. Git, Helm, Hugo, and SSH need it because they set container users and file/secret ownership. OpenTofu should not gain it unless its implementation starts using it. Kind should not be updated because the module is removed.

3. Prefix scenario container user inputs by tool.

   Multi-tool scenarios should expose names such as `hugo_container_user_id`, `helm_container_user_id`, and `git_container_user_id`. This mirrors prefixed image inputs and prevents a single generic value from ambiguously configuring multiple tools.

4. Keep domain-specific users unchanged.

   Inputs such as registry `username`, SSH `ssh_user`, Git tag `user_name`/`user_email`, and CI actor names are not container execution users. Renaming them would reduce clarity.

5. Remove `modules/kind`.

   The module is a thin wrapper and does not provide enough behavior to justify a breaking cleanup pass. Removing it keeps the module list honest and leaves room for a future Talos module with a concrete contract.

6. Pair code changes with tests and docs.

   Each module/scenario rename should update its tests and README/reference documentation in the same implementation step. Final format, lint, test, and OpenSpec validation commands are user-run handoff tasks for this change.

## Risks / Trade-offs

- Breaking existing `user_id` callers -> Document exact migration to `container_user_id` or prefixed scenario names and require new release tags.
- Removing Kind may surprise consumers -> Mark removal as breaking and document that future Talos work will be a new module.
- Scenario constructor growth -> Add prefixed container user inputs only for composed modules that actually use them.
- Test modules may drift from production signatures -> Update tests with the production change and keep offline override inputs prefixed consistently.

## Migration Plan

1. Rename `user_id` to `container_user_id` in Git, Helm, Hugo, and SSH modules, updating internal field names and ownership calls.
2. Update static-site and Helm CI scenarios to expose and pass through prefixed container user inputs for composed Hugo, Helm, and Git modules.
3. Update affected Dagger test modules alongside each component change, including optional prefixed offline override inputs where relevant.
4. Remove `modules/kind` files and references from docs/lists.
5. Update documentation and examples.
6. Hand off format, lint, test, and OpenSpec validation commands for the user to run.
7. Release changed modules/scenarios under new tags. Consumers migrate by replacing `user_id` with `container_user_id` or prefixed scenario inputs.

Rollback is tag-based: consumers can stay on previous tags until their workflows migrate.

## Open Questions

None.
