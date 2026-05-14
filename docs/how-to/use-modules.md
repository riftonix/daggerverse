# Use Modules From This Repository

All Dagger modules live under `modules/`.

Use this command shape from the repository root:

```bash
dagger -m ./modules/<module> call <function> [arguments]
```

For example:

```bash
dagger -m ./modules/git call list-tags --source=.
```

## Pass Source Directories

Most modules accept a `source` directory. The source path is resolved from the directory where you run the `dagger` command, not from the module directory.

For a chart inside this repository:

```bash
dagger -m ./modules/helm call lint --source=./modules/helm/tests/charts/ns-configurator
```

For an external chart:

```bash
dagger -m ./modules/helm call lint --source=../my-project/charts/my-chart
```

## Use Local Module Dependencies

The `pipelines` module depends on the local `helm` and `git` modules:

```json
{
  "name": "helm",
  "source": "../helm"
}
```

This keeps local development self-contained after the repository layout move to `modules/`.
