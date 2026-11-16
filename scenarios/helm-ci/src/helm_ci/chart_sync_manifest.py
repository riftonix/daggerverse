"""Render one Updatecli pipeline per chart sync component."""

import yaml

HELPER_DIRECTORY = "/opt/chart-sync"
HELPER_PATH = f"{HELPER_DIRECTORY}/chart_sync.py"
SCM_ID = "fork"


class _Dumper(yaml.SafeDumper):
    """Write multi-line strings as literal blocks for a readable manifest."""


def _represent_string(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Dumper.add_representer(str, _represent_string)


def helper_command(config_path: str, component_id: str) -> list[str]:
    return ["python3", "-I", HELPER_PATH, "sync", "--config", config_path, "--component", component_id]


def render_manifest(
    components: list[dict],
    config_path: str,
    repository: str | None = None,
    branch: str | None = None,
) -> str:
    """Render local pipelines, or GitHub pipelines when repository and branch are set."""
    documents = [_pipeline(component, config_path, repository, branch) for component in components]
    return yaml.dump_all(documents, Dumper=_Dumper, sort_keys=False, explicit_start=True, width=4096)


def _pipeline(component: dict, config_path: str, repository: str | None, branch: str | None) -> dict:
    component_id, path, pin = component["id"], component["path"], component["pin"]
    target = {
        "name": f"Merge only {path} and its source pin",
        "kind": "shell",
        "disablesourceinput": True,
        "spec": {
            "command": " ".join(helper_command(config_path, component_id)),
            "changedif": {"kind": "console/output"},
            "environments": [{"name": "PATH"}, {"name": "HOME"}],
        },
    }
    pipeline: dict = {"name": f"Update {component_id} from upstream OCI", "pipelineid": f"upstream-{component_id}"}
    if repository is None or branch is None:
        pipeline["targets"] = {"component": target}
        return pipeline

    owner, name = repository.split("/", 1)
    pipeline["scms"] = {
        SCM_ID: {
            "kind": "github",
            "spec": {
                "owner": owner,
                "repository": name,
                "branch": branch,
                "commitusingapi": True,
                "submodules": False,
            },
        }
    }
    pipeline["targets"] = {"component": {**target, "scmid": SCM_ID}}
    pipeline["actions"] = {
        "pullrequest": {
            "kind": "github/pullrequest",
            "scmid": SCM_ID,
            "title": f"chore(deps): update {component_id} from upstream",
            "spec": {
                "merge": {"strategy": "manual"},
                "description": (
                    f"Updates only `{path}` and `{pin}`.\n"
                    "Components are independent. Merge and publish missing dependencies first,\n"
                    "then rerun this pipeline. Updatecli does not order or merge dependency PRs.\n"
                ),
            },
        }
    }
    return pipeline
