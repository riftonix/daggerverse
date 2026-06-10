## Why

Several image-backed modules expose a public `user_id` input, but that name is too generic for a container execution UID and is easy to confuse with Git authors, registry users, SSH users, or CI users. Container execution user configuration should be explicit, optional, and present only where the component actually uses it for `.with_user()`, file ownership, secret ownership, or home directory setup.

## What Changes

- Establish `container_user_id` as the public name for container execution UID inputs.
- Treat container user selection as optional runtime execution configuration, not part of the required image identity contract.
- **BREAKING** Rename `user_id` to `container_user_id` in modules that actually use the value for container user or ownership behavior: Git, Helm, Hugo, and SSH.
- Expose prefixed container user inputs in scenarios that compose modules requiring them, such as `hugo_container_user_id`, `helm_container_user_id`, and `git_container_user_id`.
- Apply the same prefix rule to Dagger test modules when they expose offline or mirrored-registry runtime overrides.
- **BREAKING** Remove `modules/kind` entirely because it is currently empty/minimal and will be replaced by a future Talos-focused module instead of preserving a misleading public API.
- Keep modules and scenarios that do not use container user behavior from exposing a container user input.
- Update docs, README examples, tests, and release guidance for changed modules and scenarios.

## Capabilities

### New Capabilities

- `helm-module`: Define the Helm module public contract for chart operations and container execution user configuration.
- `ssh-module`: Define the SSH module public contract for SSH client execution and container execution user configuration.

### Modified Capabilities

- `daggerverse`: Add the repository-wide container execution user naming convention and remove the Kind module from the repository module set.
- `git-module`: Rename the Git module execution user input from `user_id` to `container_user_id`.
- `hugo-module`: Rename the Hugo module execution user input from `user_id` to `container_user_id`.
- `helm-ci-scenario`: Expose prefixed Helm and Git container user inputs and pass them through to composed modules.
- `static-site-scenario`: Expose prefixed Hugo container user input and pass it through to the Hugo module.

## Impact

- Affected code: `modules/git`, `modules/helm`, `modules/hugo`, `modules/ssh`, `modules/kind`, `scenarios/static-site`, `scenarios/helm-ci`, Dagger test modules, docs, and examples.
- API impact: released modules/scenarios with `user_id` inputs need new tags; callers must migrate to `container_user_id` or the relevant prefixed scenario input.
- Removal impact: `modules/kind` callers must stop using that module; future Kubernetes/Talos work should start as a new module instead of extending Kind.
- Documentation impact: repository reference docs and component READMEs must distinguish runtime image identity from optional container execution user configuration.
