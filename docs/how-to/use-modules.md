# Use Modules From This Repository

Reusable Dagger modules live under `modules/`. Ready-to-run CI jobs belong under `scenarios/`.

Use this command shape from the repository root:

```bash
dagger -m ./modules/<module> call <function> [arguments]
```

For example:

```bash
dagger -m ./modules/git call get-tags --source=.
```

## Pass Source Directories

Most modules and scenarios accept the primary input directory as `source`. The
source path is resolved from the directory where you run the `dagger` command,
not from the module directory.

Use `source` for the main tree being operated on: a repository checkout, chart,
site, image build tree, or IaC project. Keep secondary inputs descriptive. For
example, Helm CI keeps `charts_path`, `libs_path`, `target_branch`, and
`values`; Docker and container image calls keep `context_path`,
`dockerfile_path`, and `bake_path`.

`source` only identifies the directory tree passed to Dagger. CI provider
workflows stay responsible for event rules, checkout depth and refs, preview URL
calculation, publication timing, deployment cleanup, and pull request or merge
request comments. Compute those provider-specific values in GitHub Actions,
GitLab CI, or another workflow layer, then pass explicit inputs to modules and
scenarios.

For a chart inside this repository:

```bash
dagger -m ./modules/helm call lint --source=./modules/helm/tests/charts/ns-configurator
```

For an external chart:

```bash
dagger -m ./modules/helm call lint --source=../my-project/charts/my-chart
```

For a static site scenario call, pass the site directory as constructor
`source` before the operation name. Pin the Hugo runtime image tag in CI when
site rendering must be reproducible:

```bash
dagger -m ./scenarios/static-site call \
  --source=./site \
  --hugo-theme-url=github.com/google/docsy@v0.13.0 \
  --hugo-image-tag=0.154.5-10.5.0 \
  verify-site \
  --site-base-url=https://example.com/ \
  --engine=hugo
```

Image-backed modules use `image_registry`, `image_repository`, `image_tag`, and
`container_user_id` for their execution container. Scenarios that compose image-backed
modules prefix those fields with the tool name, such as `hugo_image_tag`,
`helm_image_tag`, or `git_image_tag`. See
[Runtime image input conventions](../reference/runtime-images.md).

## Use Local Module Dependencies

Scenarios can depend on local modules. For example, a Helm CI scenario can depend on the local `helm` and `git` modules:

```json
{
  "name": "helm",
  "source": "../../modules/helm"
}
```

This keeps local development self-contained while keeping reusable modules separate from concrete CI jobs.
