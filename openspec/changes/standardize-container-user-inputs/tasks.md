## 1. Container User API Audit

- [ ] 1.1 Audit all public module, scenario, and test module inputs named `user_id` or related to container users.
- [ ] 1.2 Classify each user-like input as container execution user, registry username, SSH login user, Git identity, provider actor, or unrelated domain user.
- [ ] 1.3 Record released modules/scenarios affected by `user_id` to `container_user_id` renames and the tags consumers must upgrade from.
- [ ] 1.4 Confirm which modules/scenarios do not need any container user input.

## 2. Git Module And Tests

- [ ] 2.1 Rename Git module public constructor input `user_id` to `container_user_id`.
- [ ] 2.2 Update Git internal field names, Git CLI helper usage, file ownership, and secret ownership to use `container_user_id`.
- [ ] 2.3 Update Git module tests in the same change for the new public input name and any offline runtime override behavior.
- [ ] 2.4 Keep Git-domain inputs such as `user_name` and `user_email` unchanged.
- [ ] 2.5 Update Git README/reference docs and migration notes.
- [ ] 2.6 Hand off `make tests module git` for the user to run after the Git changes.

## 3. Helm Module And Tests

- [x] 3.1 Rename Helm module public constructor input `user_id` to `container_user_id`.
- [x] 3.2 Update Helm internal field names, container user, chart ownership, and package ownership to use `container_user_id`.
- [x] 3.3 Update Helm module tests in the same change for the new public input name and helper service image inputs.
- [x] 3.4 Keep registry authentication `username` unchanged.
- [x] 3.5 Update Helm README/reference docs and migration notes.
- [x] 3.6 Hand off `make tests module helm` for the user to run after the Helm changes.

## 4. Hugo Module And Tests

- [ ] 4.1 Rename Hugo module public constructor input `user_id` to `container_user_id`.
- [ ] 4.2 Update Hugo internal field names, container user, and site source ownership to use `container_user_id`.
- [ ] 4.3 Update Hugo module tests in the same change for the new public input name and offline runtime overrides.
- [ ] 4.4 Update Hugo README/reference docs and migration notes.
- [ ] 4.5 Hand off `make tests module hugo` for the user to run after the Hugo changes.

## 5. SSH Module

- [ ] 5.1 Rename SSH module public constructor input `user_id` to `container_user_id`.
- [ ] 5.2 Update SSH internal field names, container user/home setup, key ownership, and mounted secret ownership to use `container_user_id`.
- [ ] 5.3 Keep remote login `ssh_user` unchanged.
- [ ] 5.4 Update SSH README/reference docs and migration notes.
- [ ] 5.5 Hand off SSH module tests for the user to run if a test module exists, or document the gap if it does not.

## 6. Scenarios And Scenario Tests

- [ ] 6.1 Add `hugo_container_user_id` to `scenarios/static-site` and pass it to the Hugo module.
- [ ] 6.2 Update static-site scenario tests in the same change for `hugo_container_user_id` pass-through and offline runtime overrides.
- [ ] 6.3 Add `helm_container_user_id` and `git_container_user_id` to `scenarios/helm-ci` and pass them to the Helm and Git modules.
- [ ] 6.4 Update Helm CI scenario tests in the same change for Helm/Git container user pass-through and offline runtime overrides.
- [ ] 6.5 Confirm scenarios do not expose generic `user_id`.
- [ ] 6.6 Hand off `make tests scenario static-site` for the user to run after the static-site changes.
- [ ] 6.7 Hand off `make tests scenario helm-ci` for the user to run after the Helm CI changes.

## 7. Remove Kind Module

- [x] 7.1 Remove `modules/kind` source, metadata, README, and configuration files.
- [x] 7.2 Remove Kind from repository README, module reference docs, and any discovery examples.
- [x] 7.3 Confirm module discovery, lint, format, and publication logic no longer references Kind.
- [x] 7.4 Document that future Talos work should be introduced as a new module.

## 8. Repository Documentation

- [ ] 8.1 Document `container_user_id` as optional container execution user configuration, separate from runtime image identity.
- [ ] 8.2 Document when modules/scenarios should not expose `container_user_id`.
- [ ] 8.3 Document prefixed scenario/test names such as `hugo_container_user_id`, `helm_container_user_id`, and `git_container_user_id`.
- [ ] 8.4 Document breaking release tag requirements for changed modules and scenarios.

## 9. User-Run Final Verification

- [ ] 9.1 Hand off `make format-check` for the user to run.
- [ ] 9.2 Hand off affected `make lint-check module <name>` and `make lint-check scenario <name>` commands for the user to run.
- [ ] 9.3 Hand off `openspec validate standardize-container-user-inputs --strict` for the user to run.

## 10. Archive

- [ ] 10.1 After implementation, archive the change and update baseline specs under `openspec/specs/`.
