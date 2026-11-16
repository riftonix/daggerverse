#!/usr/bin/env python3
"""Validate chart sync configuration and synchronize one forked chart from its upstream OCI package.

Updatecli runs this helper as a shell target. It sets DRY_RUN=false only for `pipeline apply`, and
treats any stdout as a change, so the helper prints only when a component changed or would change.
"""

import argparse
import json
import operator
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import yaml

COMPONENT_ID = re.compile(r"[a-z0-9][a-z0-9-]*")
PATH_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
UPSTREAM_NAME = re.compile(r"[a-z0-9][a-z0-9._-]*")
CONFIG_PATH = re.compile(r"[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*")
REGISTRY = re.compile(r"oci://([A-Za-z0-9.-]+(?::[0-9]+)?)((?:/[a-z0-9][a-z0-9._-]*)*)/?")
STABLE_VERSION = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)")
PIN_VERSION = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)(-[0-9A-Za-z.-]+)?")
COMPARISON = re.compile(r"(>=|<=|>|<|=)([0-9]+)\.([0-9]+)\.([0-9]+)")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
HELM_DIGEST = re.compile(r"Digest:\s*(sha256:[0-9a-f]{64})")
NEXT_LINK = re.compile(r'<([^>]+)>\s*;\s*rel="?next"?')
CHALLENGE_PARAMETER = re.compile(r'(\w+)="([^"]*)"')
OPERATORS = {"=": operator.eq, ">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le}
RULE_KEYS = ("from", "regex", "to", "file")
# Vendored dependencies are rebuilt by Helm, so they are never merged.
VENDORED = ["charts", "Chart.lock"]
DIAGNOSTICS_LIMIT = 6000
HTTP_TIMEOUT_SECONDS = 60
MAX_TAG_PAGES = 1000


class ConfigurationError(ValueError):
    """Every invalid configuration item, reported together."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("chart sync configuration is invalid:\n" + "\n".join(f"- {error}" for error in errors))


class ArgumentParser(argparse.ArgumentParser):
    """Exit 1 on usage errors, like every other helper failure."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"chart_sync: {message}", file=sys.stderr)
        raise SystemExit(1)


@dataclass(frozen=True)
class Component:
    id: str
    path: str
    upstream: str
    versionfilter: str
    exclude: list[str]
    rewrite: list[dict]
    pin: str


@dataclass(frozen=True)
class Config:
    registry: str
    plain_http: bool
    exclude: list[str]
    rewrite: list[dict]
    home: str
    # Selected components; rewrite rules always cover every declared component.
    components: dict[str, Component]
    all_components: tuple[Component, ...]


def run(command: list[str], cwd: Path, env: dict[str, str], data: str | None = None) -> str:
    """Capture tool output; never run tools from downloaded source directories."""
    return subprocess.run(command, cwd=cwd, env=env, input=data, text=True, capture_output=True, check=True).stdout


def inside(root: Path, path: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def version_key(version: str) -> tuple[int, int, int, int]:
    """Order versions; a prerelease sorts below its release."""
    match = PIN_VERSION.fullmatch(version)
    if not match:
        raise ValueError(f"not a semantic version: {version!r}")
    return int(match[1]), int(match[2]), int(match[3]), 0 if match[4] else 1


def parse_filter(text: object) -> list[tuple[str, tuple[int, int, int]]] | None:
    """Return the comparisons of a version filter, or None when it is unsupported."""
    if not isinstance(text, str) or not text.split():
        return None
    comparisons = []
    for part in text.split():
        match = COMPARISON.fullmatch(part)
        if not match:
            return None
        comparisons.append((match[1], (int(match[2]), int(match[3]), int(match[4]))))
    return comparisons


def string_list(value: object, where: str, errors: list[str]) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        errors.append(f"{where}: must be a list of non-empty strings")
        return []
    return value


def rewrite_rules(value: object, where: str, errors: list[str]) -> list[dict]:
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(f"{where}: must be a list of rules")
        return []
    rules = []
    for index, rule in enumerate(value):
        location = f"{where}[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{location}: must be a mapping")
            continue
        if ("from" in rule) == ("regex" in rule):
            errors.append(f"{location}: must define exactly one of from or regex")
        if "to" not in rule:
            errors.append(f"{location}: to is missing")
        if any(key in rule and not isinstance(rule[key], str) for key in RULE_KEYS):
            errors.append(f"{location}: from, regex, to, and file must be strings")
            continue
        if "regex" in rule:
            try:
                re.compile(rule["regex"])
            except re.error as error:
                errors.append(f"{location}: invalid regex: {error}")
        rules.append({key: rule[key] for key in RULE_KEYS if key in rule})
    return rules


def load_config(root: Path, config_path: str, selection: list[str]) -> Config:
    """Read and validate the whole configuration and every pin; raise one error listing all problems."""
    path = PurePosixPath(config_path)
    if not CONFIG_PATH.fullmatch(config_path) or any(part in (".", "..") for part in path.parts):
        raise ConfigurationError([f"config_path: {config_path!r} must be a relative path inside source"])
    config_file = root / path
    if not inside(root, config_file) or not config_file.is_file():
        raise ConfigurationError([f"config_path: {config_path} is not a file inside source"])
    try:
        policy = yaml.safe_load(config_file.read_text())
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise ConfigurationError([f"config_path: {config_path} is not valid YAML: {error}"]) from error
    if not isinstance(policy, dict):
        raise ConfigurationError([f"config_path: {config_path} must contain a mapping"])

    errors: list[str] = []
    upstream = policy.get("upstream")
    if upstream is not None and not isinstance(upstream, dict):
        errors.append("upstream: must be a mapping")
    if not isinstance(upstream, dict):
        upstream = {}

    registry = upstream.get("registry")
    if registry is None:
        errors.append("upstream.registry: missing")
    elif not isinstance(registry, str) or not REGISTRY.fullmatch(registry):
        errors.append(f"upstream.registry: {registry!r} must be oci://<host>[/<project>]")
    default_filter = upstream.get("versionfilter")
    if default_filter is None:
        errors.append("upstream.versionfilter: missing")
    plain_http = upstream.get("plainhttp", False)
    if not isinstance(plain_http, bool):
        errors.append("upstream.plainhttp: must be a boolean")
    shared_exclude = string_list(upstream.get("exclude"), "upstream.exclude", errors)
    shared_rewrite = rewrite_rules(policy.get("rewrite"), "rewrite", errors)
    home = policy.get("home")
    if home is None:
        errors.append("home: missing")
    elif not isinstance(home, str) or not home.strip():
        errors.append("home: must be a non-empty string")

    declared = policy.get("components")
    if declared is None:
        declared = {}
        errors.append("components: missing")
    elif not isinstance(declared, dict) or not declared:
        declared = {}
        errors.append("components: must be a non-empty mapping of component IDs")

    pins = path.parent / "pins"
    components: dict[str, Component] = {}
    owners: dict[str, str] = {}
    for key, value in declared.items():
        where = f"components.{key}"
        if not isinstance(key, str) or not COMPONENT_ID.fullmatch(key):
            errors.append(f"{where}: ID must match [a-z0-9][a-z0-9-]*")
            continue
        if value is None:
            value = {}
        if not isinstance(value, dict):
            errors.append(f"{where}: must be a mapping or empty")
            continue
        component_path = value.get("path", f"libs/{key}")
        parts = component_path.split("/") if isinstance(component_path, str) else []
        if (
            len(parts) != 2
            or parts[0] not in ("charts", "libs")
            or not PATH_SEGMENT.fullmatch(parts[1])
            or parts[1] in (".", "..")
        ):
            errors.append(f"{where}: path {component_path!r} must be charts/<name> or libs/<name>")
            continue
        directory = root / component_path
        if directory.is_symlink() or not inside(root, directory) or not directory.is_dir():
            errors.append(f"{where}: path {component_path} must be a directory inside source")
        if component_path in owners:
            errors.append(f"{where}: path {component_path} is also used by components.{owners[component_path]}")
        owners.setdefault(component_path, key)
        name = value.get("upstream", f"nuc-{key}")
        if not isinstance(name, str) or not UPSTREAM_NAME.fullmatch(name):
            errors.append(f"{where}: upstream {name!r} must be an OCI chart name")
        versionfilter = value.get("versionfilter", default_filter)
        if versionfilter is not None and parse_filter(versionfilter) is None:
            errors.append(f"{where}: unsupported versionfilter {versionfilter!r}")
        exclude = string_list(value.get("exclude"), f"{where}.exclude", errors)
        rewrite = rewrite_rules(value.get("rewrite"), f"{where}.rewrite", errors)
        pin = (pins / f"{key}.json").as_posix()
        pin_error = check_pin(root, pin)
        if pin_error:
            errors.append(f"{where}: pin {pin} {pin_error}")
        components[key] = Component(key, component_path, str(name), str(versionfilter), exclude, rewrite, pin)

    unknown = [key for key in selection if key not in declared]
    if unknown:
        errors.append(f"components input: unknown component IDs {', '.join(sorted(set(unknown)))}")
    if errors:
        raise ConfigurationError(errors)
    every = tuple(components.values())
    if selection:
        components = {key: components[key] for key in dict.fromkeys(selection)}
    return Config(str(registry).rstrip("/"), plain_http, shared_exclude, shared_rewrite, str(home), components, every)


def check_pin(root: Path, pin: str) -> str | None:
    """Return why a pin is invalid, or None."""
    path = root / pin
    if path.is_symlink():
        return "must not be a symbolic link"
    if not inside(root, path) or not path.is_file():
        return "is missing"
    try:
        data = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return f"is not valid JSON: {error}"
    if not isinstance(data, dict):
        return "must be a JSON object"
    problems = []
    if not isinstance(data.get("version"), str) or not PIN_VERSION.fullmatch(data["version"]):
        problems.append("a semantic version")
    if not isinstance(data.get("digest"), str) or not DIGEST.fullmatch(data["digest"]):
        problems.append("a sha256 digest")
    return f"lacks {' and '.join(problems)}" if problems else None


def rules(config: Config, component: Component) -> list[dict]:
    """Ordered rewrites: GitHub URLs, shared rules, upstream chart names, component rules."""
    every = config.all_components
    github = [
        {"from": f"https://github.com/nixys/{item.upstream}", "to": f"{config.home}/tree/master/{item.path}"}
        for item in every
    ]
    names = [{"from": item.upstream, "to": item.id} for item in every]
    return github + config.rewrite + names + component.rewrite


def normalize(tree: Path, rewrites: list[dict]) -> None:
    """Rewrite UTF-8 files in place; binary files are left untouched."""
    for path in tree.rglob("*"):
        if not path.is_file():
            continue
        try:
            original = path.read_bytes().decode()
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(tree).as_posix()
        text = original
        for rule in rewrites:
            if rule.get("file", relative) != relative:
                continue
            text = (
                re.sub(rule["regex"], rule["to"], text) if "regex" in rule else text.replace(rule["from"], rule["to"])
            )
        if text != original:
            path.write_bytes(text.encode())


def copy_tree(source: Path, destination: Path, exclusions: list[str]) -> None:
    """Copy data without following links; exclusions are exact chart-relative paths."""
    if source.is_symlink():
        raise ValueError(f"{source.name}: chart root must not be a symbolic link")
    excluded = {item.rstrip("/") for item in exclusions}

    def ignore(directory: str, names: list[str]) -> list[str]:
        parent = Path(directory).relative_to(source)
        return [name for name in names if name == "__pycache__" or (parent / name).as_posix() in excluded]

    shutil.copytree(source, destination, ignore=ignore, symlinks=True)
    if any(path.is_symlink() or ".git" in path.relative_to(destination).parts for path in destination.rglob("*")):
        raise ValueError(f"{source.name}: chart trees must contain regular files, not symbolic links or .git metadata")


def request_json(url: str, token: str | None) -> tuple[dict, str | None]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        return json.load(response), response.headers.get("Link")


def anonymous_token(challenge: str, repository: str) -> str:
    """Exchange a Bearer challenge for an anonymous pull token."""
    if not challenge.lower().startswith("bearer "):
        raise ValueError(f"unsupported registry authentication challenge {challenge!r}")
    parameters = dict(CHALLENGE_PARAMETER.findall(challenge))
    if "realm" not in parameters:
        raise ValueError(f"registry authentication challenge without realm: {challenge!r}")
    query = {"scope": parameters.get("scope", f"repository:{repository}:pull")}
    if "service" in parameters:
        query["service"] = parameters["service"]
    body, _ = request_json(f"{parameters['realm']}?{urllib.parse.urlencode(query)}", None)
    token = body.get("token") or body.get("access_token")
    if not isinstance(token, str) or not token:
        raise ValueError("registry token response has no token")
    return token


def list_tags(config: Config, name: str) -> list[str]:
    """List OCI tags with anonymous Bearer authentication and Link pagination."""
    match = REGISTRY.fullmatch(config.registry)
    host, project = match[1], match[2].strip("/")
    repository = f"{project}/{name}" if project else name
    url: str | None = f"{'http' if config.plain_http else 'https'}://{host}/v2/{repository}/tags/list"
    token = None
    tags: list[str] = []
    for _ in range(MAX_TAG_PAGES):
        if url is None:
            return tags
        try:
            body, link = request_json(url, token)
        except urllib.error.HTTPError as error:
            if error.code != 401 or token is not None:
                raise ValueError(f"tag listing {url} failed with HTTP {error.code}") from error
            token = anonymous_token(error.headers.get("WWW-Authenticate", ""), repository)
            continue
        except OSError as error:
            raise ValueError(f"tag listing {url} failed: {error}") from error
        page = body.get("tags") if isinstance(body, dict) else None
        if page is not None and not isinstance(page, list):
            raise ValueError(f"tag listing {url} returned an invalid tag list")
        tags.extend(tag for tag in page or [] if isinstance(tag, str))
        next_link = NEXT_LINK.search(link or "")
        url = urllib.parse.urljoin(url, next_link[1]) if next_link else None
    raise ValueError(f"tag listing for {repository} exceeded {MAX_TAG_PAGES} pages")


def select_version(tags: list[str], versionfilter: str) -> str | None:
    """Return the highest stable tag that satisfies every comparison."""
    comparisons = parse_filter(versionfilter) or []
    candidates = []
    for tag in tags:
        match = STABLE_VERSION.fullmatch(tag)
        if not match:
            continue
        version = (int(match[1]), int(match[2]), int(match[3]))
        if all(OPERATORS[op](version, bound) for op, bound in comparisons):
            candidates.append((version, tag))
    return max(candidates)[1] if candidates else None


def pull(
    config: Config,
    name: str,
    version: str,
    destination: Path,
    control: Path,
    env: dict[str, str],
    expected: str | None = None,
) -> tuple[Path, str]:
    """Pull and unpack one package; Helm verifies OCI content, the helper compares the digest with the pin."""
    destination.mkdir()
    command = [
        "helm",
        "pull",
        f"{config.registry}/{name}",
        "--version",
        version,
        "--untar",
        "--destination",
        str(destination),
        "--registry-config",
        str(control / "registry.json"),
    ]
    if config.plain_http:
        command.append("--plain-http")
    result = subprocess.run(command, cwd=control, env=env, text=True, capture_output=True, check=True)
    match = HELM_DIGEST.search(result.stdout + result.stderr)
    if not match:
        raise ValueError(f"{name} {version}: Helm reported no OCI digest")
    if expected and match[1] != expected:
        raise ValueError(f"{name} {version}: OCI digest {match[1]} does not match the pinned digest {expected}")
    chart = destination / name
    metadata = yaml.safe_load((chart / "Chart.yaml").read_text())
    if not isinstance(metadata, dict) or metadata.get("name") != name or str(metadata.get("version")) != version:
        raise ValueError(f"{name} {version}: pulled chart identity does not match the requested package")
    return chart, match[1]


def git_tree(git: list[str], directory: Path, control: Path, env: dict[str, str]) -> str:
    """Let Git index a complete directory and write its tree."""
    args = [*git, "--work-tree", str(directory)]
    run([*args, "read-tree", "--empty"], control, env)
    run([*args, "add", "--all", "--force"], control, env)
    return run([*git, "write-tree"], control, env).strip()


def merge(
    git: list[str], base: Path, ours: Path, incoming: Path, result: Path, control: Path, env: dict[str, str]
) -> str:
    """Git owns directory merging, deletions, renames, and conflict detection."""

    def commit(directory: Path, label: str, parent: str | None = None) -> str:
        command = [*git, "commit-tree", git_tree(git, directory, control, env), "-m", label]
        if parent:
            command += ["-p", parent]
        return run(command, control, env).strip()

    ancestor = commit(base, "base")
    local = commit(ours, "fork", ancestor)
    remote = commit(incoming, "upstream", ancestor)
    tree = run([*git, "merge-tree", "--write-tree", local, remote], control, env).splitlines()[0]
    result.mkdir()
    run([*git, "read-tree", tree], control, env)
    run([*git, "--work-tree", str(result), "checkout-index", "--all", "--force"], control, env)
    return local


def private_env(control: Path) -> dict[str, str]:
    home = control / "home"
    home.mkdir()
    return dict(
        os.environ,
        HOME=str(home),
        DOCKER_CONFIG=str(control / "docker"),
        HELM_CACHE_HOME=str(control / "cache"),
        HELM_CONFIG_HOME=str(control / "config"),
        HELM_DATA_HOME=str(control / "data"),
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL="/dev/null",
        GIT_AUTHOR_NAME="chart-sync",
        GIT_AUTHOR_EMAIL="chart-sync@example.invalid",
        GIT_COMMITTER_NAME="chart-sync",
        GIT_COMMITTER_EMAIL="chart-sync@example.invalid",
        GIT_AUTHOR_DATE="@1700000000 +0000",
        GIT_COMMITTER_DATE="@1700000000 +0000",
    )


def synchronize(root: Path, config: Config, component: Component, apply: bool) -> None:
    """Select the version, prepare the merged result, check the patch, then report and optionally write it."""
    pin_path = root / component.pin
    pin = json.loads(pin_path.read_text())
    selected = select_version(list_tags(config, component.upstream), component.versionfilter)
    if selected is None:
        raise ValueError(f"no tag of {config.registry}/{component.upstream} matches {component.versionfilter!r}")
    if version_key(selected) <= version_key(pin["version"]):
        return
    with tempfile.TemporaryDirectory(prefix="chart-sync-") as temporary:
        control = Path(temporary)
        env = private_env(control)
        original, _ = pull(
            config, component.upstream, pin["version"], control / "old-package", control, env, pin["digest"]
        )
        updated, digest = pull(config, component.upstream, selected, control / "new-package", control, env)
        base, incoming, ours, result = (control / name for name in ("base", "incoming", "ours", "result"))
        exclusions = config.exclude + component.exclude + VENDORED
        rewrites = rules(config, component)
        for package, tree in ((original, base), (updated, incoming)):
            copy_tree(package, tree, exclusions)
            normalize(tree, rewrites)
        copy_tree(root / component.path, ours, VENDORED)
        git = ["git", "--git-dir", str(control / "objects.git")]
        run(["git", "init", "--bare", "--quiet", str(control / "objects.git")], control, env)
        local = merge(git, base, ours, incoming, result, control, env)
        patch = run(
            [*git, "diff", "--binary", "--full-index", "--find-renames", local, git_tree(git, result, control, env)],
            control,
            env,
        )
        versions = [yaml.safe_load((tree / "Chart.yaml").read_text())["version"] for tree in (ours, result)]
        if patch and versions[0] == versions[1]:
            raise ValueError(
                "merged chart changed without advancing its Chart.yaml version; "
                "resolve the fork and upstream version collision manually"
            )
        if patch:
            run(["git", "apply", "--check", "--directory", component.path, "-"], root, env, patch)
        print(f"{'Apply' if apply else 'Preview'} {component.id}: {pin['version']} -> {selected}")
        if apply:
            if patch:
                run(["git", "apply", "--directory", component.path, "-"], root, env, patch)
            pin_path.write_text(json.dumps({"version": selected, "digest": digest}, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate the configuration and print the selected components")
    validate.add_argument("--config", required=True)
    validate.add_argument("--component", action="append", default=[])
    sync = commands.add_parser("sync", help="synchronize one component")
    sync.add_argument("--config", required=True)
    sync.add_argument("--component", required=True)
    args = parser.parse_args(argv)

    root = Path.cwd()
    selection = args.component if args.command == "validate" else [args.component]
    try:
        config = load_config(root, args.config, selection)
    except ConfigurationError as error:
        print(error, file=sys.stderr)
        return 1
    if args.command == "validate":
        selected = [{"id": item.id, "path": item.path, "pin": item.pin} for item in config.components.values()]
        print(json.dumps({"components": selected}))
        return 0
    try:
        synchronize(root, config, config.components[args.component], os.environ.get("DRY_RUN") == "false")
        return 0
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError, subprocess.CalledProcessError) as error:
        if isinstance(error, subprocess.CalledProcessError):
            detail = f"{' '.join(error.cmd[:2])} failed:\n{(error.stdout or '')}{(error.stderr or '')}"
        else:
            detail = str(error)
        print(f"chart_sync: {args.component}: {detail[-DIAGNOSTICS_LIMIT:]}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
