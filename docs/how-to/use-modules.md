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

Scenarios can depend on local modules. For example, a Helm CI scenario can depend on the local `helm` and `git` modules:

```json
{
  "name": "helm",
  "source": "../../modules/helm"
}
```

This keeps local development self-contained while keeping reusable modules separate from concrete CI jobs.
