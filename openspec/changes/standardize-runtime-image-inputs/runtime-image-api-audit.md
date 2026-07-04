## Runtime Image API Audit

Scope: public Dagger module and scenario constructors/functions under `modules/` and `scenarios/`, plus Dagger test module entrypoints and helper service image inputs.

### 1.1 Public Runtime Image Inputs

| Component | Public image-related inputs | Audit result |
| --- | --- | --- |
| `modules/git` | `source`, `image_registry`, `image_repository`, `image_tag`, `user_id` on constructor | Runtime image selection. Already follows the standard names. |
| `modules/helm` | `source`, `image_registry`, `image_repository`, `image_tag`, `user_id` on constructor | Runtime image selection. Already follows the standard names. |
| `modules/hugo` | `source`, `image_registry`, `image_repository`, `image_tag`, `user_id` on constructor | Runtime image selection. Already follows the standard names. |
| `modules/kind` | `image_registry`, `image_repository`, `image_tag`, `user_id` on constructor | Runtime image selection. Already follows the standard names. Doc strings still say Helm, but names match the convention. |
| `modules/ssh` | `image_registry`, `image_repository`, `image_tag`, `user_id` on constructor | Runtime image selection. Already follows the standard names. Doc strings still say Helm, but names match the convention. |
| `modules/opentofu` | `container_image`, `executor` on constructor | Runtime image selection uses combined `container_image`, which violates the target convention. `executor` is unrelated command selection and must remain separate. |
| `modules/docker` | `image_ref`, `image_refs`, `tags`, `context_path`, `dockerfile_path`, `bake_path`, `variable_overrides`, registry auth fields | Build/publish image metadata and registry authentication. These are not runtime tool image selectors and should keep their current names. |
| `scenarios/static-site` | `source`, `hugo_theme_url`; calls `dag.hugo(source=...)` with hidden Hugo defaults | Scenario composes Hugo but does not expose Hugo runtime image selection. Needs prefixed `hugo_image_registry`, `hugo_image_repository`, `hugo_image_tag`, `hugo_user_id`. |
| `scenarios/helm-ci` | `source`; private `_helm()` accepts unprefixed Helm runtime image defaults; changed-chart detection calls `dag.git(source=...)` with hidden Git defaults | Scenario composes Helm and Git. Public API needs prefixed Helm and Git runtime image inputs; current public functions do not expose them. |
| `scenarios/container-images` | `image_ref`, `publish_specs`, `context_path`, `dockerfile_path`, `bake_path`, `variable_overrides`, registry auth fields | Build/publish metadata and registry authentication. These are explicit exceptions, not runtime tool image selectors. |

### 1.2 Classification

Runtime image selection:

- `image_registry`, `image_repository`, `image_tag`, `user_id` in `modules/git`, `modules/helm`, `modules/hugo`, `modules/kind`, and `modules/ssh`.
- `container_image` in `modules/opentofu`, to be migrated to split standard inputs.
- Hidden Hugo runtime image defaults currently used by `scenarios/static-site`.
- Hidden Git runtime image defaults and private unprefixed Helm runtime image defaults currently used by `scenarios/helm-ci`.

Build/publish image metadata:

- `image_ref`, `image_refs`, `tags`, `publish_specs`, `context_path`, `dockerfile_path`, `bake_path`, `bake_target`, `variable_overrides`, `platforms`, `target`, `build_args`, `labels`, and smoke command fields in `modules/docker` and `scenarios/container-images`.

Registry authentication:

- `with_registry_auth(address, username, password)` in `modules/docker` and `scenarios/container-images`.
- Helm chart registry login inputs `username`, `password`, `address`, `oci_url`, and `insecure` in `modules/helm` and `scenarios/helm-ci`.

Unrelated version or command inputs:

- Helm chart `version` and `app_version` inputs are chart package metadata, not runtime image tags.
- `modules/opentofu` `executor` chooses the IaC command inside the runtime image and is not image identity.
- `scenarios/static-site` `hugo_theme_url` is Hugo theme/module configuration, not runtime image identity.
- Git refs, branch names, diff paths, release tags, and component path inputs are repository/version-control inputs, not runtime image selectors.

### 1.3 Test Module Audit

| Test module | Public aggregate | Helper/runtime image inputs | Audit result |
| --- | --- | --- | --- |
| `modules/docker/tests` | `all()` without inputs | `image_ref`, `image_refs`, `tags`, registry auth examples | OK. These validate build/publish metadata, not runtime image selection. |
| `modules/git/tests` | `all(source)` | None | Drift from no-argument aggregate convention. The only caller-provided source usage is metadata SHA shape checks, so task `6.1` should normalize this to `all()` by using an existing synthetic Git repository fixture instead of documenting an exception. |
| `modules/helm/tests` | `all()` without inputs | `push(registry_image_registry, registry_image_repository, registry_image_tag)` | Helper service inputs are purpose-prefixed. `all()` currently calls `push()` with defaults, so the aggregate remains no-argument. Constructor-level offline overrides are not present yet. |
| `modules/hugo/tests` | `all()` without inputs | None | OK for aggregate shape. No exposed runtime image overrides yet. |
| `scenarios/container-images/tests` | `all()` without inputs | `image_ref`, `image_refs`, registry auth examples | OK. These validate build/publish metadata, not runtime image selection. |
| `scenarios/helm-ci/tests` | `all()` without inputs | None | OK for aggregate shape. Needs constructor-level Helm/Git runtime overrides and pass-through assertions in tasks `3.3` and `3.4`. |
| `scenarios/static-site/tests` | `all()` without inputs | None | OK for aggregate shape. Needs constructor-level Hugo runtime overrides and pass-through assertions in tasks `2.2` and `2.3`. |

### 1.4 Released API Impact

Released components requiring new tags after this change:

- `scenarios/static-site`: currently released through `scenarios/static-site/v0.2.0`. Adding constructor inputs is source-compatible for callers that use defaults, but the released scenario API changes and should receive a new release tag.

Released components audited as already matching or out of scope:

- `modules/git`: latest tag `modules/git/v1.0.1`; runtime image inputs already use the standard names.
- `modules/helm`: latest tag `modules/helm/v1.3.1`; runtime image inputs already use the standard names.
- `modules/hugo`: latest tag `modules/hugo/v0.2.0`; runtime image inputs already use the standard names.
- `modules/docker`: latest tag `modules/docker/v0.1.2`; image-related inputs are build/publish metadata and registry auth exceptions.
- `scenarios/container-images`: latest tag `scenarios/container-images/v0.1.2`; image-related inputs are build/publish metadata and registry auth exceptions.

Changed components with no matching release tag found in this repository:

- `modules/opentofu`: no `modules/opentofu/*` tag found. The `container_image` removal is still a breaking API migration for any consumers using the current unreleased module reference.
- `scenarios/helm-ci`: no `scenarios/helm-ci/*` tag found. The new prefixed constructor/runtime image inputs still change the public scenario API shape.
