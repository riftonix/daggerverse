## 1. Container User API Audit

- [x] 1.1 Audit all public module, scenario, and test module inputs named `user_id` or related to container users.
- [x] 1.2 Classify each user-like input as container execution user, registry username, SSH login user, Git identity, provider actor, or unrelated domain user.
- [x] 1.3 Record released modules/scenarios affected by `user_id` to `container_user_id` renames and the tags consumers must upgrade from.
- [x] 1.4 Confirm which modules/scenarios do not need any container user input.

The audit found that `user_id` controlled container execution in Git, Hugo, SSH,
and OpenTofu. OpenTofu is included because it passes the value to `.with_user()`.
Docker and Container Images do not need a container user input. Registry and Git
HTTPS usernames, SSH login (`ssh_user`), and Git tagger identity (`user_name`,
`user_email`) are separate from container execution.

### Release migration inventory

These are the latest component tags on `origin` and the API at each tag. Keep
existing pins until replacement tags are published; do not move existing tags.

| Component | Upgrade from | Migration |
| --- | --- | --- |
| Git | `modules/git/v1.0.4` | Publish a new module tag after the rename. Direct callers replace `user_id` (`--user-id`) with `container_user_id` (`--container-user-id`). |
| Helm | `modules/helm/v1.3.1` | The tag still exposes `user_id`. Publish a new module tag for the already-renamed API. Direct callers replace `user_id` (`--user-id`) with `container_user_id` (`--container-user-id`). |
| Hugo | `modules/hugo/v0.4.0` | Publish a new module tag after the rename. Direct callers replace `user_id` (`--user-id`) with `container_user_id` (`--container-user-id`). |
| SSH | `ssh/v0.1.0` | The legacy release uses the `ssh/` module path and `container_user` (`--container-user`). Publish the first `modules/ssh/*` tag after the rename. Legacy callers switch to `modules/ssh` and `container_user_id` (`--container-user-id`); consumers pinned to a newer commit may currently use `user_id`. |
| OpenTofu | No dedicated release tag | Callers pinned to a commit that accepts `user_id` switch to `container_user_id` (`--container-user-id`) when upgrading. Publish the first `modules/opentofu/*` tag for tagged consumers. |
| Helm CI | `scenarios/helm-ci/v1.4.0` | Publish a new scenario tag after updating its local Git constructor call. Callers keep `helm_container_user_id` and `git_container_user_id`. |
| Static Site | `scenarios/static-site/v0.4.0` | Publish a new scenario tag after updating its local Hugo constructor call. Callers keep `hugo_container_user_id`. |

The removed Kind wrapper has no dedicated release tag on `origin` and has no
replacement in this change.

## 2. Git Module And Tests

- [x] 2.1 Rename Git module public constructor input `user_id` to `container_user_id`.
- [x] 2.2 Update Git internal field names, Git CLI helper usage, file ownership, and secret ownership to use `container_user_id`.
- [x] 2.3 Update Git module tests in the same change for the new public input name and any offline runtime override behavior.
- [x] 2.4 Keep Git-domain inputs such as `user_name` and `user_email` unchanged.
- [x] 2.5 Update Git README/reference docs and migration notes.
- [x] 2.6 Hand off `make tests module git` for the user to run after the Git changes.

## 3. Helm Module And Tests

- [x] 3.1 Rename Helm module public constructor input `user_id` to `container_user_id`.
- [x] 3.2 Update Helm internal field names, container user, chart ownership, and package ownership to use `container_user_id`.
- [x] 3.3 Update Helm module tests in the same change for the new public input name and helper service image inputs.
- [x] 3.4 Keep registry authentication `username` unchanged.
- [x] 3.5 Update Helm README/reference docs and migration notes.
- [x] 3.6 Hand off `make tests module helm` for the user to run after the Helm changes.

## 4. Hugo Module And Tests

- [x] 4.1 Rename Hugo module public constructor input `user_id` to `container_user_id`.
- [x] 4.2 Update Hugo internal field names, container user, and site source ownership to use `container_user_id`.
- [x] 4.3 Update Hugo module tests in the same change for the new public input name and offline runtime overrides.
- [x] 4.4 Update Hugo README/reference docs and migration notes.
- [x] 4.5 Hand off `make tests module hugo` for the user to run after the Hugo changes.

## 5. SSH Module

- [x] 5.1 Rename SSH module public constructor input `user_id` to `container_user_id`.
- [x] 5.2 Update SSH internal field names, container user/home setup, key ownership, and mounted secret ownership to use `container_user_id`.
- [x] 5.3 Keep remote login `ssh_user` unchanged.
- [x] 5.4 Update SSH README/reference docs and migration notes.
- [x] 5.5 Hand off SSH module tests for the user to run if a test module exists, or document the gap if it does not.

## 6. Scenarios And Scenario Tests

- [x] 6.1 Add `hugo_container_user_id` to `scenarios/static-site` and pass it to the Hugo module.
- [x] 6.2 Update static-site scenario tests in the same change for `hugo_container_user_id` pass-through and offline runtime overrides.
- [x] 6.3 Add `helm_container_user_id` and `git_container_user_id` to `scenarios/helm-ci` and pass them to the Helm and Git modules.
- [x] 6.4 Update Helm CI scenario tests in the same change for Helm/Git container user pass-through and offline runtime overrides.
- [x] 6.5 Confirm scenarios do not expose generic `user_id`.
- [x] 6.6 Hand off `make tests scenario static-site` for the user to run after the static-site changes.
- [x] 6.7 Hand off `make tests scenario helm-ci` for the user to run after the Helm CI changes.

Static Site and Helm CI pass their existing prefixed public inputs to Hugo, Helm,
and Git as `container_user_id`. Helm CI uses Git for release tagging in
`publish-chart`.

## 7. Remove Kind Module

- [x] 7.1 Remove `modules/kind` source, metadata, README, and configuration files.
- [x] 7.2 Remove Kind from repository README, module reference docs, and any discovery examples.
- [x] 7.3 Confirm module discovery, lint, format, and publication logic no longer references Kind.
- [x] 7.4 Document that future Talos work should be introduced as a new module.

## 8. Repository Documentation

- [x] 8.1 Document `container_user_id` as optional container execution user configuration, separate from runtime image identity.
- [x] 8.2 Document when modules/scenarios should not expose `container_user_id`.
- [x] 8.3 Document prefixed scenario/test names such as `hugo_container_user_id`, `helm_container_user_id`, and `git_container_user_id`.
- [x] 8.4 Document breaking release tag requirements for changed modules and scenarios.

## 9. Final Verification

- [x] 9.1 Leave `make format-check` to CI.
- [x] 9.2 Leave lint checks for the affected modules and scenarios to CI.
- [x] 9.3 Run `openspec validate standardize-container-user-inputs --strict`.

## 10. Archive

- [x] 10.1 After implementation, archive the change and update baseline specs under `openspec/specs/`.

## 11. OpenTofu Module And Tests

- [x] 11.1 Rename the OpenTofu constructor input and execution user to `container_user_id`, preserving the default UID and independent `executor` input.
- [x] 11.2 Update the OpenTofu module test to cover the renamed input.
- [x] 11.3 Update the OpenTofu README and migration notes.
- [x] 11.4 Hand off `make tests module opentofu` for the user to run.
