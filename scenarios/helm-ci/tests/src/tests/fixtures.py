"""Chart sync fixtures built from the files under fixtures/."""

import json
from collections.abc import Awaitable
from unittest import TestCase

import dagger
import yaml
from dagger import Directory, ExecError, QueryError, Service, dag

REGISTRY_IMAGE_REGISTRY = "docker.io"
REGISTRY_IMAGE_REPOSITORY = "registry"
# renovate: datasource=docker depName=registry
REGISTRY_IMAGE_TAG = "3"
REGISTRY_HOST = "registry"
REGISTRY_PORT = 5000

CONFIG_PATH = "updatecli/values.yaml"
FAKE_DIGEST = "sha256:" + "0" * 64
# Versions of nuc-demo built from fixtures/upstream/update; 1.0.4 is built from fixtures/upstream/base.
UPDATE_VERSIONS = ("1.0.5", "1.1.0-rc.1", "2.0.0")
# Files that are not valid UTF-8 and are compared by content digest.
BINARY_SUFFIXES = (".bin", ".tgz")
PROXY_VARIABLES = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "FTP_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "ftp_proxy",
    "all_proxy",
)
OTEL_VARIABLES = ("OTEL_TRACES_EXPORTER", "OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")


def fixtures() -> Directory:
    return dag.current_module().source().directory("fixtures")


def pin(version: str, digest: str) -> str:
    return json.dumps({"version": version, "digest": digest}, indent=2) + "\n"


def demo_chart(version: str) -> str:
    """Return the fork demo Chart.yaml with sorted keys, as Helm writes it into a package."""
    return f"apiVersion: v2\ndescription: Demo STEP2 chart\nname: demo\nversion: {version}\n"


def demo_values(first: str) -> str:
    """Return fork demo values; unchanged lines keep an upstream first-line change apart from the fork edit."""
    return f"first: {first}\na: 1\nb: 2\nc: 3\nd: 4\nlast: fork-edit\nmarker: fork-marker\n"


def fork(digests: dict[str, str] | None = None) -> Directory:
    """Return the fork fixture with pins to the pushed base packages, or to a fake digest."""
    digests = digests or {}
    return (
        fixtures()
        .directory("fork")
        .with_new_file("updatecli/pins/demo.json", pin("1.0.4", digests.get("nuc-demo:1.0.4", FAKE_DIGEST)))
        .with_new_file("updatecli/pins/other.json", pin("1.0.0", digests.get("nuc-other:1.0.0", FAKE_DIGEST)))
    )


async def read_config(source: Directory) -> dict:
    return yaml.safe_load(await source.file(CONFIG_PATH).contents())


def with_config(source: Directory, config: dict) -> Directory:
    return source.with_new_file(CONFIG_PATH, yaml.safe_dump(config, sort_keys=False))


async def with_nomatch(source: Directory, digests: dict[str, str]) -> Directory:
    """Add a component whose version filter matches no upstream tag."""
    config = await read_config(source)
    config["components"] = config["components"] | {"nomatch": {"upstream": "nuc-other", "versionfilter": ">=3.0.0"}}
    return (
        with_config(source, config)
        .with_new_file("updatecli/pins/nomatch.json", pin("1.0.0", digests["nuc-other:1.0.0"]))
        .with_new_file("libs/nomatch/Chart.yaml", "apiVersion: v2\nname: nomatch\nversion: 1.0.0\n")
    )


def without_proxies(container: dagger.Container) -> dagger.Container:
    for name in PROXY_VARIABLES + OTEL_VARIABLES:
        container = container.with_env_variable(name, "")
    return container


async def registry() -> tuple[Service, dict[str, str]]:
    """Return a stateless registry serving every upstream fixture chart, and the pushed digests."""
    image = dag.container().from_(f"{REGISTRY_IMAGE_REGISTRY}/{REGISTRY_IMAGE_REPOSITORY}:{REGISTRY_IMAGE_TAG}")
    upstream = fixtures().directory("upstream")
    charts = (
        dag.directory()
        .with_directory("1.0.0/nuc-other", upstream.directory("base/nuc-other"))
        .with_directory("1.0.4/nuc-demo", upstream.directory("base/nuc-demo"))
    )
    for version in UPDATE_VERSIONS:
        charts = charts.with_directory(f"{version}/nuc-demo", upstream.directory("update/nuc-demo"))
    populated = (
        without_proxies(dag.helm_ci(source=dag.directory()).updatecli_container())
        .with_directory("/tmp/upstream", charts)
        .with_file("/tmp/registry-bin/registry", image.file("/bin/registry"))
        .with_directory("/tmp/registry-fixture", fixtures().directory("registry"))
        .with_exec(["python3", "/tmp/registry-fixture/populate.py"])
    )
    digests = json.loads(await populated.file("/tmp/digests.json").contents())
    service = (
        image.with_directory("/var/lib/registry", populated.directory("/tmp/registry-data"))
        .with_exposed_port(REGISTRY_PORT)
        .as_service(use_entrypoint=True)
    )
    return service, digests


def scenario(source: Directory, registry_service: Service | None = None) -> dagger.HelmCi:
    """Return the scenario with a runtime that reaches only the fixture registry."""
    helm_ci = dag.helm_ci(source=source)
    container = without_proxies(helm_ci.updatecli_container())
    if registry_service is not None:
        container = container.with_service_binding(REGISTRY_HOST, registry_service)
    for name in ("NO_PROXY", "no_proxy"):
        container = container.with_env_variable(name, REGISTRY_HOST)
    return helm_ci.with_updatecli_container(container)


async def snapshot(directory: Directory) -> dict[str, str]:
    """Return every file of a tree: text content, or the content digest of a binary file."""
    files = {}
    for path in sorted(await directory.glob("**/*")):
        if path.endswith("/"):
            continue
        file = directory.file(path)
        if path.endswith(BINARY_SUFFIXES):
            files[path] = await file.digest(exclude_metadata=True)
        else:
            files[path] = await file.contents()
    return files


async def failure_output(call: Awaitable[object]) -> str:
    try:
        await call
    except QueryError as error:
        return f"{error.stdout}{error.stderr}" if isinstance(error, ExecError) else str(error)
    raise AssertionError("expected the chart sync call to fail")


async def assert_fails_with(call: Awaitable[object], expected: str, message: str | None = None) -> None:
    TestCase().assertIn(expected, await failure_output(call), message)
