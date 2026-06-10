## Why

Runtime tool image selection is currently inconsistent across modules and scenarios. Most image-backed modules expose `image_registry`, `image_repository`, `image_tag`, and `user_id`, but some modules use a combined image string and scenarios often hide module runtime defaults, making CI reproducibility and Renovate synchronization harder.

## What Changes

- Establish a repository-wide convention for image-backed modules and scenarios: public runtime image inputs use `image_registry`, `image_repository`, `image_tag`, and `user_id`.
- Require scenarios that compose image-backed modules to expose the relevant runtime image inputs instead of relying only on hidden module defaults.
- Require scenarios with multiple tool images to prefix each image input set with the tool or engine name, such as `hugo_image_tag`, `helm_image_tag`, or `git_image_tag`.
- Keep `source` as the primary input tree and keep secondary path inputs descriptive.
- Update `scenarios/static-site` to accept Hugo runtime image inputs and pass them to the Hugo module.
- Update `scenarios/helm-ci` to accept Helm and Git runtime image inputs and pass them to the Helm and Git modules.
- **BREAKING** Update `modules/opentofu` from combined `container_image` to standard image inputs while keeping `executor` as the IaC tool command.
- Document the convention so new and updated modules/scenarios do not introduce incompatible runtime image parameter names.
- Standardize Dagger test module public shape: expose a no-argument aggregate `all()` by default, use local fixture sources internally, and prefix runtime image inputs for helper services when tests expose them.
- Allow duplicated runtime image defaults in production, scenario, test, and downstream workflow code when Renovate owns every occurrence through the same dependency source and updates the full version string atomically.
- Align Hugo minimum-version Renovate tracking with the runtime image source used by `container-images`: Docker tags from `hugomods/hugo:exts-*`, not upstream `gohugoio/hugo` releases.
- Update READMEs, reference docs, examples, tests, and Renovate guidance to reflect explicit runtime image pins where applicable.

## Capabilities

### New Capabilities

- `opentofu-module`: Define the OpenTofu module public contract, including standardized runtime image inputs and the IaC executor input.

### Modified Capabilities

- `daggerverse`: Add the repository-wide runtime image input convention for new and updated modules/scenarios.
- `hugo-module`: Confirm Hugo follows the runtime image convention and document its image inputs as the source of truth for Hugo execution.
- `static-site-scenario`: Expose Hugo runtime image inputs on the scenario constructor and pass them through to the Hugo module.
- `helm-ci-scenario`: Expose Helm and Git runtime image inputs on the scenario and pass them through to composed modules.

## Impact

- Affected code: `scenarios/static-site`, `scenarios/helm-ci`, `modules/opentofu`, docs, examples, and tests.
- API impact: `modules/opentofu` callers must migrate from `container_image=<ref>` to `image_registry`, `image_repository`, and `image_tag`; changed released modules/scenarios require new release tags.
- CI impact: provider workflows can pin the actual runtime image tag explicitly and synchronize site/tool configuration such as Hugo minimum version with the image that is used to build.
- Documentation impact: root/reference docs and component READMEs must describe the image input convention, multi-image prefix rule, and allowed exceptions.
